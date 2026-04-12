"""CROFindings model — scored audit output from the CRO Strategist agent."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    """Score for a single CRO criterion."""

    criterion_id: str = Field(
        description="One of: message_match, hero_clarity, cta_visibility, "
        "social_proof, urgency_scarcity, trust_signals, mobile_readiness"
    )
    label: str = Field(description="Human-readable criterion name")
    score: float = Field(ge=0.0, le=100.0, description="Score 0–100")
    weight: float = Field(ge=0.0, le=1.0, description="Weight in composite score calculation")
    rationale: str = Field(description="Why this score was assigned")


class CROIssue(BaseModel):
    """A specific conversion problem identified on the page."""

    issue_id: str
    severity: Literal["critical", "high", "medium", "low"]
    criterion_id: str
    description: str = Field(description="What the issue is")
    impact: str = Field(description="Why it hurts conversion")


class ChangeCandidate(BaseModel):
    """A proposed change to improve CRO score, ready for the Copywriter agent."""

    change_id: str
    priority: int = Field(ge=1, description="1 = highest priority")
    target_selector: str = Field(description="CSS selector from SemanticMap — must exist on page")
    change_type: Literal["copy", "style", "structure"]
    current_text: Optional[str] = Field(default=None, description="Existing text at this selector")
    cro_principles: List[str] = Field(description="Which criterion IDs this change addresses")
    proposed_direction: str = Field(
        description="What the change should accomplish — NOT the final copy"
    )
    estimated_impact: Literal["high", "medium", "low"]


class CROFindings(BaseModel):
    """Complete CRO audit — scored criteria, issues, and prioritized change candidates."""

    overall_score: float = Field(ge=0.0, le=100.0, description="Weighted composite score 0–100")
    criteria: List[CriterionScore] = Field(description="Individual criterion scores")
    top_issues: List[CROIssue] = Field(description="Issues sorted by severity, critical first")
    change_candidates: List[ChangeCandidate] = Field(
        description="Proposed changes sorted by priority (1 = first to implement)"
    )
    summary: str = Field(description="1-2 sentence summary of the page's main CRO problems")
