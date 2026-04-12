"""Tests for DOM semantic mapper heuristics."""

import pytest
from app.tools.dom_mapper import map_semantic_elements, _detect_page_type
from app.tools.shopify import detect_shopify

GENERIC_HTML = """<html>
<head><title>Summer Collection</title></head>
<body>
  <div class="announcement-bar">Free shipping on orders over ₹999</div>
  <section class="hero">
    <h1>Summer Sale — 40% OFF</h1>
    <p class="subtext">Shop our latest collection</p>
    <a href="/shop" class="btn btn-primary">Shop Now</a>
  </section>
  <section class="social-proof">
    <span>4.8 stars from 12,000+ reviews</span>
  </section>
  <div class="trust-badge">100% Secure Checkout</div>
</body>
</html>"""

SHOPIFY_HTML = """<html>
<head></head>
<body>
  <section data-section-type="image-banner">
    <h2>New Arrivals</h2>
    <a class="btn btn-primary">Shop Collection</a>
  </section>
  <script>window.Shopify = {}; Shopify.theme = {"name": "Dawn"};</script>
  <div>cdn.shopify.com</div>
</body>
</html>"""


def test_finds_hero_headline():
    elements = map_semantic_elements(GENERIC_HTML)
    assert "hero_headline" in elements
    assert "Summer Sale" in elements["hero_headline"].text


def test_finds_primary_cta():
    elements = map_semantic_elements(GENERIC_HTML)
    assert "primary_cta" in elements


def test_finds_announcement_bar():
    elements = map_semantic_elements(GENERIC_HTML)
    assert "announcement_bar" in elements


def test_finds_social_proof():
    elements = map_semantic_elements(GENERIC_HTML)
    assert "social_proof_blocks" in elements
    assert len(elements["social_proof_blocks"]) > 0


def test_shopify_detection_positive():
    is_shopify, theme = detect_shopify(SHOPIFY_HTML)
    assert is_shopify is True
    assert theme == "Dawn"


def test_shopify_detection_negative():
    is_shopify, theme = detect_shopify(GENERIC_HTML)
    assert is_shopify is False
    assert theme is None


def test_detect_page_type_product():
    assert _detect_page_type("https://example.com/products/shirt") == "product"


def test_detect_page_type_homepage():
    assert _detect_page_type("https://example.com") == "homepage"


def test_detect_page_type_landing():
    assert _detect_page_type("https://example.com/lp/summer") == "landing"
