# Dashboards

A **Dashboard** is a Python class that binds a Collector to a set of named, styled columns. It controls what the user sees in the browser: which data fields are shown, what each column is called, and how each cell is styled.

---

## Anatomy of a Dashboard

A Dashboard extends `TableDashboard` and must:

1. Implement `getCollector()` — return the Collector that supplies the data
2. Define at least one method decorated with `@dashboardColumn` — each method extracts and optionally styles one column

```python
from src.models.collector import Collector
from src.models.dashboard import TableDashboard, dashboardColumn, CellResult
from pods import PodCollector

class PodDashboard(TableDashboard):
    def getCollector(self) -> Collector:
        return PodCollector()

    @dashboardColumn("Pod Name")
    def pod_name(self, row: dict) -> CellResult:
        return {"value": row["name"], "style": ""}

    @dashboardColumn("Status")
    def status(self, row: dict) -> CellResult:
        color = "text-green-500" if row["status"] == "Running" else "text-red-400"
        return {"value": row["status"], "style": color}

    @dashboardColumn("Node")
    def node(self, row: dict) -> CellResult:
        return {"value": row["node"], "style": ""}
```

---

## `@dashboardColumn`

Each column method receives one `row` argument — a plain dict from the Collector — and returns a `CellResult`.

### CellResult fields

| Field | Required | Description |
|-------|----------|-------------|
| `value` | Yes | The raw value shown in the cell (any type) |
| `display` | No | Override string shown in the cell (useful for formatting dates, numbers, etc.) |
| `style` | Yes | CSS class string applied to the cell (use empty string `""` for no styling) |

---

## Column ordering

Columns appear in the UI in the order the `@dashboardColumn` methods are defined in the class body.

---

## Dashboard ID

The dashboard's ID in the sidebar and URL is derived from the class name. `PodDashboard` becomes `pod_dashboard` (snake_case). This ID is used in the API route `/api/v1/dashboards/{dashboard_id}/data`.

---

## Where Dashboards live

Dashboard `.py` files live in the same Git repository as Collectors. Chart-Monitor registers any class that inherits from `TableDashboard`.

```
your-repo/
├── pods.py           # PodCollector
└── pod_dashboard.py  # PodDashboard  ← references PodCollector
```

---

## Relationship to Collectors

A Dashboard **does not fetch data itself** — it delegates to its Collector.

```
Browser → GET /api/v1/dashboards/pod_dashboard/data
              ↓
         PodDashboard.getCollector() → PodCollector
              ↓
         PodCollector.collect() → list[dict]
              ↓
         PodDashboard columns → styled rows → JSON response
              ↓
         Browser renders table
```

See the [Collectors concept page](collectors.md) and the [Create a Dashboard how-to guide](../how-to/create-dashboard.md) for more.
