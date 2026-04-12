"""QAReport model — validation output from the QA Verifier agent."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class StructuralIssue(BaseModel):
    """A structural problem found in the modified HTML."""

    severity: Literal["critical", "warning"]
    code: str = Field(description="Machine-readable issue code, e.g. 'MISSING_HERO_ELEMENT'")
    message: str = Field(description="Human-readable description of the issue")
    selector: Optional[str] = Field(default=None, description="The selector that caused the issue")


class HallucinationFlag(BaseModel):
    """A piece of content in the modified page not grounded in source material."""

    code: str = Field(description="e.g. 'NEW_DISCOUNT_VALUE', 'INVENTED_PRODUCT_NAME'")
    message: str = Field(description="What was hallucinated and why it's flagged")
    offending_text: str = Field(description="The exact text that triggered this flag")


class QAReport(BaseModel):
    """Full validation report for a modified landing page variant."""

    variant_id: str
    passed: bool = Field(description="True if the variant passes all critical checks")

    # ── Structural checks ─────────────────────────────────────────────────────
    is_valid_html: bool
    structural_issues: List[StructuralIssue] = Field(default_factory=list)
    key_elements_present: bool = Field(
        description="True if hero headline, primary CTA, and at least one trust element are present"
    )

    # ── Visual integrity ──────────────────────────────────────────────────────
    visual_diff_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Pixel diff ratio between original and modified screenshots. "
        "0.0 = identical, 1.0 = completely different. Fails QA if > 0.5.",
    )

    # ── Hallucination check ───────────────────────────────────────────────────
    hallucination_flags: List[HallucinationFlag] = Field(default_factory=list)
    grounded_change_count: int = Field(
        description="Number of patch operations that passed grounding checks"
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    failure_reasons: List[str] = Field(
        default_factory=list,
        description="Human-readable reasons for failure — fed back to Code Modifier on retry",
    )
