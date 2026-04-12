"""Pipeline state and I/O models — the backbone of the LangGraph pipeline."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .ad_context import AdContext
from .cro_findings import CROFindings
from .patch_spec import PatchSpec
from .qa_report import QAReport
from .semantic_map import SemanticMap


class PageSnapshot(BaseModel):
    """Raw data captured from the landing page during scraping."""

    url: str
    raw_html: str = Field(description="Full rawHtml from Firecrawl or Playwright")
    clean_markdown: Optional[str] = Field(
        default=None, description="Cleaned markdown from Firecrawl — used for CRO text analysis"
    )
    screenshot_path: Optional[str] = Field(
        default=None, description="Path or GCS URI to full-page screenshot"
    )
    screenshot_hero_path: Optional[str] = Field(
        default=None, description="Path or GCS URI to cropped hero-area screenshot"
    )


class ExplanationItem(BaseModel):
    """Explanation for a single change applied to the page."""

    change_id: str = Field(description="Matches PatchOperation or ChangeCandidate id")
    element_selector: str
    original_text: Optional[str] = None
    new_text: Optional[str] = None
    change_type: str = Field(description="'copy', 'style', or 'structure'")
    cro_principles: List[str] = Field(default_factory=list, description="CRO criterion IDs addressed")
    rationale: str = Field(description="Why this change was made — shown in Explanation Panel")


class PipelineState(BaseModel):
    """
    Complete state object flowing through all LangGraph agent nodes.
    Fields are populated progressively as each agent completes.
    """

    # ── Inputs ────────────────────────────────────────────────────────────────
    run_id: str
    landing_page_url: str
    ad_image_url: Optional[str] = None
    ad_image_base64: Optional[str] = None  # base64-encoded bytes

    # ── Agent outputs (populated progressively) ───────────────────────────────
    ad_context: Optional[AdContext] = None
    page_snapshot: Optional[PageSnapshot] = None
    semantic_map: Optional[SemanticMap] = None
    cro_findings: Optional[CROFindings] = None
    patch_spec: Optional[PatchSpec] = None
    modified_html: Optional[str] = None
    modified_screenshot_path: Optional[str] = None
    qa_report: Optional[QAReport] = None
    explanations: List[ExplanationItem] = Field(default_factory=list)

    # ── Control flow ──────────────────────────────────────────────────────────
    retry_count: int = Field(default=0, description="Number of QA→CodeModifier retry cycles")
    max_retries: int = Field(default=2)
    current_stage: Optional[str] = None
    error: Optional[str] = None

    # ── Scores ────────────────────────────────────────────────────────────────
    cro_score_before: Optional[float] = None
    cro_score_after: Optional[float] = None
    predicted_lift_range: Optional[str] = None  # e.g. "5-10%"


class RunConfig(BaseModel):
    """User-submitted configuration for a single pipeline run."""

    landing_page_url: str
    ad_image_url: Optional[str] = None
    ad_image_file: Optional[str] = None  # base64 encoded
    num_variants: int = Field(default=1, ge=1, le=5)


class RunResult(BaseModel):
    """Final output bundle returned to the frontend after pipeline completion."""

    run_id: str
    status: Literal["completed", "completed_with_warnings", "failed"]

    # ── Preview URLs ──────────────────────────────────────────────────────────
    original_html_url: str
    modified_html_url: str
    original_screenshot_url: str
    modified_screenshot_url: str

    # ── Analysis ──────────────────────────────────────────────────────────────
    ad_context: AdContext
    cro_findings: CROFindings
    patch_spec: PatchSpec
    qa_report: QAReport
    explanations: List[ExplanationItem]

    # ── Scores ────────────────────────────────────────────────────────────────
    cro_score_before: float
    cro_score_after: float
    predicted_lift_range: str
