"""FieldExtractor – transforms raw Collector rows into styled cell dicts.

This is the heart of the Dashboard processing step.  For each row returned
by the Collector, the FieldExtractor calls every ``@dashboardColumn``-annotated
method on the Dashboard instance, catches per-column exceptions (marking them
with a red CSS class), and assembles the final ``DashboardDataResponse``.
"""
from __future__ import annotations

import logging
from typing import Any

from src.models.dashboard import TableDashboard

logger = logging.getLogger(__name__)

# Shape returned by process()
DashboardResult = dict[str, Any]


class FieldExtractor:
    """Orchestrates data extraction and styling for a single dashboard.

    Usage::

        extractor = FieldExtractor()
        result = extractor.process(my_dashboard_instance)
        # result is a DashboardResult ready to serialize to JSON
    """

    def process(self, dashboard: TableDashboard) -> DashboardResult:
        """Run the full extraction pipeline for *dashboard*.

        Returns
        -------
        DashboardResult
            A dict with keys:
            - ``columns``: list of column names (strings).
            - ``rows``: list of row dicts, each mapping column name → ``CellResult``.
            - ``error``: None, or an error string if the Collector failed.
            - ``scrape_interval_seconds``: int from the Collector.
        """
        columns_meta = dashboard.get_columns()
        column_names = [name for name, _ in columns_meta]

        # ── 1. Collect raw rows ───────────────────────────────────────────────
        try:
            collector = dashboard.getCollector()
            raw_rows = collector.safe_collect()
        except Exception as exc:
            logger.error(
                "FieldExtractor: collector error for %s: %s",
                type(dashboard).__name__, exc, exc_info=True,
            )
            return {
                "columns": column_names,
                "rows": [],
                "error": str(exc),
                "scrape_interval_seconds": self._scrape_interval(dashboard),
            }

        # ── 2. Extract and style each cell ────────────────────────────────────
        rows: list[dict[str, Any]] = []
        for raw_row in raw_rows:
            row_result: dict[str, Any] = {}
            for col_name, extractor_fn in columns_meta:
                try:
                    cell = extractor_fn(raw_row)
                    row_result[col_name] = cell
                except Exception as exc:
                    logger.error(
                        "FieldExtractor: column '%s' error: %s",
                        col_name, exc, exc_info=True,
                    )
                    row_result[col_name] = {
                        "value": f"Error: {exc}",
                        "style": "cell-error",
                    }
            rows.append(row_result)

        return {
            "columns": column_names,
            "rows": rows,
            "error": None,
            "scrape_interval_seconds": self._scrape_interval(dashboard),
        }

    @staticmethod
    def _scrape_interval(dashboard: TableDashboard) -> int:
        """Best-effort: read scrape_interval from the collector, fallback to 30."""
        try:
            return dashboard.getCollector().scrape_interval
        except Exception:
            return 30
