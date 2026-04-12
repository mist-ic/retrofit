"""Page Scraper agent — scrapes the landing page and builds a SemanticMap."""

from langgraph.config import get_stream_writer

from app.config import settings
from app.models.pipeline import PageSnapshot, PipelineState
from app.models.semantic_map import SemanticMap
from app.storage.artifacts import save_screenshot
from app.tools.dom_mapper import map_semantic_elements, merge_mappings, vision_assisted_mapping
from app.tools.scraper import scrape_page
from app.tools.shopify import detect_shopify


async def page_scraper_node(state: dict) -> dict:
    """
    LangGraph node: scrape the landing page → return PageSnapshot + SemanticMap.

    Steps:
    1. Firecrawl for rawHtml + markdown
    2. Playwright for full-page screenshot
    3. Shopify detection
    4. DOM heuristic element mapping
    5. Optional vision-assisted bounding boxes
    6. Merge into SemanticMap
    """
    writer = get_stream_writer()
    writer({"event": "stage_start", "stage": "page_scraper", "message": "Scraping landing page..."})

    ps = PipelineState(**state)
    url = ps.landing_page_url

    # Step 1+2 — scrape HTML and take screenshot
    page_data = await scrape_page(url)

    writer({"event": "stage_progress", "stage": "page_scraper", "message": "Page scraped. Mapping elements..."})

    # Step 3 — save screenshot artifact
    screenshot_path = None
    if page_data.get("screenshot_bytes"):
        screenshot_path = await save_screenshot(
            ps.run_id, page_data["screenshot_bytes"], variant="original"
        )

    page_snapshot = PageSnapshot(
        url=url,
        raw_html=page_data["rawHtml"],
        clean_markdown=page_data.get("markdown"),
        screenshot_path=screenshot_path,
    )

    # Step 4 — Shopify detection
    is_shopify, theme_name = detect_shopify(page_data["rawHtml"])

    # Step 5 — DOM heuristic mapping
    dom_elements = map_semantic_elements(page_data["rawHtml"], is_shopify=is_shopify)

    # Step 6 — Vision-assisted mapping (improves bbox accuracy, non-fatal if fails)
    vision_elements = await vision_assisted_mapping(
        screenshot_bytes=page_data.get("screenshot_bytes"),
        llm_model=settings.gemini_flash_model,
    )

    # Step 7 — Merge into SemanticMap
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
        },
    })

    return {
        "page_snapshot": page_snapshot.model_dump(),
        "semantic_map": semantic_map.model_dump(),
        "current_stage": "page_scraper_complete",
    }
