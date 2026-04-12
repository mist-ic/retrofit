"""Models package — all Pydantic data contracts for the pipeline."""

from .ad_context import AdContext
from .cro_findings import ChangeCandidate, CROFindings, CROIssue, CriterionScore
from .patch_spec import (
    AddClassOp,
    InsertAfterOp,
    InsertBeforeOp,
    PatchOperation,
    PatchSpec,
    RemoveClassOp,
    ReplaceAttributeOp,
    ReplaceStyleOp,
    ReplaceTextOp,
)
from .pipeline import ExplanationItem, PageSnapshot, PipelineState, RunConfig, RunResult
from .qa_report import HallucinationFlag, QAReport, StructuralIssue
from .semantic_map import PageElement, SemanticMap
from .shared import BoundingBox, ColorSwatch

__all__ = [
    "AdContext",
    "ColorSwatch",
    "BoundingBox",
    "PageElement",
    "SemanticMap",
    "CriterionScore",
    "CROIssue",
    "ChangeCandidate",
    "CROFindings",
    "ReplaceTextOp",
    "ReplaceAttributeOp",
    "AddClassOp",
    "RemoveClassOp",
    "InsertBeforeOp",
    "InsertAfterOp",
    "ReplaceStyleOp",
    "PatchOperation",
    "PatchSpec",
    "StructuralIssue",
    "HallucinationFlag",
    "QAReport",
    "PageSnapshot",
    "ExplanationItem",
    "PipelineState",
    "RunConfig",
    "RunResult",
]
