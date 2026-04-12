"""Screenshot capture and visual diff using Playwright."""

import asyncio
import math
from typing import Optional

from app.config import settings


async def capture_screenshot_from_html(html_content: str, run_id: str, variant: str) -> Optional[bytes]:
    """
    Render an HTML string in a headless browser and capture a full-page screenshot.
    Returns PNG bytes or None if capture fails.
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1440, "height": 900})

            # Load HTML directly as content (not via URL)
            await page.set_content(html_content, wait_until="networkidle", timeout=20000)
            await asyncio.sleep(0.5)

            screenshot_bytes = await page.screenshot(full_page=True, type="png")
            await browser.close()
            return screenshot_bytes

    except Exception as e:
        print(f"[screenshot] Capture failed for run={run_id} variant={variant}: {e}")
        return None


async def compute_visual_diff(
    original_path: Optional[str],
    modified_path: Optional[str],
) -> Optional[float]:
    """
    Compute a pixel-level diff ratio between two screenshots.

    Returns a float 0.0–1.0 where 0.0 = identical, 1.0 = completely different.
    Returns None if either screenshot is unavailable.
    """
    if not original_path or not modified_path:
        return None

    try:
        from PIL import Image
        import numpy as np

        orig = Image.open(original_path).convert("RGB")
        mod = Image.open(modified_path).convert("RGB")

        # Resize to same dimensions for comparison
        if orig.size != mod.size:
            mod = mod.resize(orig.size, Image.LANCZOS)

        orig_arr = np.array(orig, dtype=float)
        mod_arr = np.array(mod, dtype=float)

        # Mean absolute difference per pixel (0-255 range → normalize to 0-1)
        diff = np.abs(orig_arr - mod_arr).mean() / 255.0
        return float(diff)

    except Exception as e:
        print(f"[screenshot] Visual diff failed: {e}")
        return None
