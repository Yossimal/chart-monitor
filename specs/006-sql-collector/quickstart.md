# Quickstart: SQL Collector

## Scenario 1: Basic SQL JOIN across two collectors

**Goal**: Combine pod data and node data using a SQL JOIN.

### Step 1: Create test collectors

```python
# store/test_pods_collector.py
from src.models.collector import Collector

class TestPodsCollector(Collector):
    def collect(self):
        return [
            {"metadata": {"name": "web-1", "namespace": "prod"}, "spec": {"nodeName": "node-a"}},
            {"metadata": {"name": "api-1", "namespace": "prod"}, "spec": {"nodeName": "node-b"}},
            {"metadata": {"name": "debug-1", "namespace": "kube-system"}, "spec": {"nodeName": "node-a"}},
        ]

class TestNodesCollector(Collector):
    def collect(self):
        return [
            {"metadata": {"name": "node-a", "labels": {"region": "us-east-1"}}},
            {"metadata": {"name": "node-b", "labels": {"region": "eu-west-1"}}},
        ]
```

### Step 2: Create SQLCollector subclass

```python
# store/pods_by_region.py
from src.models.collector import SQLCollector
from store.test_pods_collector import TestPodsCollector, TestNodesCollector

class PodsByRegionCollector(SQLCollector):
    def init_tables(self):
        self.define_table(TestPodsCollector, "pods")
        self.define_table(TestNodesCollector, "nodes")

        self.define_view("pods_view", "pods")
        self.view_column("pods_view", "pod_name", "metadata.name")
        self.view_column("pods_view", "namespace", "metadata.namespace")
        self.view_column("pods_view", "node_name", "spec.nodeName")

        self.define_view("nodes_view", "nodes")
        self.view_column("nodes_view", "node_name", "metadata.name")
        self.view_column("nodes_view", "region", "metadata.labels.region")

    def sql(self):
        return """
            SELECT p.pod_name, p.namespace, n.region
            FROM pods_view p
            JOIN nodes_view n ON p.node_name = n.node_name
            WHERE p.namespace != 'kube-system'
            ORDER BY n.region
        """
```

### Step 3: Expected output

```python
collector = PodsByRegionCollector()
result = collector.collect()
# [
#     {"pod_name": "api-1", "namespace": "prod", "region": "eu-west-1"},
#     {"pod_name": "web-1", "namespace": "prod", "region": "us-east-1"},
# ]
```

## Scenario 2: Use SQLCollector in a TableDashboard

```python
# store/pods_by_region_dashboard.py
from src.models.dashboard import TableDashboard, CellResult, dashboardColumn
from src.models.collector import Collector
from store.pods_by_region import PodsByRegionCollector

class PodsByRegionDashboard(TableDashboard):
    def getCollector(self) -> Collector:
        return PodsByRegionCollector()

    @dashboardColumn("Pod")
    def pod_name(self, row: dict) -> CellResult:
        return {"value": row["pod_name"], "style": "font-family: monospace;"}

    @dashboardColumn("Namespace")
    def namespace(self, row: dict) -> CellResult:
        return {"value": row["namespace"], "style": "color: #818cf8;"}

    @dashboardColumn("Region")
    def region(self, row: dict) -> CellResult:
        return {"value": row["region"], "style": "color: #10b981;"}
```

## Scenario 3: Frontend SQL filter

1. Open any dashboard in the browser
2. Click the "SQL" toggle button (next to the filter row)
3. Type: `SELECT * FROM data WHERE status = 'Running'`
4. Press Enter — table filters to show only running pods
5. Click "Simple" toggle to restore original view

## Scenario 4: SQLCollector with secrets

```python
class SecureCollector(SQLCollector):
    def init_tables(self):
        self.define_table(
            PodsCollector,
            "pods",
            secrets={"K8S_TOKEN": os.environ["K8S_TOKEN"]}
        )
        self.define_view("pods_view", "pods")
        self.view_column("pods_view", "name", "metadata.name")

    def sql(self):
        return "SELECT name FROM pods_view"
```
