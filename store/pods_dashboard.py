"""Kubernetes Pods Dashboard.

Renders a styled table of all pods across all namespaces.
CSS styles are raw inline CSS strings (no Tailwind).
"""
from __future__ import annotations

from typing import Any

from src.models.collector import Collector
from src.models.dashboard import CellResult, TableDashboard, dashboardColumn
from store.pods_collector import PodsCollector


class PodsDashboard(TableDashboard):
    """All-namespaces pod monitoring dashboard."""

    def getCollector(self) -> Collector:
        return PodsCollector()

    @dashboardColumn("Namespace")
    def namespace(self, row: dict[str, Any]) -> CellResult:
        ns = row.get("metadata", {}).get("namespace", "—")
        return {"value": ns, "style": "color: #818cf8; font-family: monospace;"}

    @dashboardColumn("Pod Name")
    def pod_name(self, row: dict[str, Any]) -> CellResult:
        name = row.get("metadata", {}).get("name", "—")
        return {"value": name, "style": "font-weight: 500; font-family: monospace;"}

    @dashboardColumn("Status")
    def status(self, row: dict[str, Any]) -> CellResult:
        phase = row.get("status", {}).get("phase", "Unknown")
        style_map = {
            "Running":   "color: #10b981; font-weight: 600;",
            "Pending":   "color: #f59e0b; font-weight: 600;",
            "Succeeded": "color: #3b82f6;",
        }
        style = style_map.get(phase, "color: #ef4444; font-weight: 600;")
        return {"value": phase, "style": style}

    @dashboardColumn("Ready")
    def ready(self, row: dict[str, Any]) -> CellResult:
        containers = row.get("status", {}).get("containerStatuses", [])
        if not containers:
            return {"value": "0/0", "style": "color: #52525b;"}
        ready_count = sum(1 for c in containers if c.get("ready"))
        total = len(containers)
        style = "color: #10b981;" if ready_count == total else "color: #ef4444;"
        return {"value": f"{ready_count}/{total}", "style": style}

    @dashboardColumn("Restarts")
    def restarts(self, row: dict[str, Any]) -> CellResult:
        containers = row.get("status", {}).get("containerStatuses", [])
        total = sum(c.get("restartCount", 0) for c in containers)
        if total == 0:
            style = "color: #71717a;"
        elif total < 5:
            style = "color: #f59e0b;"
        else:
            style = "color: #ef4444; font-weight: 700;"
        return {"value": str(total), "style": style}

    @dashboardColumn("Node")
    def node(self, row: dict[str, Any]) -> CellResult:
        node = row.get("spec", {}).get("nodeName", "—")
        return {"value": node, "style": "color: #71717a; font-family: monospace;"}

    @dashboardColumn("Age")
    def age(self, row: dict[str, Any]) -> CellResult:
        from datetime import datetime, timezone
        created = row.get("metadata", {}).get("creationTimestamp", "")
        if not created:
            return {"value": "—", "style": "color: #52525b;"}
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - dt
            hours = int(delta.total_seconds() // 3600)
            if hours < 1:
                age_str = f"{int(delta.total_seconds() // 60)}m"
            elif hours < 24:
                age_str = f"{hours}h"
            else:
                age_str = f"{hours // 24}d"
        except Exception:
            age_str = "—"
        return {"value": age_str, "style": "color: #71717a; font-family: monospace;"}
