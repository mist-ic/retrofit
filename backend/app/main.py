"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health, preview, runs

app = FastAPI(
    title="RetroFit API",
    description="AI-powered ad→landing-page personalization pipeline",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(runs.router, prefix="/api", tags=["runs"])
app.include_router(preview.router, prefix="/api", tags=["preview"])
