"""QA Verifier agent — structural, visual, and hallucination validation of the modified page."""

import json

from google import genai
from google.genai import types
from langgraph.config import get_stream_writer

from app.config import settings
from app.models.ad_context import AdContext
from app.models.patch_spec import PatchSpec
from app.models.pipeline import PageSnapshot, PipelineState
from app.models.qa_report import HallucinationFlag, QAReport
from app.models.semantic_map import SemanticMap
from app.prompts.qa_verifier import QA_VERIFIER_HALLUCINATION_PROMPT
from app.tools.screenshot import compute_visual_diff
from app.tools.validators import (
    check_key_elements,
    detect_hallucinations,
    validate_html_structure,
)


async def qa_verifier_node(state: dict) -> dict:
    """
    LangGraph node: validate modified HTML → return QAReport.
    Runs structural + hallucination + visual diff checks.
    Uses Gemini 3 Flash for LLM-assisted hallucination check (thinking_level=low).
    """
    writer = get_stream_writer()
    writer({"event": "stage_start", "stage": "qa_verifier", "message": "Validating output quality..."})

    ps = PipelineState(**state)
    snapshot = PageSnapshot(**ps.page_snapshot) if isinstance(ps.page_snapshot, dict) else ps.page_snapshot
    semantic_map = SemanticMap(**ps.semantic_map) if isinstance(ps.semantic_map, dict) else ps.semantic_map
    ad_context = AdContext(**ps.ad_context) if isinstance(ps.ad_context, dict) else ps.ad_context
    patch_spec = PatchSpec(**ps.patch_spec) if isinstance(ps.patch_spec, dict) else ps.patch_spec

    modified_html = ps.modified_html or ""

    # ── 1. Structural validation ───────────────────────────────────────────────
    structural_issues = validate_html_structure(modified_html)

    # ── 2. Key elements still present ─────────────────────────────────────────
    key_elements_present = check_key_elements(modified_html, semantic_map)

    # ── 3. Rule-based hallucination detection ──────────────────────────────────
    rule_flags = detect_hallucinations(
        original_html=snapshot.raw_html,
        modified_html=modified_html,
        ad_context=ad_context,
    )

    # ── 4. LLM-assisted hallucination check ───────────────────────────────────
    llm_flags = await _llm_hallucination_check(
        snapshot.raw_html, modified_html, ad_context
    )

    # Merge and deduplicate by code
    all_flags = rule_flags.copy()
    seen_codes = {f.code for f in rule_flags}
    for flag in llm_flags:
        if flag.code not in seen_codes:
            all_flags.append(flag)

    # ── 5. Visual diff ────────────────────────────────────────────────────────
    visual_diff_score = await compute_visual_diff(
        snapshot.screenshot_path,
        ps.modified_screenshot_path,
    )

    # ── 6. Pass / fail decision ───────────────────────────────────────────────
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

    # Estimate CRO score after (use strategist's score as proxy; ideally re-score)
    cro_score_after = ps.cro_score_before or 0.0
    if passed:
        # Rough heuristic: each applied, QA-passing operation adds ~3 points
        cro_score_after = min(100.0, cro_score_after + len(patch_spec.operations) * 3)

    delta = cro_score_after - (ps.cro_score_before or 0)
    lift = "0-2%" if delta <= 5 else ("2-7%" if delta <= 15 else "7-15%")

    status_msg = "Validation passed" if passed else f"Issues found — retry {ps.retry_count + 1}"
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


async def _llm_hallucination_check(
    original_html: str,
    modified_html: str,
    ad_context: AdContext,
) -> list[HallucinationFlag]:
    """Ask Gemini Flash to cross-check modified text for hallucinated content."""
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
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=QA_VERIFIER_HALLUCINATION_PROMPT,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                response_mime_type="application/json",
            ),
        )

        flags_data = json.loads(response.text)
        return [HallucinationFlag.model_validate(f) for f in flags_data]

    except Exception as e:
        print(f"[qa_verifier] LLM hallucination check failed: {e}")
        return []
