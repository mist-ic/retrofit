"""HTML patcher — applies PatchSpec operations to raw HTML using BeautifulSoup."""

from bs4 import BeautifulSoup

from app.models.patch_spec import PatchSpec


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
            new_el = BeautifulSoup(op.html, "html.parser")
            el.insert_before(new_el)

        elif op_type == "insertAfter":
            new_el = BeautifulSoup(op.html, "html.parser")
            el.insert_after(new_el)

        elif op_type == "replaceStyle":
            el["style"] = op.css_text

    return str(soup), warnings
