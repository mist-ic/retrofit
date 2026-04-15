"""Code Modifier agent — deterministic DOM patcher. No LLM involved in happy path."""

from langgraph.types import StreamWriter

from app.agents.utils import extract_json, unwrap_list
from app.models.patch_spec import PatchSpec
from app.models.pipeline import PageSnapshot
from app.models.qa_report import QAReport
from app.storage.artifacts import save_html, save_screenshot
from app.tools.html_patcher import apply_patch
from app.tools.screenshot import capture_screenshot_from_html
from app.tools.url_rewriter import rewrite_urls_with_base_tag


async def code_modifier_node(state: dict, writer: StreamWriter) -> dict:
    """
    LangGraph node: apply PatchSpec to raw HTML → modified HTML + screenshot.

    Deterministic tool node — no LLM in the happy path.
    On QA retry, uses Gemini Flash to revise broken patches.
    """
    writer({"event": "stage_start", "stage": "code_modifier", "message": "Applying personalization changes..."})

    try:
        run_id = state["run_id"]
        retry_count = state.get("retry_count", 0)

        patch_spec = PatchSpec.model_validate(state["patch_spec"])
        snapshot = PageSnapshot.model_validate(state["page_snapshot"])

        # On retry — revise patch based on QA feedback
        if retry_count > 0 and state.get("qa_report"):
            qa = QAReport.model_validate(state["qa_report"])
            writer({
                "event": "stage_progress",
                "stage": "code_modifier",
                "message": f"Retry {retry_count}: revising patch based on QA feedback...",
            })
            patch_spec = await _revise_patch_for_retry(patch_spec, qa, state)

        # Apply patches deterministically
        modified_html, warnings = apply_patch(snapshot.raw_html, patch_spec)

        if warnings:
            writer({
                "event": "stage_progress",
                "stage": "code_modifier",
                "message": f"Applied with {len(warnings)} selector warning(s): {warnings[0]}",
            })

        # Inject base tag so relative URLs resolve in preview iframes
        modified_html = rewrite_urls_with_base_tag(modified_html, snapshot.url)

        # Save artifacts
        await save_html(run_id, modified_html, variant="variant")
        screenshot_bytes = await capture_screenshot_from_html(modified_html, run_id, "modified")
        screenshot_path = None
        if screenshot_bytes:
            screenshot_path = await save_screenshot(run_id, screenshot_bytes, variant="modified")

        # Increment retry_count if this run was triggered by a QA failure
        new_retry_count = retry_count
        if state.get("qa_report"):
            qa = QAReport.model_validate(state["qa_report"])
            if not qa.passed:
                new_retry_count += 1

        writer({
            "event": "stage_complete",
            "stage": "code_modifier",
            "message": f"Changes applied — {len(patch_spec.operations)} operations",
        })

        return {
            "modified_html": modified_html,
            "modified_screenshot_path": screenshot_path,
            "retry_count": new_retry_count,
            "current_stage": "code_modifier_complete",
        }

    except Exception as e:
        writer({"event": "stage_error", "stage": "code_modifier", "message": f"Patching failed: {e}"})
        raise


async def _revise_patch_for_retry(
    original_patch: PatchSpec,
    qa_report: QAReport,
    state: dict,
) -> PatchSpec:
    """Gemini Flash revises a PatchSpec to address QA failures. Only called on retry."""
    import json
    from google import genai
    from google.genai import types
    from app.config import settings
    from app.prompts.code_modifier import CODE_MODIFIER_RETRY_PROMPT

    client = genai.Client(api_key=settings.gemini_api_key)

    user_content = f"""## Original PatchSpec
{original_patch.model_dump_json(indent=2)}

## QA Report (failures to fix)
Failure reasons: {json.dumps(qa_report.failure_reasons)}
Hallucinations: {json.dumps([h.model_dump() for h in qa_report.hallucination_flags])}
Structural issues: {json.dumps([i.model_dump() for i in qa_report.structural_issues])}

Produce a revised PatchSpec that fixes these issues."""

    response = await client.aio.models.generate_content(
        model=settings.gemini_flash_model,
        contents=[types.Content(role="user", parts=[types.Part(text=user_content)])],
        config=types.GenerateContentConfig(
            system_instruction=CODE_MODIFIER_RETRY_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_level="high"),
            response_mime_type="application/json",
        ),
    )

    raw = unwrap_list(extract_json(response.text))
    return PatchSpec.model_validate(raw)
