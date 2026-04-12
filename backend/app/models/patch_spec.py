"""PatchSpec model — the typed instruction set the Copywriter sends to the Code Modifier."""

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field


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


class InsertBeforeOp(BaseModel):
    """Insert an HTML snippet immediately before a target element."""

    op: Literal["insertBefore"]
    selector: str
    html: str = Field(
        description="Inline-styled HTML snippet to insert. Keep simple — "
        "<div> or <span> with inline styles only."
    )


class InsertAfterOp(BaseModel):
    """Insert an HTML snippet immediately after a target element."""

    op: Literal["insertAfter"]
    selector: str
    html: str = Field(
        description="Inline-styled HTML snippet to insert. Keep simple — "
        "<div> or <span> with inline styles only."
    )


class ReplaceStyleOp(BaseModel):
    """Override the inline style of an element."""

    op: Literal["replaceStyle"]
    selector: str
    css_text: str = Field(
        description="Full inline style string, e.g. 'color: #fff; background: #e53e3e;'"
    )


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


class PatchSpec(BaseModel):
    """Complete set of surgical instructions for modifying a landing page."""

    variant_id: str = Field(description="Unique identifier for this variant, e.g. 'hero-variant-a'")
    description: str = Field(description="Brief summary of what this patch does")
    operations: List[PatchOperation] = Field(
        description="Ordered list of operations to apply. Applied sequentially."
    )
