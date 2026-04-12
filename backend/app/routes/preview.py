"""Preview routes — serve original and modified HTML + screenshots for iframe preview."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response

from app.storage.artifacts import load_html, load_screenshot

router = APIRouter()


@router.get("/preview/{run_id}/original", response_class=HTMLResponse)
async def preview_original(run_id: str) -> HTMLResponse:
    """Serve the original scraped page HTML (with base tag) for iframe preview."""
    html = await load_html(run_id, "original")
    return HTMLResponse(content=html)


@router.get("/preview/{run_id}/variant", response_class=HTMLResponse)
async def preview_variant(run_id: str) -> HTMLResponse:
    """Serve the modified (personalized) page HTML for iframe preview."""
    html = await load_html(run_id, "variant")
    return HTMLResponse(content=html)


@router.get("/screenshots/{run_id}/{variant}")
async def serve_screenshot(run_id: str, variant: str) -> Response:
    """
    Serve a run screenshot as a PNG image.
    variant: 'original' | 'modified'
    Used by BeforeAfterSlider component for pixel-diff comparison.
    """
    data = await load_screenshot(run_id, variant)
    if not data:
        raise HTTPException(status_code=404, detail=f"Screenshot not found: {run_id}/{variant}")
    return Response(content=data, media_type="image/png")
