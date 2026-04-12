"""Tests for html_patcher — each PatchOperation type."""

import pytest
from app.models.patch_spec import PatchSpec
from app.tools.html_patcher import apply_patch

SAMPLE_HTML = """<html>
<head><title>Test Page</title></head>
<body>
  <h1 id="hero-title">Welcome to Our Store</h1>
  <p class="hero-sub">Discover amazing products</p>
  <a href="/shop" class="btn btn-primary">Shop Now</a>
  <div class="trust-badge">Secure Checkout</div>
</body>
</html>"""


def _make_spec(operations: list) -> PatchSpec:
    return PatchSpec(variant_id="test", description="test", operations=operations)


def test_replace_text():
    spec = _make_spec([{"op": "replaceText", "selector": "#hero-title", "new_text": "40% OFF Summer Sale"}])
    result, warnings = apply_patch(SAMPLE_HTML, spec)
    assert "40% OFF Summer Sale" in result
    assert "Welcome to Our Store" not in result
    assert warnings == []


def test_replace_text_missing_selector():
    spec = _make_spec([{"op": "replaceText", "selector": "#nonexistent", "new_text": "Hello"}])
    result, warnings = apply_patch(SAMPLE_HTML, spec)
    assert len(warnings) == 1
    assert "nonexistent" in warnings[0]
    # Original HTML preserved
    assert "Welcome to Our Store" in result


def test_add_class():
    spec = _make_spec([{"op": "addClass", "selector": "a.btn", "class_name": "btn-urgent"}])
    result, _ = apply_patch(SAMPLE_HTML, spec)
    assert "btn-urgent" in result


def test_remove_class():
    spec = _make_spec([{"op": "removeClass", "selector": "a.btn", "class_name": "btn-primary"}])
    result, _ = apply_patch(SAMPLE_HTML, spec)
    assert "btn-primary" not in result


def test_replace_style():
    spec = _make_spec([
        {"op": "replaceStyle", "selector": "a.btn", "css_text": "background: #e53e3e; color: white;"}
    ])
    result, _ = apply_patch(SAMPLE_HTML, spec)
    assert "background: #e53e3e" in result


def test_insert_before():
    spec = _make_spec([
        {"op": "insertBefore", "selector": "#hero-title", "html": "<div class='promo-bar'>Limited time</div>"}
    ])
    result, _ = apply_patch(SAMPLE_HTML, spec)
    assert "promo-bar" in result
    # Promo bar must appear before hero title in output
    assert result.index("promo-bar") < result.index("hero-title")


def test_multiple_operations_in_order():
    spec = _make_spec([
        {"op": "replaceText", "selector": "#hero-title", "new_text": "Summer Sale 40% OFF"},
        {"op": "replaceText", "selector": "a.btn", "new_text": "Claim Offer"},
    ])
    result, warnings = apply_patch(SAMPLE_HTML, spec)
    assert "Summer Sale 40% OFF" in result
    assert "Claim Offer" in result
    assert len(warnings) == 0
