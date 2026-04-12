"""Shopify detection — identifies Shopify stores and theme names from raw HTML."""

import re


def detect_shopify(raw_html: str) -> tuple[bool, str | None]:
    """
    Detect if a page is a Shopify store and identify the theme if possible.
    Returns (is_shopify, theme_name_or_none).
    """
    markers = [
        "cdn.shopify.com",
        "cdn.shopifycdn.net",
        "shopify-digital-wallet",
        "data-shopify",
        "data-section-id",
        "Shopify.theme",
        "myshopify.com",
        "window.Shopify",
    ]

    is_shopify = any(marker in raw_html for marker in markers)

    if not is_shopify:
        return False, None

    # Try to extract theme name from Shopify global object
    theme_name = None
    theme_match = re.search(
        r'Shopify\.theme\s*=\s*\{[^}]*"name"\s*:\s*"([^"]+)"', raw_html
    )
    if theme_match:
        theme_name = theme_match.group(1)
    else:
        # Heuristic fallbacks based on theme-specific CSS classes
        if "banner__content" in raw_html or "image-banner" in raw_html:
            theme_name = "Dawn (probable)"
        elif "hero__content" in raw_html and "shopify" in raw_html.lower():
            theme_name = "Debut (probable)"
        elif "hero-section" in raw_html:
            theme_name = "Unknown Shopify theme"

    return True, theme_name


def get_shopify_hero_selectors() -> list[str]:
    """Return priority-ordered Shopify-specific selectors for hero detection."""
    return [
        "[data-section-type*='hero']",
        "[data-section-type*='banner']",
        "[data-section-type='slideshow']",
        ".hero",
        ".banner",
        ".image-banner",
        ".slideshow",
        ".hero-section",
        "[class*='hero']",
    ]
