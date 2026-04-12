"""Code Modifier agent — deterministic DOM patcher. No LLM involved in happy path."""

from langgraph.config import get_stream_writer

from app.models.patch_spec import PatchSpec
from app.models.pipeline import PageSnapshot, PipelineState
from app.models.qa_report import QAReport
from app.storage.artifacts import save_html, save_screenshot
from app.tools.html_patcher import apply_patch
from app.tools.screenshot import capture_screenshot_from_html
from app.tools.url_rewriter import rewrite_urls_with_base_tag


async def code_modifier_node(state: dict) -> dict:
    """
    LangGraph node: apply PatchSpec to raw HTML → modified HTML + screenshot.

    This is a deterministic tool node — no LLM call in the happy path.
    On QA retry, incorporates failure reasons from QAReport into a revised patch
    (LLM-assisted only on retry to fix broken selectors or hallucinated content).
    """
    writer = get_stream_writer()
    writer({"event": "stage_start", "stage": "code_modifier", "message": "Applying personalization changes..."})

    ps = PipelineState(**state)
    patch_spec = PatchSpec(**ps.patch_spec) if isinstance(ps.patch_spec, dict) else ps.patch_spec
    snapshot = PageSnapshot(**ps.page_snapshot) if isinstance(ps.page_snapshot, dict) else ps.page_snapshot

    # On retry — optionally revise patch based on QA feedback
    if ps.retry_count > 0 and ps.qa_report:
        qa = QAReport(**ps.qa_report) if isinstance(ps.qa_report, dict) else ps.qa_report
        patch_spec = await _revise_patch_for_retry(patch_spec, qa, ps)
        writer({"event": "stage_progress", "stage": "code_modifier",
                "message": f"Retry {ps.retry_count}: revising patch based on QA feedback..."})

    # Apply patches
    modified_html, warnings = apply_patch(snapshot.raw_html, patch_spec)

    if warnings:
        writer({"event": "stage_progress", "stage": "code_modifier",
                "message": f"Applied with {len(warnings)} selector warning(s)"})

    # Inject base tag so relative URLs resolve correctly in preview
    modified_html = rewrite_urls_with_base_tag(modified_html, snapshot.url)

    # Save modified HTML artifact
    html_path = await save_html(ps.run_id, modified_html, variant="variant")

    # Capture screenshot of modified page
    screenshot_bytes = await capture_screenshot_from_html(modified_html, ps.run_id, "modified")
    screenshot_path = None
    if screenshot_bytes:
        screenshot_path = await save_screenshot(ps.run_id, screenshot_bytes, variant="modified")

    # Increment retry_count only if this was triggered by a QA failure
    new_retry_count = ps.retry_count
    if ps.qa_report:
        qa = QAReport(**ps.qa_report) if isinstance(ps.qa_report, dict) else ps.qa_report
        if not qa.passed:
            new_retry_count += 1

    writer({"event": "stage_complete", "stage": "code_modifier",
            "message": f"Changes applied — {len(patch_spec.operations)} operations"})

    return {
        "modified_html": modified_html,
        "modified_screenshot_path": screenshot_path,
        "retry_count": new_retry_count,
        "current_stage": "code_modifier_complete",
    }


async def _revise_patch_for_retry(
    original_patch: PatchSpec,
    qa_report: QAReport,
    state: PipelineState,
) -> PatchSpec:
    """
    Use Gemini Flash to produce a revised PatchSpec that addresses QA failures.
    Only called on retry (retry_count > 0).
    """
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

    response = client.models.generate_content(
        model=settings.gemini_flash_model,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=CODE_MODIFIER_RETRY_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
            response_mime_type="application/json",
        ),
    )

    return PatchSpec.model_validate_json(response.text)
