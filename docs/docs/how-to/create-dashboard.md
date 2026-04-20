# Create a Dashboard

A Dashboard binds a Collector to a set of named, styled columns and makes the data visible in the Chart-Monitor UI.

**Prerequisites**: [Create a Collector](create-collector.md) · [Understand Dashboards](../concepts/dashboards.md)

---

## Step 1: Create the file

In your Git repository, create a new `.py` file for the Dashboard:

```
your-repo/
├── pods.py            # PodCollector (data source)
└── pod_dashboard.py   # PodDashboard (this file)
```

---

## Step 2: Implement the Dashboard class

```python
from src.models.collector import Collector
from src.models.dashboard import TableDashboard, dashboardColumn, CellResult
from pods import PodCollector

class PodDashboard(TableDashboard):
    """Displays running pods with status colour-coding."""

    def getCollector(self) -> Collector:
        return PodCollector()

    @dashboardColumn("Pod Name")
    def pod_name(self, row: dict) -> CellResult:
        return {"value": row["name"], "style": ""}

    @dashboardColumn("Status")
    def status(self, row: dict) -> CellResult:
        style = "text-green-500" if row["status"] == "Running" else "text-red-400"
        return {"value": row["status"], "style": style}

    @dashboardColumn("Restarts")
    def restarts(self, row: dict) -> CellResult:
        count = row.get("restarts", 0)
        style = "text-red-500 font-bold" if count > 5 else ""
        return {"value": count, "style": style}
```

---

## API reference

### `getCollector()`

Must return an instantiated Collector. This is called on every scrape.

```python
def getCollector(self) -> Collector:
    return PodCollector()
```

To configure the Collector per-dashboard, set attributes on it:

```python
def getCollector(self) -> Collector:
    c = PodCollector()
    c.max_data = 100
    c.scrape_interval = 60
    return c
```

### `@dashboardColumn(column_name)`

Decorates a method that extracts one column from each row.

| Parameter | Description |
|-----------|-------------|
| `column_name` | The header label shown in the UI |

The method receives `row: dict` (one row from the Collector) and returns a `CellResult`:

| Field | Required | Description |
|-------|----------|-------------|
| `value` | Yes | The raw value (string, int, float, bool, None) |
| `display` | No | Override text shown in the cell (e.g. formatted date) |
| `style` | Yes | CSS class string (Tailwind classes work; use `""` for none) |

### Column ordering

Columns appear in the UI in the **order the methods are defined** in the class body.

---

## Useful style patterns

```python
# Status colours
style = "text-green-500"   # green for healthy
style = "text-red-400"     # red for errors
style = "text-yellow-500"  # yellow for warning
style = "text-gray-400"    # gray for unknown/disabled

# Display override for large numbers
return {"value": 1234567, "display": "1.2M", "style": ""}

# Bold emphasis
style = "font-bold"

# Combine classes
style = "text-red-500 font-bold"
```

---

## Dashboard ID

The Dashboard's ID is derived from its class name in snake_case:

| Class name | Dashboard ID |
|-----------|-------------|
| `PodDashboard` | `pod_dashboard` |
| `MyServiceMetrics` | `my_service_metrics` |
| `K8sNodeHealth` | `k8s_node_health` |

The ID appears in the sidebar, the URL (`?dashboard=pod_dashboard`), and the API path (`/api/v1/dashboards/pod_dashboard/data`).

---

## Step 3: Commit and sync

1. Commit both the Collector and Dashboard files to your Git repository
2. In the Chart-Monitor UI, click **↕ Sync Scripts** in the sidebar
3. Enter your `SYNC_SECRET` and click **Sync**
4. The new Dashboard appears in the sidebar

---

## Complete example: Kubernetes nodes with memory

```python
import requests
from src.models.collector import Collector, secret
from src.models.dashboard import TableDashboard, dashboardColumn, CellResult


class NodeCollector(Collector):
    scrape_interval = 60

    @secret("K8S_API_TOKEN")
    def collect(self, secrets: dict) -> list[dict]:
        token = secrets["K8S_API_TOKEN"]
        resp = requests.get(
            "https://kubernetes.default.svc/api/v1/nodes",
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=5,
        )
        resp.raise_for_status()
        return [
            {
                "name": n["metadata"]["name"],
                "ready": next(
                    (c["status"] for c in n["status"]["conditions"] if c["type"] == "Ready"),
                    "Unknown",
                ),
                "cpu": n["status"]["capacity"].get("cpu", "?"),
                "memory": n["status"]["capacity"].get("memory", "?"),
            }
            for n in resp.json().get("items", [])
        ]


class NodeDashboard(TableDashboard):
    def getCollector(self) -> Collector:
        return NodeCollector()

    @dashboardColumn("Node")
    def node(self, row: dict) -> CellResult:
        return {"value": row["name"], "style": "font-mono text-sm"}

    @dashboardColumn("Ready")
    def ready(self, row: dict) -> CellResult:
        ok = row["ready"] == "True"
        return {"value": row["ready"], "style": "text-green-500" if ok else "text-red-400"}

    @dashboardColumn("CPU")
    def cpu(self, row: dict) -> CellResult:
        return {"value": row["cpu"], "style": ""}

    @dashboardColumn("Memory")
    def memory(self, row: dict) -> CellResult:
        return {"value": row["memory"], "style": ""}
```

---

## Common errors

??? failure "Dashboard not appearing in sidebar after sync"
    Check that the class correctly extends `TableDashboard` (not `Collector`). Also verify the file was committed and the sync completed successfully (check the sync response message).

??? failure "KeyError: 'field_name' in column method"
    The Collector returned rows that don't have the key your column method expects. Check the Collector's output shape.

??? failure "'NoneType' has no attribute 'collect'"
    `getCollector()` returned `None`. Make sure it always returns a Collector instance.
