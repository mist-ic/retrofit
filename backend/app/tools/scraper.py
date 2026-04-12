"""Web scraping — Firecrawl API with Playwright fallback.

If FIRECRAWL_API_KEY is not set, falls back to Playwright + html2text.
Both paths return the same dict shape: {rawHtml, markdown, screenshot_bytes}.
"""

import asyncio
from typing import Optional

from app.config import settings


async def scrape_page(url: str) -> dict:
    """
    Scrape a landing page. Uses Firecrawl if API key is configured,
    otherwise falls back to Playwright (free, no external dependency).

    Returns:
        dict with keys: rawHtml (str), markdown (str | None), screenshot_bytes (bytes | None)
    """
    if settings.firecrawl_api_key:
        return await _scrape_with_firecrawl(url)
    else:
        return await _scrape_with_playwright(url)


# ── Firecrawl path ────────────────────────────────────────────────────────────

async def _scrape_with_firecrawl(url: str) -> dict:
    """Firecrawl API — better JS rendering and anti-bot handling."""
    import httpx

    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["rawHtml", "markdown"],
        "waitFor": 2000,
        "timeout": 30000,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

    # Take screenshot separately with Playwright (Firecrawl doesn't return image bytes)
    screenshot_bytes = await _take_playwright_screenshot(url)

    return {
        "rawHtml": data.get("rawHtml", ""),
        "markdown": data.get("markdown"),
        "screenshot_bytes": screenshot_bytes,
    }


# ── Playwright fallback path ──────────────────────────────────────────────────

async def _scrape_with_playwright(url: str) -> dict:
    """
    Playwright-only scraping — headless Chromium, no external API.
    Generates markdown from HTML using html2text.
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            )

            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1.5)  # Let lazy-loaded content settle

            raw_html = await page.content()
            screenshot_bytes = await page.screenshot(full_page=True, type="png")

            await browser.close()

        markdown = _html_to_markdown(raw_html)

        return {
            "rawHtml": raw_html,
            "markdown": markdown,
            "screenshot_bytes": screenshot_bytes,
        }

    except Exception as e:
        print(f"[scraper] Playwright scrape failed for {url}: {e}")
        return {"rawHtml": "", "markdown": None, "screenshot_bytes": None}


async def _take_playwright_screenshot(url: str) -> Optional[bytes]:
    """Capture a full-page screenshot — used alongside Firecrawl."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)
            screenshot_bytes = await page.screenshot(full_page=True, type="png")
            await browser.close()
            return screenshot_bytes

    except Exception as e:
        print(f"[scraper] Screenshot failed for {url}: {e}")
        return None


# ── Markdown conversion ───────────────────────────────────────────────────────

def _html_to_markdown(html: str) -> Optional[str]:
    """
    Convert raw HTML to clean markdown using html2text.
    Strips navigation, scripts, styles — leaves content text.
    Falls back to None if html2text is not installed.
    """
    try:
        import html2text

        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_tables = False
        h.body_width = 0  # Don't wrap lines
        h.ignore_emphasis = False

        return h.handle(html)[:15000]  # Cap at 15k chars — enough for LLM context

    except ImportError:
        # html2text not installed — extract plain text via BeautifulSoup as fallback
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "head"]):
                tag.decompose()
            return soup.get_text("\n", strip=True)[:15000]
        except Exception:
            return None
