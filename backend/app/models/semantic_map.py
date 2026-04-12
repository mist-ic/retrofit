"""SemanticMap model — structured representation of a landing page's key elements."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .shared import BoundingBox


class PageElement(BaseModel):
    """A single semantic element identified on the landing page."""

    role: str = Field(
        description="Semantic role, e.g. 'hero_headline', 'primary_cta', 'social_proof_block'"
    )
    selector: str = Field(description="CSS selector targeting this element")
    xpath: Optional[str] = Field(default=None, description="XPath fallback")
    text: Optional[str] = Field(default=None, description="Current text content (truncated to 500 chars)")
    html: Optional[str] = Field(default=None, description="Raw HTML of the element (truncated to 2000 chars)")
    bbox: Optional[BoundingBox] = Field(
        default=None, description="Pixel bounding box from vision-assisted mapping"
    )
    is_above_the_fold: Optional[bool] = Field(
        default=None, description="True if element is visible without scrolling (1080px viewport)"
    )
    importance: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Heuristic importance score for CRO prioritization"
    )


class SemanticMap(BaseModel):
    """
    Mapping of key semantic elements on a landing page.
    Built by combining DOM heuristics + optional vision-assisted bounding boxes.
    """

    url: str
    page_title: Optional[str] = None

    # ── Hero area ─────────────────────────────────────────────────────────────
    hero_section: Optional[PageElement] = None
    hero_headline: Optional[PageElement] = None
    hero_subheadline: Optional[PageElement] = None
    hero_image: Optional[PageElement] = None

    # ── CTAs ──────────────────────────────────────────────────────────────────
    primary_cta: Optional[PageElement] = None
    secondary_cta: Optional[PageElement] = None

    # ── Above-fold trust signals ──────────────────────────────────────────────
    announcement_bar: Optional[PageElement] = None
    social_proof_blocks: List[PageElement] = Field(default_factory=list)
    trust_badges: List[PageElement] = Field(default_factory=list)
    price_block: Optional[PageElement] = None
    benefit_bullets: Optional[PageElement] = None

    # ── Shopify-specific ──────────────────────────────────────────────────────
    is_shopify: bool = Field(default=False, description="True if page is a Shopify store")
    shopify_theme: Optional[str] = Field(
        default=None, description="Detected Shopify theme name, e.g. 'Dawn', 'Debut'"
    )
    page_type: Optional[Literal["homepage", "collection", "product", "landing", "other"]] = Field(
        default=None, description="Page type inferred from URL patterns and content"
    )
