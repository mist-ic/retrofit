"""Ad Analyzer agent — reads the ad creative image and extracts structured AdContext."""

import json
from typing import Any

from google import genai
from google.genai import types
from langgraph.config import get_stream_writer

from app.config import settings
from app.models.ad_context import AdContext
from app.models.pipeline import PipelineState
from app.prompts.ad_analyzer import AD_ANALYZER_SYSTEM_PROMPT


async def ad_analyzer_node(state: dict) -> dict:
    """
    LangGraph node: analyze the ad creative → return AdContext.
    Uses Gemini 3 Flash with vision, thinking_level=low (extraction task).
    """
    writer = get_stream_writer()
    writer({"event": "stage_start", "stage": "ad_analyzer", "message": "Analyzing ad creative..."})

    ps = PipelineState(**state)
    client = genai.Client(api_key=settings.gemini_api_key)

    # Build image content
    image_bytes = await _get_image_bytes(ps)

    parts: list[Any] = [types.Part(text=AD_ANALYZER_SYSTEM_PROMPT)]
    if image_bytes:
        parts.append(
            types.Part(
                inline_data=types.Blob(mime_type="image/png", data=image_bytes)
            )
        )
    else:
        parts.append(types.Part(text="No ad image provided. Return a minimal AdContext with offer_type='none'."))

    response = client.models.generate_content(
        model=settings.gemini_flash_model,
        contents=types.Content(parts=parts),
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="low"),
            response_mime_type="application/json",
        ),
    )

    ad_context = AdContext.model_validate_json(response.text)

    writer({
        "event": "stage_complete",
        "stage": "ad_analyzer",
        "message": f"Ad analyzed — {ad_context.headline[:50]}",
        "data": {
            "headline": ad_context.headline,
            "offer_type": ad_context.offer_type,
            "tone": ad_context.tone,
        },
    })

    return {
        "ad_context": ad_context.model_dump(),
        "current_stage": "ad_analyzer_complete",
    }


async def _get_image_bytes(state: PipelineState) -> bytes | None:
    """Resolve ad image from base64 or URL."""
    if state.ad_image_base64:
        import base64
        return base64.b64decode(state.ad_image_base64)

    if state.ad_image_url:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(state.ad_image_url)
                r.raise_for_status()
                return r.content
        except Exception as e:
            print(f"[ad_analyzer] Failed to download ad image from URL: {e}")

    return None
