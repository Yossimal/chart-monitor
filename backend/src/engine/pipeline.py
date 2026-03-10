"""Pipeline – thin orchestration layer that connects Store → FieldExtractor.

The pipeline is the single entry point that the API routes call.  It
fetches the dashboard class from the Store, instantiates it, delegates to
the FieldExtractor, and returns a result that maps directly to the API contract.
"""
from __future__ import annotations

import logging
from typing import Any

from src.engine.extractor import FieldExtractor
from src.storage.store import store

logger = logging.getLogger(__name__)
_extractor = FieldExtractor()


def run_dashboard(dashboard_id: str) -> dict[str, Any] | None:
    """Execute the full pipeline for *dashboard_id*.

    Returns
    -------
    dict | None
        A DashboardResult ready to serialize, or ``None`` when the dashboard
        ID is not registered in the store.
    """
    dashboards = store.get_dashboards()
    dashboard_cls = dashboards.get(dashboard_id)
    if dashboard_cls is None:
        logger.warning("Dashboard '%s' not found in store.", dashboard_id)
        return None

    try:
        dashboard = dashboard_cls()
    except Exception as exc:
        logger.error(
            "Failed to instantiate '%s': %s", dashboard_id, exc, exc_info=True
        )
        return {
            "columns": [],
            "rows": [],
            "error": f"Dashboard instantiation error: {exc}",
            "scrape_interval_seconds": 30,
        }

    result = _extractor.process(dashboard)
    result["dashboard_id"] = dashboard_id
    return result


def list_dashboards() -> list[dict[str, Any]]:
    """Return metadata for all registered dashboards."""
    out: list[dict[str, Any]] = []
    for dashboard_id, dashboard_cls in store.get_dashboards().items():
        try:
            dashboard = dashboard_cls()
            collector = dashboard.getCollector()
            out.append(
                {
                    "id": dashboard_id,
                    "name": dashboard_id,
                    "scrape_interval_seconds": collector.scrape_interval,
                }
            )
        except Exception as exc:
            logger.warning("Cannot introspect dashboard '%s': %s", dashboard_id, exc)
            out.append({"id": dashboard_id, "name": dashboard_id, "scrape_interval_seconds": 30})
    return out
