"""CRO Strategist agent — scores the page against the ad and produces CROFindings."""

import json

from google import genai
from google.genai import types
from langgraph.types import StreamWriter

from app.config import settings
from app.agents.utils import extract_json, unwrap_list
from app.models.ad_context import AdContext
from app.models.cro_findings import CROFindings
from app.models.semantic_map import SemanticMap
from app.prompts.cro_strategist import CRO_STRATEGIST_SYSTEM_PROMPT


async def cro_strategist_node(state: dict, writer: StreamWriter) -> dict:
    """
    LangGraph node: analyze page vs ad → return CROFindings.
    Uses Gemini 3.1 Pro with thinking_level=high.
    """
    writer({"event": "stage_start", "stage": "cro_strategist", "message": "Running CRO analysis..."})

    try:
        client = genai.Client(api_key=settings.gemini_api_key)

        ad_context = AdContext.model_validate(state["ad_context"])
        semantic_map = SemanticMap.model_validate(state["semantic_map"])
        page_snapshot = state.get("page_snapshot") or {}
        clean_markdown = page_snapshot.get("clean_markdown") or ""

        user_content = f"""## AdContext
{ad_context.model_dump_json(indent=2)}

## SemanticMap
{semantic_map.model_dump_json(indent=2)}

## PageContent (markdown — first 8000 chars)
{clean_markdown[:8000]}

Analyze this page against the ad and return CROFindings JSON."""

        response = await client.aio.models.generate_content(
            model=settings.gemini_pro_model,
            contents=[types.Content(role="user", parts=[types.Part(text=user_content)])],
            config=types.GenerateContentConfig(
                system_instruction=CRO_STRATEGIST_SYSTEM_PROMPT,
                thinking_config=types.ThinkingConfig(thinking_level="high"),
                response_mime_type="application/json",
            ),
        )

        raw = unwrap_list(extract_json(response.text))
        cro_findings = CROFindings.model_validate(raw)
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

    except Exception as e:
        writer({"event": "stage_error", "stage": "cro_strategist", "message": f"CRO analysis failed: {e}"})
        raise
