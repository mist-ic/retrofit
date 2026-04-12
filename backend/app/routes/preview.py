"""Preview routes — serve original and modified HTML for iframe preview."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.storage.artifacts import load_html

router = APIRouter()


@router.get("/preview/{run_id}/original", response_class=HTMLResponse)
async def preview_original(run_id: str) -> HTMLResponse:
    """Serve the original scraped page HTML for iframe preview."""
    html = await load_html(run_id, "original")
    return HTMLResponse(content=html)


@router.get("/preview/{run_id}/variant", response_class=HTMLResponse)
async def preview_variant(run_id: str) -> HTMLResponse:
    """Serve the modified (personalized) page HTML for iframe preview."""
    html = await load_html(run_id, "variant")
    return HTMLResponse(content=html)
