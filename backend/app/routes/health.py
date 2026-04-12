"""Health check route."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health() -> JSONResponse:
    """Basic health check — returns 200 if the server is up."""
    return JSONResponse({"status": "ok"})
