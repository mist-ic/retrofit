"""PatchSpec model — the typed instruction set the Copywriter sends to the Code Modifier."""

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReplaceTextOp(BaseModel):
    """Replace the text content of an element."""

    op: Literal["replaceText"]
    selector: str = Field(description="CSS selector targeting the element")
    new_text: str = Field(description="Replacement text — must be grounded in ad or original page")
    original_text: Optional[str] = Field(default=None, description="Original text for audit trail")


class ReplaceAttributeOp(BaseModel):
    """Replace a specific HTML attribute value."""

    op: Literal["replaceAttribute"]
    selector: str
    attribute: str = Field(description="HTML attribute name, e.g. 'href', 'src', 'alt'")
    new_value: str


class AddClassOp(BaseModel):
    """Add a CSS class to an element."""

    op: Literal["addClass"]
    selector: str
    class_name: str


class RemoveClassOp(BaseModel):
    """Remove a CSS class from an element."""

    op: Literal["removeClass"]
    selector: str
    class_name: str


# ── Alias coercion for html field ─────────────────────────────────────────────
# Gemini models frequently use 'content', 'new_html', 'markup', 'snippet',
# 'value', 'text', or 'inner_html' instead of the required 'html' key.
_HTML_ALIASES = ("content", "new_html", "markup", "snippet", "value", "text", "inner_html")

_DEFAULT_HTML = (
    '<div style="display:block;position:relative;clear:both;'
    'padding:4px 8px;"></div>'
)


def _coerce_html_field(data: object) -> object:
    """Normalize LLM output: coerce alternative field names to 'html'."""
    if not isinstance(data, dict):
        return data
    if "html" in data and data["html"]:
        return data
    data = dict(data)
    for alias in _HTML_ALIASES:
        if alias in data and data[alias]:
            data["html"] = data.pop(alias)
            return data
    # Last resort — set a safe fallback so Pydantic doesn't crash
    if "html" not in data or not data.get("html"):
        data["html"] = _DEFAULT_HTML
    return data


class InsertBeforeOp(BaseModel):
    """Insert an HTML snippet immediately before a target element."""

    model_config = ConfigDict(extra="ignore")

    op: Literal["insertBefore"]
    selector: str
    html: str = Field(
        default="",
        description="Inline-styled HTML snippet to insert. Keep simple — "
        "<div> or <span> with inline styles only."
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_html_alias(cls, data: object) -> object:
        """LLM sometimes returns 'content', 'new_html', etc. instead of 'html'."""
        return _coerce_html_field(data)


class InsertAfterOp(BaseModel):
    """Insert an HTML snippet immediately after a target element."""

    model_config = ConfigDict(extra="ignore")

    op: Literal["insertAfter"]
    selector: str
    html: str = Field(
        default="",
        description="Inline-styled HTML snippet to insert. Keep simple — "
        "<div> or <span> with inline styles only."
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_html_alias(cls, data: object) -> object:
        """LLM sometimes returns 'content', 'new_html', etc. instead of 'html'."""
        return _coerce_html_field(data)


class ReplaceStyleOp(BaseModel):
    """Override the inline style of an element."""

    model_config = ConfigDict(extra="ignore")

    op: Literal["replaceStyle"]
    selector: str
    css_text: str = Field(
        description="Full inline style string, e.g. 'color: #fff; background: #e53e3e;'"
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_css_alias(cls, data: object) -> object:
        """LLM sometimes returns 'css', 'style', or 'css_value' instead of 'css_text'."""
        if isinstance(data, dict) and "css_text" not in data:
            for alias in ("css", "style", "css_value", "value"):
                if alias in data:
                    data = dict(data)
                    data["css_text"] = data.pop(alias)
                    break
        return data


# Discriminated union — Pydantic uses the 'op' literal to pick the right model.
# Each op value MUST map to exactly one class.
# InsertBefore and InsertAfter are intentionally separate classes for this reason.
PatchOperation = Annotated[
    Union[
        ReplaceTextOp,
        ReplaceAttributeOp,
        AddClassOp,
        RemoveClassOp,
        InsertBeforeOp,
        InsertAfterOp,
        ReplaceStyleOp,
    ],
    Field(discriminator="op"),
]


def sanitize_operations(raw_ops: list) -> list:
    """
    Pre-process raw LLM operation dicts BEFORE PatchSpec.model_validate().

    Pydantic discriminated unions can skip model_validators in some cases,
    so we defensively fix known LLM output issues at the list level.
    This is the primary defense; the per-model validators are a backup.
    """
    cleaned = []
    for op_dict in raw_ops:
        if not isinstance(op_dict, dict):
            cleaned.append(op_dict)
            continue
        op_type = op_dict.get("op", "")
        if op_type in ("insertBefore", "insertAfter"):
            op_dict = _coerce_html_field(op_dict)
        elif op_type == "replaceStyle":
            if "css_text" not in op_dict:
                for alias in ("css", "style", "css_value", "value"):
                    if alias in op_dict:
                        op_dict = dict(op_dict)
                        op_dict["css_text"] = op_dict.pop(alias)
                        break
        cleaned.append(op_dict)
    return cleaned


class PatchSpec(BaseModel):
    """Complete set of surgical instructions for modifying a landing page."""

    variant_id: str = Field(description="Unique identifier for this variant, e.g. 'hero-variant-a'")
    description: str = Field(description="Brief summary of what this patch does")
    operations: List[PatchOperation] = Field(
        description="Ordered list of operations to apply. Applied sequentially."
    )

    @model_validator(mode="before")
    @classmethod
    def pre_sanitize_ops(cls, data: object) -> object:
        """Run sanitize_operations on the raw operations list before Pydantic touches it."""
        if isinstance(data, dict) and "operations" in data:
            data = dict(data)
            data["operations"] = sanitize_operations(data["operations"])
        return data

