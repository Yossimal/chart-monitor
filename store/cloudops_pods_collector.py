"""Example SQL dashboard: Pods joined with Nodes by region.

Demonstrates how to use ``SQLCollector`` as a drop-in replacement for
``Collector`` inside a ``TableDashboard``.

The dashboard joins pod data with node data to show each pod's region
alongside its name and namespace — something impossible with a single
simple collector.
"""
from __future__ import annotations

from typing import Any

from src.models.collector import Collector, SQLCollector
from src.models.dashboard import CellResult, TableDashboard, dashboardColumn
from store.pods_collector import PodsCollector

class CloudopsPodsCollector(SQLCollector):
    """Joins pods and nodes to produce (pod_name, namespace, region) rows."""

    scrape_interval: int = 30

    def init_tables(self) -> None:
        # Register source collectors as logical tables
        self.define_table(PodsCollector, "pods")

        # Define a view over pods that flattens nested fields
        self.define_view("pods", "pods")
        self.view_column("pods", "name", "metadata.name")
        self.view_column("pods","namespace","metadata.namespace")
        self.view_column("pods","generateName","metadata.generateName")
        self.view_column("pods","restartPolicy","spec.restartPolicy")

    def sql(self) -> str:
        return """
            SELECT
                *
            FROM pods
            WHERE namespace = 'cloudops'
        """

