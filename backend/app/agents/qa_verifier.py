"""QA Verifier agent — structural, visual, and hallucination validation of modified page."""

import json

from google import genai
from google.genai import types
from langgraph.types import StreamWriter

from app.config import settings
from app.agents.utils import extract_json
from app.models.ad_context import AdContext
from app.models.patch_spec import PatchSpec
from app.models.pipeline import PageSnapshot
from app.models.qa_report import HallucinationFlag, QAReport
from app.models.semantic_map import SemanticMap
from app.prompts.qa_verifier import QA_VERIFIER_HALLUCINATION_PROMPT
from app.tools.screenshot import compute_visual_diff
from app.tools.validators import (
    check_key_elements,
    detect_hallucinations,
    validate_html_structure,
)


async def qa_verifier_node(state: dict, writer: StreamWriter) -> dict:
    """
    LangGraph node: validate modified HTML → return QAReport.
    Runs structural + hallucination + visual diff checks.
    Uses Gemini Flash for LLM-assisted hallucination check (thinking_level=low).
    """
    writer({"event": "stage_start", "stage": "qa_verifier", "message": "Validating output quality..."})

    try:
        snapshot = PageSnapshot.model_validate(state["page_snapshot"])
        semantic_map = SemanticMap.model_validate(state["semantic_map"])
        ad_context = AdContext.model_validate(state["ad_context"])
        patch_spec = PatchSpec.model_validate(state["patch_spec"])
        modified_html = state.get("modified_html") or ""
        modified_screenshot_path = state.get("modified_screenshot_path")

        # ── 1. Structural validation ───────────────────────────────────────────
        structural_issues = validate_html_structure(modified_html)

        # ── 2. Key elements still present ─────────────────────────────────────
        key_elements_present = check_key_elements(modified_html, semantic_map)

        # ── 3. Rule-based hallucination detection ──────────────────────────────
        rule_flags = detect_hallucinations(
            original_html=snapshot.raw_html,
            modified_html=modified_html,
            ad_context=ad_context,
        )

        # ── 4. LLM-assisted hallucination check ───────────────────────────────
        llm_flags = await _llm_hallucination_check(snapshot.raw_html, modified_html, ad_context)

        # Merge and deduplicate by code
        all_flags = rule_flags.copy()
        seen_codes = {f.code for f in rule_flags}
        for flag in llm_flags:
            if flag.code not in seen_codes:
                all_flags.append(flag)

        # ── 5. Visual diff ────────────────────────────────────────────────────
        visual_diff_score = await compute_visual_diff(
            snapshot.screenshot_path,
            modified_screenshot_path,
        )

        # ── 6. Pass / fail decision ───────────────────────────────────────────
        has_critical = any(i.severity == "critical" for i in structural_issues)
        has_hallucinations = len(all_flags) > 0
        visual_too_different = visual_diff_score is not None and visual_diff_score > 0.5

        passed = not has_critical and key_elements_present and not has_hallucinations and not visual_too_different

        failure_reasons: list[str] = []
        if has_critical:
            failure_reasons.extend(f"[STRUCTURE] {i.message}" for i in structural_issues if i.severity == "critical")
        if not key_elements_present:
            failure_reasons.append("[STRUCTURE] Critical page elements missing after patch")
        if has_hallucinations:
            failure_reasons.extend(f"[HALLUCINATION] {f.message}" for f in all_flags)
        if visual_too_different:
            failure_reasons.append(f"[VISUAL] Too much layout change: {visual_diff_score:.0%} pixel diff")

        qa_report = QAReport(
            variant_id=patch_spec.variant_id,
            passed=passed,
            is_valid_html=len(structural_issues) == 0,
            structural_issues=structural_issues,
            key_elements_present=key_elements_present,
            visual_diff_score=visual_diff_score,
            hallucination_flags=all_flags,
            grounded_change_count=len(patch_spec.operations) - len(all_flags),
            failure_reasons=failure_reasons,
        )

        # CRO score after — rough heuristic
        cro_score_before = state.get("cro_score_before") or 0.0
        cro_score_after = cro_score_before
        if passed:
            cro_score_after = min(100.0, cro_score_before + len(patch_spec.operations) * 3)

        delta = cro_score_after - cro_score_before
        lift = "0-2%" if delta <= 5 else ("2-7%" if delta <= 15 else "7-15%")

        retry_count = state.get("retry_count", 0)
        status_msg = "Validation passed ✓" if passed else f"Issues found — retry {retry_count + 1}"

        writer({
            "event": "stage_complete",
            "stage": "qa_verifier",
            "message": status_msg,
            "data": {"passed": passed, "issues": len(failure_reasons)},
        })

        return {
            "qa_report": qa_report.model_dump(),
            "cro_score_after": cro_score_after,
            "predicted_lift_range": lift,
            "current_stage": "qa_verifier_complete",
        }

    except Exception as e:
        writer({"event": "stage_error", "stage": "qa_verifier", "message": f"QA validation failed: {e}"})
        raise


async def _llm_hallucination_check(
    original_html: str,
    modified_html: str,
    ad_context: AdContext,
) -> list[HallucinationFlag]:
    """LLM cross-check for hallucinated content in modified HTML."""
    try:
        from bs4 import BeautifulSoup
        client = genai.Client(api_key=settings.gemini_api_key)

        original_text = BeautifulSoup(original_html, "lxml").get_text(" ", strip=True)[:4000]
        modified_text = BeautifulSoup(modified_html, "lxml").get_text(" ", strip=True)[:4000]

        user_content = f"""## Original Page Text
{original_text}

## Modified Page Text
{modified_text}

## AdContext
{ad_context.model_dump_json(indent=2)}

Check for hallucinations and return a JSON array of flags."""

        response = client.models.generate_content(
            model=settings.gemini_flash_model,
            contents=[types.Content(role="user", parts=[types.Part(text=user_content)])],
            config=types.GenerateContentConfig(
                system_instruction=QA_VERIFIER_HALLUCINATION_PROMPT,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                response_mime_type="application/json",
            ),
        )

        raw = extract_json(response.text)
        if isinstance(raw, dict):
            raw = raw.get("flags", [])
        return [HallucinationFlag.model_validate(f) for f in (raw or [])]

    except Exception as e:
        print(f"[qa_verifier] LLM hallucination check failed: {e}")
        return []

