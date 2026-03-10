"""FastAPI route definitions for Chart-Monitor API v1."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from src.engine.pipeline import list_dashboards, run_dashboard
from src.storage.git_sync import is_gitops_enabled, perform_sync

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Response models ───────────────────────────────────────────────────────────

class DashboardMeta(BaseModel):
    id: str
    name: str
    scrape_interval_seconds: int
    dashboard_name: str | None = None


class CellResult(BaseModel):
    value: Any
    display: str | None = None
    style: str


class DashboardDataResponse(BaseModel):
    dashboard_id: str
    dashboard_name: str | None = None
    columns: list[str]
    rows: list[dict[str, CellResult]]
    scrape_interval_seconds: int
    error: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/dashboards", response_model=list[DashboardMeta])
async def get_dashboards() -> list[dict[str, Any]]:
    """List all registered dashboards."""
    return list_dashboards()


@router.get("/dashboards/{dashboard_id}/data", response_model=DashboardDataResponse)
async def get_dashboard_data(dashboard_id: str) -> dict[str, Any]:
    """Execute the pipeline for *dashboard_id* and return styled data."""
    result = run_dashboard(dashboard_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dashboard '{dashboard_id}' not found.",
        )
    return result


# ── GitOps Routes ─────────────────────────────────────────────────────────────

class GitOpsStatusResponse(BaseModel):
    enabled: bool


class SyncResponse(BaseModel):
    success: bool
    message: str
    details: str = ""


@router.get("/git/status", response_model=GitOpsStatusResponse)
async def get_gitops_status() -> dict[str, bool]:
    """Return whether GitOps is enabled (all env vars present)."""
    return {"enabled": is_gitops_enabled()}


@router.post("/git/sync", response_model=SyncResponse)
async def trigger_sync(
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    """Trigger a manual GitOps sync.

    Requires a ``Authorization: Bearer <SYNC_SECRET>`` header.
    """
    import os
    sync_secret = os.environ.get("SYNC_SECRET", "")
    if not sync_secret:
        raise HTTPException(status_code=503, detail="GitOps is not configured on the server.")

    expected = f"Bearer {sync_secret}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing SYNC_SECRET.")

    result = perform_sync()
    if not result.success:
        return {"success": False, "message": result.message, "details": result.details}

    return {"success": True, "message": result.message, "details": result.details}
