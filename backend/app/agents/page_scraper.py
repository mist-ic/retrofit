"""Page Scraper agent — scrapes the landing page and builds a SemanticMap."""

from langgraph.types import StreamWriter

from app.config import settings
from app.models.pipeline import PageSnapshot
from app.storage.artifacts import save_html, save_screenshot
from app.tools.dom_mapper import map_semantic_elements, merge_mappings, vision_assisted_mapping
from app.tools.scraper import scrape_page
from app.tools.shopify import detect_shopify


async def page_scraper_node(state: dict, writer: StreamWriter) -> dict:
    """
    LangGraph node: scrape the landing page → return PageSnapshot + SemanticMap.

    Steps:
    1. Firecrawl (or Playwright fallback) for rawHtml + markdown
    2. Playwright for full-page screenshot (non-fatal if fails)
    3. Shopify detection
    4. DOM heuristic element mapping
    5. Optional vision-assisted bounding boxes
    6. Merge into SemanticMap
    """
    writer({"event": "stage_start", "stage": "page_scraper", "message": "Scraping landing page..."})

    try:
        url = state["landing_page_url"]
        run_id = state["run_id"]

        # ── Steps 1+2: scrape HTML and take screenshot ─────────────────────────
        page_data = await scrape_page(url)

        writer({
            "event": "stage_progress",
            "stage": "page_scraper",
            "message": f"Page fetched ({len(page_data.get('rawHtml', '')) // 1024}KB HTML). Mapping elements...",
        })

        # ── Step 3: save screenshot artifact ──────────────────────────────────
        screenshot_path = None
        if page_data.get("screenshot_bytes"):
            screenshot_path = await save_screenshot(
                run_id, page_data["screenshot_bytes"], variant="original"
            )

        page_snapshot = PageSnapshot(
            url=url,
            raw_html=page_data["rawHtml"],
            clean_markdown=page_data.get("markdown"),
            screenshot_path=screenshot_path,
        )

        # Save original HTML with base tag so /api/preview/{id}/original renders correctly
        from app.tools.url_rewriter import rewrite_urls_with_base_tag
        original_html_for_preview = rewrite_urls_with_base_tag(page_data["rawHtml"], url)
        await save_html(run_id, original_html_for_preview, "original")

        # ── Step 4: Shopify detection ──────────────────────────────────────────
        is_shopify, theme_name = detect_shopify(page_data["rawHtml"])

        # ── Step 5: DOM heuristic mapping ─────────────────────────────────────
        dom_elements = map_semantic_elements(page_data["rawHtml"], is_shopify=is_shopify)

        # ── Step 6: vision-assisted mapping (non-fatal) ───────────────────────
        vision_elements = await vision_assisted_mapping(
            screenshot_bytes=page_data.get("screenshot_bytes"),
            llm_model=settings.gemini_flash_model,
        )

        # ── Step 7: merge into SemanticMap ────────────────────────────────────
        semantic_map = merge_mappings(
            url=url,
            dom_elements=dom_elements,
            vision_elements=vision_elements,
            is_shopify=is_shopify,
            theme_name=theme_name,
        )

        el_count = sum(1 for v in [
            semantic_map.hero_headline, semantic_map.primary_cta,
            semantic_map.hero_subheadline, semantic_map.announcement_bar,
        ] if v is not None) + len(semantic_map.social_proof_blocks)

        writer({
            "event": "stage_complete",
            "stage": "page_scraper",
            "message": f"Mapped {el_count} semantic elements",
            "data": {
                "is_shopify": is_shopify,
                "shopify_theme": theme_name,
                "has_hero": semantic_map.hero_headline is not None,
                "has_cta": semantic_map.primary_cta is not None,
                "markdown_chars": len(page_data.get("markdown") or ""),
            },
        })

        return {
            "page_snapshot": page_snapshot.model_dump(),
            "semantic_map": semantic_map.model_dump(),
            "current_stage": "page_scraper_complete",
        }

    except Exception as e:
        writer({"event": "stage_error", "stage": "page_scraper", "message": f"Scraping failed: {e}"})
        raise
