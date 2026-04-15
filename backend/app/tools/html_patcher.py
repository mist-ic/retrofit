"""HTML patcher — applies PatchSpec operations to raw HTML using BeautifulSoup."""

import re
from bs4 import BeautifulSoup

from app.models.patch_spec import PatchSpec


def _sanitize_inserted_html(raw_html: str) -> str:
    """
    Force layout-safe CSS on any inserted HTML so it cannot cause overlap on the target page.

    Shopify/live-site themes often use `position: absolute` or complex z-index stacking.
    Injecting a new element with `position: absolute` breaks the layout by rendering the
    new element on top of (or behind) existing elements.

    We always override/append:
      display: block
      position: relative  (overrides any absolute/fixed the LLM may have generated)
      clear: both         (prevents float collapse issues)

    This is applied ONLY to the outermost root element of the inserted HTML.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    root = next((t for t in soup.children if hasattr(t, "attrs")), None)
    if root is None:
        return raw_html

    # Parse existing style attribute
    existing_style: str = root.get("style", "") or ""

    # Remove any position: absolute / fixed that LLM may have added
    safe_style = re.sub(r"position\s*:\s*(absolute|fixed)\s*;?", "", existing_style, flags=re.IGNORECASE)

    # Ensure our safe properties are present
    safe_overrides = "display: block; position: relative; clear: both;"

    # Merge: safe_overrides take precedence (placed at end)
    merged = f"{safe_style.rstrip('; ')}; {safe_overrides}".lstrip("; ").strip()
    root["style"] = merged

    return str(soup)


def apply_patch(raw_html: str, patch: PatchSpec) -> tuple[str, list[str]]:
    """
    Apply a PatchSpec to raw HTML and return (modified_html, warnings).

    Operations are applied in order. Unknown selectors are skipped with a warning
    rather than failing — partial output is better than no output.
    """
    soup = BeautifulSoup(raw_html, "lxml")
    warnings: list[str] = []

    for op in patch.operations:
        elements = soup.select(op.selector)
        if not elements:
            warnings.append(f"Selector not found, skipped: {op.selector}")
            continue

        el = elements[0]  # Always target first match

        op_type = op.op

        if op_type == "replaceText":
            el.string = op.new_text

        elif op_type == "replaceAttribute":
            el[op.attribute] = op.new_value

        elif op_type == "addClass":
            existing = el.get("class", [])
            if op.class_name not in existing:
                el["class"] = existing + [op.class_name]

        elif op_type == "removeClass":
            existing = el.get("class", [])
            el["class"] = [c for c in existing if c != op.class_name]

        elif op_type == "insertBefore":
            safe_html = _sanitize_inserted_html(op.html)
            new_el = BeautifulSoup(safe_html, "html.parser")
            el.insert_before(new_el)

        elif op_type == "insertAfter":
            safe_html = _sanitize_inserted_html(op.html)
            new_el = BeautifulSoup(safe_html, "html.parser")
            el.insert_after(new_el)

        elif op_type == "replaceStyle":
            el["style"] = op.css_text

    return str(soup), warnings

