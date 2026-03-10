"""FastAPI route definitions for Chart-Monitor API v1."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.engine.pipeline import list_dashboards, run_dashboard

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Response models ───────────────────────────────────────────────────────────

class DashboardMeta(BaseModel):
    id: str
    name: str
    scrape_interval_seconds: int


class CellResult(BaseModel):
    value: str
    style: str


class DashboardDataResponse(BaseModel):
    dashboard_id: str
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
