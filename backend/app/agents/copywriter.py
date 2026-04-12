"""Copywriter agent — generates replacement copy and produces a PatchSpec."""

import json

from google import genai
from google.genai import types
from langgraph.types import StreamWriter

from app.config import settings
from app.agents.utils import extract_json, unwrap_list
from app.models.ad_context import AdContext
from app.models.cro_findings import CROFindings
from app.models.patch_spec import PatchSpec
from app.models.pipeline import ExplanationItem
from app.prompts.copywriter import COPYWRITER_SYSTEM_PROMPT


async def copywriter_node(state: dict, writer: StreamWriter) -> dict:
    """
    LangGraph node: generate replacement copy for each ChangeCandidate → PatchSpec + explanations.
    Uses Gemini 3.1 Pro with thinking_level=medium.
    """
    writer({"event": "stage_start", "stage": "copywriter", "message": "Writing personalized copy..."})

    try:
        client = genai.Client(api_key=settings.gemini_api_key)

        ad_context = AdContext.model_validate(state["ad_context"])
        cro_findings = CROFindings.model_validate(state["cro_findings"])

        original_elements = {
            c.change_id: {
                "selector": c.target_selector,
                "current_text": c.current_text or "",
                "change_type": c.change_type,
                "proposed_direction": c.proposed_direction,
                "cro_principles": c.cro_principles,
            }
            for c in cro_findings.change_candidates
        }

        user_content = f"""## AdContext
{ad_context.model_dump_json(indent=2)}

## ChangeCandidates
{json.dumps([c.model_dump() for c in cro_findings.change_candidates], indent=2)}

## OriginalElements (grounding — only use text already on page or explicitly in ad)
{json.dumps(original_elements, indent=2)}

Write replacement copy for each change candidate and return PatchSpec + explanations JSON."""

        response = client.models.generate_content(
            model=settings.gemini_pro_model,
            contents=[types.Content(role="user", parts=[types.Part(text=user_content)])],
            config=types.GenerateContentConfig(
                system_instruction=COPYWRITER_SYSTEM_PROMPT,
                thinking_config=types.ThinkingConfig(thinking_level="medium"),
                response_mime_type="application/json",
            ),
        )

        raw = unwrap_list(extract_json(response.text))

        patch_spec = PatchSpec.model_validate(raw["patch_spec"])
        explanations = [ExplanationItem.model_validate(e) for e in raw.get("explanations", [])]

        writer({
            "event": "stage_complete",
            "stage": "copywriter",
            "message": f"Generated {len(patch_spec.operations)} patch operations",
            "data": {"operation_count": len(patch_spec.operations)},
        })

        return {
            "patch_spec": patch_spec.model_dump(),
            "explanations": [e.model_dump() for e in explanations],
            "current_stage": "copywriter_complete",
        }

    except Exception as e:
        writer({"event": "stage_error", "stage": "copywriter", "message": f"Copywriting failed: {e}"})
        raise
