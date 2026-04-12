"""Web scraping — Firecrawl API wrapper and Playwright screenshot capture."""

import asyncio
import base64
from typing import Optional

import httpx

from app.config import settings


async def scrape_page(url: str) -> dict:
    """
    Scrape a landing page using Firecrawl for HTML/markdown and Playwright for screenshots.

    Returns:
        dict with keys: rawHtml, markdown, screenshot_bytes (bytes | None)
    """
    firecrawl_data = await _scrape_with_firecrawl(url)
    screenshot_bytes = await _take_screenshot(url)

    return {
        "rawHtml": firecrawl_data.get("rawHtml", ""),
        "markdown": firecrawl_data.get("markdown"),
        "screenshot_bytes": screenshot_bytes,
    }


async def _scrape_with_firecrawl(url: str) -> dict:
    """Call Firecrawl API to get rawHtml + markdown."""
    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["rawHtml", "markdown"],
        "waitFor": 2000,  # 2s for JS rendering
        "timeout": 30000,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {})


async def _take_screenshot(url: str) -> Optional[bytes]:
    """Capture a full-page screenshot using Playwright (headless Chromium)."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1440, "height": 900})

            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)  # Let lazy-loaded images settle

            screenshot_bytes = await page.screenshot(full_page=True, type="png")
            await browser.close()
            return screenshot_bytes

    except Exception as e:
        # Screenshot failure is non-fatal — pipeline continues without it
        print(f"[scraper] Screenshot failed for {url}: {e}")
        return None
