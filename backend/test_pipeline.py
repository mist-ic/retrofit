"""Quick SSE pipeline test — shows all events including full error messages."""
import asyncio
import httpx
import json
import sys
import traceback

# Force UTF-8 output on Windows to handle Unicode in SSE messages
sys.stdout.reconfigure(encoding="utf-8")


async def test_run():
    async with httpx.AsyncClient(timeout=300) as client:
        # Create run (no ad image)
        r = await client.post(
            "http://localhost:8080/api/runs",
            data={"landing_page_url": "https://mamaearth.in/product/onion-hair-oil"},
        )
        run_id = r.json()["run_id"]
        print(f"Run ID: {run_id}\n{'='*60}")

        # Stream events
        async with client.stream("GET", f"http://localhost:8080/api/runs/{run_id}/stream") as resp:
            buffer = ""
            async for chunk in resp.aiter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    event_block, buffer = buffer.split("\n\n", 1)
                    lines = event_block.strip().split("\n")
                    event_type = ""
                    data = {}
                    for line in lines:
                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            try:
                                data = json.loads(line.split(":", 1)[1].strip())
                            except Exception:
                                pass
                    if event_type:
                        # Print full data for errors
                        if "error" in event_type or "error" in data:
                            print(f"[{event_type}] FULL DATA:")
                            print(json.dumps(data, indent=2))
                        else:
                            msg = data.get("message", "")
                            print(f"[{event_type}] {msg or json.dumps(data)[:200]}")
                    if event_type in ("run_complete", "run_error"):
                        print(f"\n{'='*60}\nFINAL STATUS: {event_type}")
                        return


async def test_direct():
    """Test the ad_analyzer in total isolation to get the real traceback."""
    import os, sys
    sys.path.insert(0, r"c:\Work\Git\RetroFit\backend")
    os.chdir(r"c:\Work\Git\RetroFit\backend")
    from dotenv import load_dotenv
    load_dotenv(".env")

    from app.config import settings
    print(f"Flash model: {settings.gemini_flash_model}")
    print(f"Pro model:   {settings.gemini_pro_model}")

    from google import genai
    from google.genai import types
    from app.prompts.ad_analyzer import AD_ANALYZER_SYSTEM_PROMPT

    client = genai.Client(api_key=settings.gemini_api_key)
    parts = [
        types.Part(text=AD_ANALYZER_SYSTEM_PROMPT),
        types.Part(text="No ad image provided. Return a minimal AdContext with offer_type='none'."),
    ]

    try:
        print("Calling Gemini...")
        response = client.models.generate_content(
            model=settings.gemini_flash_model,
            contents=types.Content(parts=parts),
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                response_mime_type="application/json",
            ),
        )
        print(f"Response text ({type(response.text)}): {str(response.text)[:500]}")
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    print("=== DIRECT GEMINI TEST ===")
    asyncio.run(test_direct())
    print("\n\n=== FULL PIPELINE TEST ===")
    asyncio.run(test_run())
