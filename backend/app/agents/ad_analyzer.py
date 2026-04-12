"""Ad Analyzer agent — reads the ad creative image and extracts structured AdContext."""

import base64
import json
from typing import Any

import httpx
from google import genai
from google.genai import types
from langgraph.types import StreamWriter

from app.config import settings
from app.agents.utils import extract_json, unwrap_list
from app.models.ad_context import AdContext
from app.prompts.ad_analyzer import AD_ANALYZER_SYSTEM_PROMPT


async def ad_analyzer_node(state: dict, writer: StreamWriter) -> dict:
    """
    LangGraph node: analyze the ad creative → return AdContext.

    Uses Gemini 3 Flash with vision + thinking_level=low.
    Correct SDK pattern: system_instruction in config, user content with role="user".
    """
    writer({"event": "stage_start", "stage": "ad_analyzer", "message": "Analyzing ad creative..."})

    try:
        # Client reads GEMINI_API_KEY from env automatically (per models.md §14)
        client = genai.Client(api_key=settings.gemini_api_key)

        image_bytes = await _get_image_bytes(
            ad_image_base64=state.get("ad_image_base64"),
            ad_image_url=state.get("ad_image_url"),
        )

        # Build user parts: image first (if present), then the extraction request
        user_parts: list[Any] = []
        if image_bytes:
            user_parts.append(
                types.Part(inline_data=types.Blob(mime_type="image/png", data=image_bytes))
            )
            user_parts.append(types.Part(text="Analyze this ad creative and return the AdContext JSON."))
        else:
            user_parts.append(
                types.Part(text="No ad image provided. Return a minimal AdContext JSON with offer_type='none' and headline='(no ad)'.")
            )

        response = client.models.generate_content(
            model=settings.gemini_flash_model,
            # contents must be a list of Content objects with explicit role (per models.md)
            contents=[types.Content(role="user", parts=user_parts)],
            config=types.GenerateContentConfig(
                # System instruction belongs in config, not in contents
                system_instruction=AD_ANALYZER_SYSTEM_PROMPT,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                response_mime_type="application/json",
                # Do NOT set temperature — Gemini 3 must stay at default 1.0
            ),
        )

        raw = unwrap_list(extract_json(response.text))
        ad_context = AdContext.model_validate(raw)

        writer({
            "event": "stage_complete",
            "stage": "ad_analyzer",
            "message": f"Ad analyzed — {(ad_context.headline or '(no headline)')[:50]}",
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

    except Exception as e:
        writer({"event": "stage_error", "stage": "ad_analyzer", "message": f"Ad analysis failed: {e}"})
        raise


async def _get_image_bytes(
    ad_image_base64: str | None,
    ad_image_url: str | None,
) -> bytes | None:
    """Resolve ad image from base64 payload or URL."""
    if ad_image_base64:
        return base64.b64decode(ad_image_base64)

    if ad_image_url:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(ad_image_url)
                r.raise_for_status()
                return r.content
        except Exception as e:
            print(f"[ad_analyzer] Image URL download failed: {e}")

    return None
