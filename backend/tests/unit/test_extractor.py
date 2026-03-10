"""Unit tests: FieldExtractor column extraction and CSS mapping (TDD)."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from src.models.collector import Collector
from src.models.dashboard import CellResult, TableDashboard, dashboardColumn
from src.engine.extractor import FieldExtractor


# ── Fixtures ──────────────────────────────────────────────────────────────────

class SimpleCollector(Collector):
    def collect(self) -> Iterable[dict[str, Any]]:
        return [
            {"name": "pod-a", "status": "Running"},
            {"name": "pod-b", "status": "CrashLoopBackOff"},
        ]


class SimpleDashboard(TableDashboard):
    def getCollector(self) -> Collector:
        return SimpleCollector()

    @dashboardColumn("Pod Name")
    def pod_name(self, row: dict[str, Any]) -> CellResult:
        return {"value": row["name"], "style": ""}

    @dashboardColumn("Status")
    def status(self, row: dict[str, Any]) -> CellResult:
        style = "text-green-500" if row["status"] == "Running" else "text-red-400"
        return {"value": row["status"], "style": style}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestFieldExtractor:
    @pytest.fixture
    def extractor(self) -> FieldExtractor:
        return FieldExtractor()

    def test_columns_extracted_correctly(self, extractor: FieldExtractor) -> None:
        dashboard = SimpleDashboard()
        result = extractor.process(dashboard)
        assert result["columns"] == ["Pod Name", "Status"]

    def test_row_values_extracted(self, extractor: FieldExtractor) -> None:
        dashboard = SimpleDashboard()
        result = extractor.process(dashboard)
        assert result["rows"][0]["Pod Name"]["value"] == "pod-a"
        assert result["rows"][1]["Pod Name"]["value"] == "pod-b"

    def test_css_style_applied_correctly(self, extractor: FieldExtractor) -> None:
        dashboard = SimpleDashboard()
        result = extractor.process(dashboard)
        assert result["rows"][0]["Status"]["style"] == "text-green-500"
        assert result["rows"][1]["Status"]["style"] == "text-red-400"

    def test_error_in_column_marks_cell_red(self, extractor: FieldExtractor) -> None:
        class BrokenDashboard(TableDashboard):
            def getCollector(self) -> Collector:
                return SimpleCollector()

            @dashboardColumn("Broken")
            def broken(self, row: dict[str, Any]) -> CellResult:
                raise ValueError("This column is broken")

        dashboard = BrokenDashboard()
        result = extractor.process(dashboard)
        # Should not raise; broken column gets error style
        assert result["rows"][0]["Broken"]["style"] == "cell-error"
        assert "broken" in result["rows"][0]["Broken"]["value"].lower()

    def test_collector_error_propagates_to_result(self, extractor: FieldExtractor) -> None:
        class ErrorCollector(Collector):
            def collect(self) -> Iterable[dict[str, Any]]:
                raise RuntimeError("Collector failed!")

        class ErrorDashboard(TableDashboard):
            def getCollector(self) -> Collector:
                return ErrorCollector()

            @dashboardColumn("Col")
            def col(self, row: dict[str, Any]) -> CellResult:
                return {"value": row.get("x", ""), "style": ""}

        dashboard = ErrorDashboard()
        result = extractor.process(dashboard)
        assert result["error"] is not None
        assert "Collector failed" in result["error"]
        assert result["rows"] == []
