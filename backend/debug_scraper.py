import asyncio
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(".env")


async def test():
    from app.tools.scraper import scrape_page
    from app.tools.dom_mapper import map_semantic_elements, merge_mappings, vision_assisted_mapping
    from app.tools.shopify import detect_shopify
    from app.config import settings

    url = "https://mamaearth.in/product/onion-hair-oil"

    print("Step 1: scraping...")
    page_data = await scrape_page(url)
    html_len = len(page_data.get("rawHtml", ""))
    md_len = len(page_data.get("markdown") or "")
    has_ss = page_data.get("screenshot_bytes") is not None
    print(f"  html={html_len} markdown={md_len} screenshot={has_ss}")

    print("Step 2: shopify detect...")
    is_shopify, theme = detect_shopify(page_data["rawHtml"])
    print(f"  is_shopify={is_shopify} theme={theme}")

    print("Step 3: DOM mapping...")
    dom_elements = map_semantic_elements(page_data["rawHtml"], is_shopify=is_shopify)
    print(f"  keys={list(dom_elements.keys())}")

    print("Step 4: vision mapping (screenshot=None, should return None)...")
    vision = await vision_assisted_mapping(page_data.get("screenshot_bytes"), settings.gemini_flash_model)
    print(f"  vision={vision}")

    print("Step 5: merge into SemanticMap...")
    sm = merge_mappings(
        url=url,
        dom_elements=dom_elements,
        vision_elements=vision,
        is_shopify=is_shopify,
        theme_name=theme,
    )
    headline = sm.hero_headline.text[:60] if sm.hero_headline else None
    cta = sm.primary_cta.text[:40] if sm.primary_cta else None
    print(f"  hero_headline={headline!r}")
    print(f"  primary_cta={cta!r}")
    print("ALL STEPS OK")


if __name__ == "__main__":
    asyncio.run(test())
