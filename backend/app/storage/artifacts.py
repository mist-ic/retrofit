"""Artifact storage — saves/loads HTML, screenshots, and run configs (local or GCS)."""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from app.config import settings

# In-memory store for run configs (replace with Redis/Firestore for production)
_run_configs: dict[str, dict] = {}

# Local artifact root (used when use_local_storage=True)
_LOCAL_ROOT = Path(tempfile.gettempdir()) / "retrofit_artifacts"


# ── Run config ────────────────────────────────────────────────────────────────

async def store_run_config(run_id: str, config: dict) -> None:
    """Persist run configuration so the stream endpoint can retrieve it."""
    _run_configs[run_id] = config


async def get_run_config(run_id: str) -> dict:
    """Retrieve a run's configuration by ID."""
    if run_id not in _run_configs:
        raise KeyError(f"Run {run_id} not found")
    return _run_configs[run_id]


# ── Screenshot ────────────────────────────────────────────────────────────────

async def save_screenshot(run_id: str, data: bytes, variant: str) -> str:
    """
    Save a screenshot PNG. Returns the local path or GCS URI.
    variant: 'original' | 'modified'
    """
    filename = f"{variant}_screenshot.png"
    return await _write_artifact(run_id, filename, data, mode="wb")


async def load_screenshot(run_id: str, variant: str) -> Optional[bytes]:
    """Load a screenshot by run ID and variant."""
    filename = f"{variant}_screenshot.png"
    return await _read_artifact(run_id, filename, mode="rb")


# ── HTML ──────────────────────────────────────────────────────────────────────

async def save_html(run_id: str, html: str, variant: str) -> str:
    """Save an HTML string. variant: 'original' | 'variant'"""
    filename = f"{variant}.html"
    return await _write_artifact(run_id, filename, html.encode("utf-8"), mode="wb")


async def load_html(run_id: str, variant: str) -> str:
    """Load an HTML string by run ID and variant."""
    filename = f"{variant}.html"
    data = await _read_artifact(run_id, filename, mode="rb")
    return data.decode("utf-8") if data else "<html><body><p>Not found</p></body></html>"


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _write_artifact(run_id: str, filename: str, data: bytes, mode: str) -> str:
    if settings.use_local_storage or not settings.gcs_bucket:
        return _write_local(run_id, filename, data)
    return await _write_gcs(run_id, filename, data)


async def _read_artifact(run_id: str, filename: str, mode: str) -> Optional[bytes]:
    if settings.use_local_storage or not settings.gcs_bucket:
        return _read_local(run_id, filename)
    return await _read_gcs(run_id, filename)


def _write_local(run_id: str, filename: str, data: bytes) -> str:
    run_dir = _LOCAL_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / filename
    path.write_bytes(data)
    return str(path)


def _read_local(run_id: str, filename: str) -> Optional[bytes]:
    path = _LOCAL_ROOT / run_id / filename
    if path.exists():
        return path.read_bytes()
    return None


async def _write_gcs(run_id: str, filename: str, data: bytes) -> str:
    from google.cloud import storage

    client = storage.Client(project=settings.google_cloud_project)
    bucket = client.bucket(settings.gcs_bucket)
    blob_path = f"runs/{run_id}/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(data)
    return f"gs://{settings.gcs_bucket}/{blob_path}"


async def _read_gcs(run_id: str, filename: str) -> Optional[bytes]:
    from google.cloud import storage

    client = storage.Client(project=settings.google_cloud_project)
    bucket = client.bucket(settings.gcs_bucket)
    blob_path = f"runs/{run_id}/{filename}"
    blob = bucket.blob(blob_path)
    if blob.exists():
        return blob.download_as_bytes()
    return None
