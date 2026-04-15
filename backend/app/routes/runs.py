"""Run routes — pipeline lifecycle: create, stream (SSE), and fetch results."""

import base64
import json
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from app.agents.graph import pipeline_graph
from app.models.pipeline import ExplanationItem, PageSnapshot, RunResult
from app.models.ad_context import AdContext
from app.models.cro_findings import CROFindings
from app.models.patch_spec import PatchSpec
from app.models.qa_report import QAReport
from app.storage.artifacts import get_run_config, store_run_config

router = APIRouter()


# ── POST /api/runs ─────────────────────────────────────────────────────────────

@router.post("/runs")
async def create_run(
    landing_page_url: str = Form(...),
    ad_image: Optional[UploadFile] = File(None),
    ad_image_url: Optional[str] = Form(None),
):
    """
    Start a new pipeline run. Returns run_id immediately.
    The frontend connects to /api/runs/{run_id}/stream for SSE events.
    """
    run_id = str(uuid.uuid4())

    ad_image_base64 = None
    if ad_image and ad_image.filename:
        content = await ad_image.read()
        ad_image_base64 = base64.b64encode(content).decode()

    await store_run_config(run_id, {
        "landing_page_url": landing_page_url,
        "ad_image_url": ad_image_url,
        "ad_image_base64": ad_image_base64,
    })

    return {"run_id": run_id, "status": "created"}


# ── GET /api/runs/{run_id}/stream ─────────────────────────────────────────────

@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str):
    """
    Stream pipeline execution events via Server-Sent Events (SSE).

    LangGraph 1.x streaming:
    - stream_mode=["updates", "custom"] yields tuples: (mode, data)
    - "custom" mode: data emitted by writer() inside each node
    - "updates" mode: {node_name: {output_keys}} after each node completes
    """
    async def event_generator():
        try:
            config = await get_run_config(run_id)

            initial_state = {
                "run_id": run_id,
                "landing_page_url": config["landing_page_url"],
                "ad_image_url": config.get("ad_image_url"),
                "ad_image_base64": config.get("ad_image_base64"),
                "retry_count": 0,
                "max_retries": 2,
                "explanations": [],
            }

            thread_config = {"configurable": {"thread_id": run_id}}

            print(f"[runs] 🚀 Starting pipeline for run {run_id[:8]}...")
            print(f"[runs]    URL: {config['landing_page_url']}")
            print(f"[runs]    Has image: {bool(config.get('ad_image_base64') or config.get('ad_image_url'))}")

            # In LangGraph 1.x, astream with multiple modes yields (mode, data) tuples
            async for event_tuple in pipeline_graph.astream(
                initial_state,
                stream_mode=["updates", "custom"],
                config=thread_config,
            ):
                # Unpack mode + data — use distinct variable names to avoid shadowing
                if isinstance(event_tuple, tuple):
                    event_mode, event_data = event_tuple
                else:
                    event_mode, event_data = "updates", event_tuple

                if event_mode == "custom":
                    # Custom events emitted via writer() inside each node
                    evt = event_data.get("event", "custom")
                    stage = event_data.get("stage", "?")
                    print(f"[runs]   📡 custom → {evt} [{stage}]: {event_data.get('message', '')[:60]}")
                    yield _sse(evt, event_data)

                elif event_mode == "updates":
                    # Node completed — emit node_complete with updated keys
                    for node_name, node_output in event_data.items():
                        print(f"[runs]   ✓ node_complete: {node_name} → {list(node_output.keys())}")
                        yield _sse("node_complete", {
                            "node": node_name,
                            "keys_updated": list(node_output.keys()),
                        })

            # Pipeline finished — build and emit final result
            final_state_snapshot = pipeline_graph.get_state(config=thread_config)
            try:
                result = _build_run_result(run_id, final_state_snapshot.values)
                yield _sse("run_complete", result.model_dump())
            except Exception as result_err:
                import traceback
                print(f"[runs] Failed to build run result for {run_id}:\n{traceback.format_exc()}")
                yield _sse("run_error", {"error": f"Result serialization failed: {result_err}", "run_id": run_id})

        except Exception as e:
            import traceback
            print(f"[runs] Pipeline error for run {run_id}:\n{traceback.format_exc()}")
            yield _sse("run_error", {"error": str(e), "run_id": run_id})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── GET /api/runs/{run_id}/result ─────────────────────────────────────────────

@router.get("/runs/{run_id}/result")
async def get_result(run_id: str):
    """Get the final result of a completed run (polling fallback for SSE)."""
    thread_config = {"configurable": {"thread_id": run_id}}
    final_state_snapshot = pipeline_graph.get_state(config=thread_config)
    result = _build_run_result(run_id, final_state_snapshot.values)
    return result.model_dump()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _build_run_result(run_id: str, state: dict) -> RunResult:
    """Construct a RunResult from the final pipeline state dict."""
    qa_report_dict = state.get("qa_report") or {}
    passed = qa_report_dict.get("passed", False) if qa_report_dict else False

    if state.get("modified_html"):
        status = "completed" if passed else "completed_with_warnings"
    else:
        status = "failed"

    base = "/api"

    return RunResult(
        run_id=run_id,
        status=status,
        original_html_url=f"{base}/preview/{run_id}/original",
        modified_html_url=f"{base}/preview/{run_id}/variant",
        original_screenshot_url=f"{base}/screenshots/{run_id}/original",
        modified_screenshot_url=f"{base}/screenshots/{run_id}/modified",
        ad_context=AdContext.model_validate(state["ad_context"]) if state.get("ad_context") else _empty_ad_context(),
        cro_findings=CROFindings.model_validate(state["cro_findings"]) if state.get("cro_findings") else _empty_cro_findings(),
        patch_spec=PatchSpec.model_validate(state["patch_spec"]) if state.get("patch_spec") else _empty_patch_spec(),
        qa_report=QAReport.model_validate(state["qa_report"]) if state.get("qa_report") else _empty_qa_report(),
        explanations=[ExplanationItem.model_validate(e) for e in state.get("explanations", [])],
        cro_score_before=state.get("cro_score_before") or 0.0,
        cro_score_after=state.get("cro_score_after") or 0.0,
        predicted_lift_range=state.get("predicted_lift_range") or "0-2%",
    )


def _empty_ad_context() -> AdContext:
    return AdContext(headline="(unavailable)", offer_type="none")


def _empty_cro_findings() -> CROFindings:
    return CROFindings(
        overall_score=0,
        criteria=[],
        top_issues=[],
        change_candidates=[],
        summary="Pipeline did not complete",
    )


def _empty_patch_spec() -> PatchSpec:
    return PatchSpec(variant_id="empty", description="No changes", operations=[])


def _empty_qa_report() -> QAReport:
    return QAReport(
        variant_id="empty",
        passed=False,
        is_valid_html=False,
        key_elements_present=False,
        grounded_change_count=0,
    )
