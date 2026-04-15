"""LangGraph graph state TypedDict — shared across all pipeline nodes."""

from typing import Annotated, List, Optional
from typing_extensions import TypedDict

# Reducer for scalar fields written by parallel nodes (last-writer-wins).
# ad_analyzer and page_scraper run concurrently and both write `current_stage`
# and `error`; without a reducer LangGraph raises INVALID_CONCURRENT_GRAPH_UPDATE.
_last = lambda a, b: b  # noqa: E731


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
    # NOTE: Annotated[..., _last] required for fields written by parallel nodes.
    retry_count: int
    max_retries: int
    current_stage: Annotated[Optional[str], _last]
    error: Annotated[Optional[str], _last]

    # ── Scores ────────────────────────────────────────────────────────────────
    cro_score_before: Optional[float]
    cro_score_after: Optional[float]
    predicted_lift_range: Optional[str]
