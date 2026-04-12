"""Tools package — scraping, DOM manipulation, validation utilities."""

from .dom_mapper import map_semantic_elements, merge_mappings, vision_assisted_mapping
from .html_patcher import apply_patch
from .scraper import scrape_page
from .screenshot import capture_screenshot_from_html, compute_visual_diff
from .shopify import detect_shopify
from .url_rewriter import rewrite_urls_with_base_tag
from .validators import check_key_elements, detect_hallucinations, validate_html_structure

__all__ = [
    "scrape_page",
    "detect_shopify",
    "map_semantic_elements",
    "merge_mappings",
    "vision_assisted_mapping",
    "apply_patch",
    "rewrite_urls_with_base_tag",
    "capture_screenshot_from_html",
    "compute_visual_diff",
    "validate_html_structure",
    "check_key_elements",
    "detect_hallucinations",
]
