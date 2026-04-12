"""CRO Strategist agent — scores the page against the ad and produces CROFindings."""

import json

from google import genai
from google.genai import types
from langgraph.config import get_stream_writer

from app.config import settings
from app.models.ad_context import AdContext
from app.models.cro_findings import CROFindings
from app.models.pipeline import PipelineState
from app.models.semantic_map import SemanticMap
from app.prompts.cro_strategist import CRO_STRATEGIST_SYSTEM_PROMPT


async def cro_strategist_node(state: dict) -> dict:
    """
    LangGraph node: analyze page vs ad → return CROFindings.
    Uses Gemini 3.1 Pro with thinking_level=high (deep strategic reasoning needed).
    """
    writer = get_stream_writer()
    writer({"event": "stage_start", "stage": "cro_strategist", "message": "Running CRO analysis..."})

    ps = PipelineState(**state)
    client = genai.Client(api_key=settings.gemini_api_key)

    ad_context = AdContext(**ps.ad_context) if isinstance(ps.ad_context, dict) else ps.ad_context
    semantic_map = SemanticMap(**ps.semantic_map) if isinstance(ps.semantic_map, dict) else ps.semantic_map

    user_content = f"""## AdContext
{ad_context.model_dump_json(indent=2)}

## SemanticMap
{semantic_map.model_dump_json(indent=2)}

## PageContent (markdown)
{ps.page_snapshot.get("clean_markdown", "")[:8000] if isinstance(ps.page_snapshot, dict) else (ps.page_snapshot.clean_markdown or "")[:8000]}

Analyze this page against the ad and return CROFindings JSON."""

    response = client.models.generate_content(
        model=settings.gemini_pro_model,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=CRO_STRATEGIST_SYSTEM_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_level="high"),
            response_mime_type="application/json",
        ),
    )

    cro_findings = CROFindings.model_validate_json(response.text)

    # Compute weighted CRO score before
    cro_score_before = cro_findings.overall_score

    writer({
        "event": "stage_complete",
        "stage": "cro_strategist",
        "message": f"CRO score: {cro_score_before:.0f}/100 — {len(cro_findings.change_candidates)} changes proposed",
        "data": {
            "overall_score": cro_score_before,
            "top_issue": cro_findings.top_issues[0].description if cro_findings.top_issues else None,
            "change_count": len(cro_findings.change_candidates),
        },
    })

    return {
        "cro_findings": cro_findings.model_dump(),
        "cro_score_before": cro_score_before,
        "current_stage": "cro_strategist_complete",
    }
