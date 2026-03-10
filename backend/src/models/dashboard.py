"""Base ``TableDashboard`` class and the ``@dashboardColumn`` annotation.

Users extend this class to define how raw collector rows are transformed
into styled table cells for the UI.

Example::

    class PodDashboard(TableDashboard):
        def getCollector(self) -> Collector:
            return PodCollector()

        @dashboardColumn("Pod Name")
        def pod_name(self, row: dict) -> CellResult:
            return {"value": row["name"], "style": ""}

        @dashboardColumn("Status")
        def status(self, row: dict) -> CellResult:
            style = "text-green-500" if row["status"] == "Running" else "text-red-400"
            return {"value": row["status"], "style": style}
"""
from __future__ import annotations

import functools
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, TypedDict

from src.models.collector import Collector

logger = logging.getLogger(__name__)


class CellResult(TypedDict):
    """Shape returned by each @dashboardColumn method."""
    value: str
    style: str


# ─────────────────────────────────────────────────────────────────────────────
# @dashboardColumn decorator
# ─────────────────────────────────────────────────────────────────────────────

def dashboardColumn(column_name: str) -> Callable:
    """Mark a method as a dashboard table column extractor.

    The decorated method receives one ``row`` argument (a plain dict from the
    Collector) and must return a :class:`CellResult`.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self: "TableDashboard", row: dict[str, Any]) -> CellResult:
            return fn(self, row)
        wrapper._is_dashboard_column = True           # type: ignore[attr-defined]
        wrapper._column_name = column_name            # type: ignore[attr-defined]
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# TableDashboard base class
# ─────────────────────────────────────────────────────────────────────────────

class TableDashboard(ABC):
    """Abstract base class for all Chart-Monitor table dashboards.

    Subclasses must implement ``getCollector`` and annotate at least one
    method with ``@dashboardColumn``.
    """

    @abstractmethod
    def getCollector(self) -> Collector:
        """Return the configured Collector instance for this dashboard."""

    def get_columns(self) -> list[tuple[str, Callable]]:
        """Return ordered list of (column_name, extractor_method) tuples."""
        columns: list[tuple[str, Callable]] = []
        for _name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, "_is_dashboard_column", False):
                columns.append((method._column_name, method))
        return columns
