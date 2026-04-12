"""AdContext model — structured output from the Ad Analyzer agent."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .shared import ColorSwatch


class AdContext(BaseModel):
    """Structured representation of an ad creative, extracted via Gemini vision."""

    model_config = ConfigDict(extra="ignore")

    # ── Copy ──────────────────────────────────────────────────────────────────
    # headline is Optional — Gemini returns null when no image is provided
    headline: Optional[str] = Field(default="(no headline)", description="Primary headline text visible in the ad")
    subheadline: Optional[str] = Field(default=None, description="Secondary headline or tagline")
    body_text: Optional[str] = Field(default=None, description="Any additional body copy")
    primary_cta_text: Optional[str] = Field(default=None, description="CTA button text if visible")
    secondary_cta_text: Optional[str] = Field(default=None)

    # ── Offer ─────────────────────────────────────────────────────────────────
    offer_type: Literal["percent_discount", "amount_discount", "bogo", "free_shipping", "none"] = Field(
        default="none",
        description="Type of offer shown in the ad",
    )
    discount_percent: Optional[float] = Field(default=None, description="e.g. 40.0 for 40% OFF")
    discount_amount: Optional[float] = Field(default=None, description="e.g. 500.0 for ₹500 OFF")
    discount_code: Optional[str] = Field(default=None, description="Promo code if shown in ad")
    urgency_phrase: Optional[str] = Field(
        default=None, description="Exact urgency/scarcity text from the ad, e.g. 'Ends Sunday'"
    )

    # ── Product ───────────────────────────────────────────────────────────────
    primary_product: Optional[str] = Field(default=None, description="Product name or descriptor")
    product_category: Optional[str] = Field(default=None, description="Product category")

    # ── Audience & tone ───────────────────────────────────────────────────────
    audience_segment: Optional[str] = Field(
        default=None, description="Plain English audience description inferred from visuals and copy"
    )
    tone: Optional[Literal["playful", "premium", "minimal", "bold", "informational", "other"]] = None
    intent_stage: Optional[Literal["awareness", "consideration", "purchase"]] = None

    # ── Visuals ───────────────────────────────────────────────────────────────
    dominant_colors: List[ColorSwatch] = Field(default_factory=list)
    background_style: Optional[str] = None
    layout_style: Optional[str] = None

    # ── Metadata ──────────────────────────────────────────────────────────────
    language: str = Field(default="en", description="BCP-47 language code")
    detected_currencies: List[str] = Field(default_factory=list, description="e.g. ['INR']")
