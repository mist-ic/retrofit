"""LangGraph graph state TypedDict — shared across all pipeline nodes."""

from typing import List, Optional
from typing_extensions import TypedDict


class GraphState(TypedDict, total=False):
    """
    Pipeline state flowing through all 6 LangGraph nodes.

    Uses TypedDict (not Pydantic) so LangGraph can checkpoint and diff cleanly.
    All nested models are stored as plain dicts; nodes deserialize them on demand.
    total=False means all fields are optional at graph construction time.
    """
    # ── Required inputs ───────────────────────────────────────────────────────
    run_id: str
    landing_page_url: str
    ad_image_url: Optional[str]
    ad_image_base64: Optional[str]

    # ── Agent outputs (populated progressively) ───────────────────────────────
    ad_context: Optional[dict]        # AdContext.model_dump()
    page_snapshot: Optional[dict]     # PageSnapshot.model_dump()
    semantic_map: Optional[dict]      # SemanticMap.model_dump()
    cro_findings: Optional[dict]      # CROFindings.model_dump()
    patch_spec: Optional[dict]        # PatchSpec.model_dump()
    modified_html: Optional[str]
    modified_screenshot_path: Optional[str]
    qa_report: Optional[dict]         # QAReport.model_dump()
    explanations: List[dict]          # List[ExplanationItem.model_dump()]

    # ── Control flow ──────────────────────────────────────────────────────────
    retry_count: int
    max_retries: int
    current_stage: Optional[str]
    error: Optional[str]

    # ── Scores ────────────────────────────────────────────────────────────────
    cro_score_before: Optional[float]
    cro_score_after: Optional[float]
    predicted_lift_range: Optional[str]
