"""Tests for all Pydantic data models — serialization and validation."""

import pytest
from app.models import (
    AdContext,
    BoundingBox,
    ChangeCandidate,
    CROFindings,
    CROIssue,
    CriterionScore,
    ExplanationItem,
    HallucinationFlag,
    PageElement,
    PageSnapshot,
    PatchSpec,
    PipelineState,
    QAReport,
    ReplaceTextOp,
    RunResult,
    SemanticMap,
    StructuralIssue,
)


def test_ad_context_minimal():
    ctx = AdContext(headline="Summer Sale", offer_type="percent_discount")
    assert ctx.headline == "Summer Sale"
    assert ctx.discount_percent is None
    data = ctx.model_dump()
    assert data["offer_type"] == "percent_discount"


def test_ad_context_full():
    ctx = AdContext(
        headline="40% OFF All Skincare",
        offer_type="percent_discount",
        discount_percent=40.0,
        discount_code="SUMMER40",
        tone="bold",
        intent_stage="purchase",
        dominant_colors=[{"hex": "#FF3366", "h": 345, "s": 0.85, "l": 0.6}],
    )
    assert ctx.discount_percent == 40.0
    assert ctx.dominant_colors[0].hex == "#FF3366"


def test_replace_text_op():
    op = ReplaceTextOp(op="replaceText", selector="h1.hero", new_text="New Headline")
    assert op.op == "replaceText"
    assert op.selector == "h1.hero"


def test_patch_spec_discriminator():
    spec = PatchSpec(
        variant_id="test-v1",
        description="test",
        operations=[
            {"op": "replaceText", "selector": "h1", "new_text": "Hello"},
            {"op": "addClass", "selector": "button.cta", "class_name": "btn-urgent"},
        ],
    )
    assert len(spec.operations) == 2
    assert spec.operations[0].op == "replaceText"
    assert spec.operations[1].op == "addClass"


def test_semantic_map_shopify_fields():
    sm = SemanticMap(url="https://store.myshopify.com", is_shopify=True, shopify_theme="Dawn")
    assert sm.is_shopify is True
    assert sm.shopify_theme == "Dawn"


def test_qa_report_pass():
    report = QAReport(
        variant_id="v1",
        passed=True,
        is_valid_html=True,
        key_elements_present=True,
        grounded_change_count=3,
    )
    assert report.passed is True
    assert report.hallucination_flags == []


def test_pipeline_state_defaults():
    state = PipelineState(run_id="abc123", landing_page_url="https://example.com")
    assert state.retry_count == 0
    assert state.max_retries == 2
    assert state.explanations == []


def test_cro_findings_serialization():
    findings = CROFindings(
        overall_score=65.5,
        criteria=[
            CriterionScore(
                criterion_id="message_match",
                label="Message Match",
                score=45.0,
                weight=0.25,
                rationale="Hero headline doesn't match ad",
            )
        ],
        top_issues=[
            CROIssue(
                issue_id="i1",
                severity="critical",
                criterion_id="message_match",
                description="No message match",
                impact="High bounce rate",
            )
        ],
        change_candidates=[
            ChangeCandidate(
                change_id="c1",
                priority=1,
                target_selector="h1",
                change_type="copy",
                cro_principles=["message_match"],
                proposed_direction="Restate the 40% OFF offer",
                estimated_impact="high",
            )
        ],
        summary="Page ignores the ad's offer",
    )
    assert findings.overall_score == 65.5
    assert findings.criteria[0].criterion_id == "message_match"
    dumped = findings.model_dump_json()
    assert "message_match" in dumped
