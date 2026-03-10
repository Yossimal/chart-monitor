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
    
    dashboard_name_val = None
    set_name_fn = getattr(dashboard, "set_name", None)
    if set_name_fn and callable(set_name_fn):
        try:
            dashboard_name_val = str(set_name_fn())
            if len(dashboard_name_val) > 150:
                logger.warning("Dashboard '%s' set_name exceeds 150 characters.", dashboard_id)
                dashboard_name_val = "Error: set_name exceeds 150 characters"
        except Exception as exc:
            logger.warning("Error evaluating set_name for '%s': %s", dashboard_id, exc)
            
    result["dashboard_name"] = dashboard_name_val

    return result


def list_dashboards() -> list[dict[str, Any]]:
    """Return metadata for all registered dashboards."""
    out: list[dict[str, Any]] = []
    for dashboard_id, dashboard_cls in store.get_dashboards().items():
        try:
            dashboard = dashboard_cls()
            collector = dashboard.getCollector()
            
            dashboard_name_val = None
            set_name_fn = getattr(dashboard, "set_name", None)
            
            if set_name_fn and callable(set_name_fn):
                try:
                    dashboard_name_val = str(set_name_fn())
                    if len(dashboard_name_val) > 150:
                        logger.warning("Dashboard '%s' set_name exceeds 150 characters.", dashboard_id)
                        dashboard_name_val = "Error: set_name exceeds 150 characters"
                except Exception as exc:
                    logger.warning("Error evaluating set_name for '%s': %s", dashboard_id, exc)

            out.append(
                {
                    "id": dashboard_id,
                    "name": dashboard_id,
                    "scrape_interval_seconds": collector.scrape_interval,
                    "dashboard_name": dashboard_name_val
                }
            )
        except Exception as exc:
            logger.warning("Cannot introspect dashboard '%s': %s", dashboard_id, exc)
            out.append({"id": dashboard_id, "name": dashboard_id, "scrape_interval_seconds": 30, "dashboard_name": None})
    return out
