"""Web scraping — Firecrawl API with Playwright fallback.

If FIRECRAWL_API_KEY is not set, falls back to Playwright + html2text.
Both paths return the same dict shape: {rawHtml, markdown, screenshot_bytes}.

Windows note: asyncio.SelectorEventLoop (used by uvicorn on Windows) cannot
spawn subprocesses. Playwright uses subprocess to talk to the browser.
Fix: use synchronous Playwright API inside asyncio.to_thread().
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

    # Screenshot via sync Playwright in thread (safe on Windows SelectorEventLoop)
    screenshot_bytes = await asyncio.to_thread(_sync_playwright_screenshot, url)

    return {
        "rawHtml": data.get("rawHtml", ""),
        "markdown": data.get("markdown"),
        "screenshot_bytes": screenshot_bytes,
    }


# ── Playwright fallback path ──────────────────────────────────────────────────

async def _scrape_with_playwright(url: str) -> dict:
    """
    Playwright-only scraping — headless Chromium, no external API.
    Runs synchronous Playwright in a thread (required on Windows).
    """
    result = await asyncio.to_thread(_sync_playwright_scrape, url)
    return result


# ── Sync Playwright helpers (thread-safe on Windows) ─────────────────────────

def _sync_playwright_scrape(url: str) -> dict:
    """
    Synchronous Playwright scrape — called via asyncio.to_thread().
    Uses sync_playwright which doesn't require ProactorEventLoop on Windows.
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            )
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            import time; time.sleep(2)  # Let lazy-loaded content settle

            raw_html = page.content()
            screenshot_bytes = page.screenshot(full_page=True, type="png")
            browser.close()

        markdown = _html_to_markdown(raw_html)
        return {
            "rawHtml": raw_html,
            "markdown": markdown,
            "screenshot_bytes": screenshot_bytes,
        }

    except Exception as e:
        print(f"[scraper] Playwright scrape failed for {url}: {e}")
        return {"rawHtml": "", "markdown": None, "screenshot_bytes": None}


def _sync_playwright_screenshot(url: str) -> Optional[bytes]:
    """
    Capture a full-page screenshot synchronously — called via asyncio.to_thread().
    Used alongside Firecrawl (which returns HTML/markdown but not screenshots).
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            import time; time.sleep(1.5)
            screenshot_bytes = page.screenshot(full_page=True, type="png")
            browser.close()
            return screenshot_bytes

    except Exception as e:
        print(f"[scraper] Screenshot failed for {url}: {e}")
        return None


# ── Markdown conversion ───────────────────────────────────────────────────────

def _html_to_markdown(html: str) -> Optional[str]:
    """
    Convert raw HTML to clean markdown using html2text.
    Strips navigation, scripts, styles — leaves content text.
    Falls back to BeautifulSoup plain text if html2text not installed.
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
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "head"]):
                tag.decompose()
            return soup.get_text("\n", strip=True)[:15000]
        except Exception:
            return None
