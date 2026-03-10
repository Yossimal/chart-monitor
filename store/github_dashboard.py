"""
Chart-Monitor Quickstart – GitHub Pull Requests Dashboard
CSS styles are raw inline CSS strings (no Tailwind).
"""
from __future__ import annotations

from typing import Any

from src.models.collector import Collector
from src.models.dashboard import CellResult, TableDashboard, dashboardColumn
from store.github_prs import GitHubPRCollector


class GitHubPRDashboard(TableDashboard):
    """Renders open GitHub Pull Requests as a monitoring table."""

    def getCollector(self) -> Collector:
        collector = GitHubPRCollector()
        collector.max_data = 25
        collector.scrape_interval = 120
        return collector

    @dashboardColumn("PR Title")
    def title(self, row: dict[str, Any]) -> CellResult:
        return {"value": row.get("title", "—"), "style": "font-weight: 500;"}

    @dashboardColumn("Author")
    def author(self, row: dict[str, Any]) -> CellResult:
        return {"value": row.get("user", {}).get("login", "—"), "style": "color: #818cf8;"}

    @dashboardColumn("State")
    def state(self, row: dict[str, Any]) -> CellResult:
        state = row.get("state", "closed")
        style = "color: #10b981; font-weight: 700;" if state == "open" else "color: #ef4444;"
        return {"value": state.upper(), "style": style}

    @dashboardColumn("PR #")
    def number(self, row: dict[str, Any]) -> CellResult:
        num = row.get("number", "")
        return {"value": f"#{num}", "style": "color: #71717a; font-family: monospace;"}
