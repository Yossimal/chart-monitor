# End-to-End Data Flow

This page traces one complete request cycle from a user opening a Dashboard to rows appearing in the browser.

---

## Full flow diagram

```
Developer commits pods.py + pod_dashboard.py
        │
        ▼ (git push)
Remote Git Repository
        │
        ▼ (POST /api/v1/git/sync  OR  background Poller)
Backend: git pull → FileStore.reload()
        │  imports pods.py, pod_dashboard.py
        │  registers PodCollector, PodDashboard
        │
        ▼ (user clicks "pod_dashboard" in sidebar)
Browser: GET /api/v1/dashboards/pod_dashboard/data
        │
        ▼
FastAPI routes.py: get_dashboard_data("pod_dashboard")
        │
        ▼
pipeline.run_dashboard("pod_dashboard")
  ├── FileStore.get_dashboards()["pod_dashboard"]  → PodDashboard class
  └── PodDashboard.getCollector()                  → PodCollector instance
        │
        ▼
executor.execute(PodCollector)
  ├── RestrictedPython sandbox: compile + exec collect()
  │       └── requests.get("https://k8s-api/pods") → raw API response
  │       └── return [{"name": "pod-1", "status": "Running"}, ...]
  └── safe_collect(): enforce max_data=500, truncate if needed
        │
        ▼
PodDashboard.get_columns()
  └── [("Pod Name", pod_name), ("Status", status), ("Restarts", restarts)]
        │
        ▼
For each row × column: extractor(row) → CellResult {value, style}
  e.g. status("Running") → {"value": "Running", "style": "text-green-500"}
        │
        ▼
FastAPI: JSON response
  {
    "dashboard_id": "pod_dashboard",
    "columns": ["Pod Name", "Status", "Restarts"],
    "rows": [
      {
        "Pod Name":  {"value": "pod-1", "style": ""},
        "Status":    {"value": "Running", "style": "text-green-500"},
        "Restarts":  {"value": 0, "style": ""}
      },
      ...
    ],
    "scrape_interval_seconds": 30
  }
        │
        ▼ (HTTP response arrives in browser)
app.js: store rows in memory
        │
        ▼
getFilteredAndSortedRows()
  ├── filterMode = 'column'? → apply columnFilters object
  ├── filterMode = 'sql'?    → return previously sql.js-filtered rows
  └── (no filter active)    → return all rows
        │
        ▼
sort by sortColumn / sortDir (if set)
        │
        ▼
renderProcessedTable(columns, filteredRows)
  └── Build <table> DOM: one <th> per column, one <tr> per row
      Each <td> gets the CellResult.style as its CSS class
        │
        ▼
User sees the table. After scrape_interval seconds, the cycle repeats from
"Browser: GET /api/v1/dashboards/pod_dashboard/data".
```

---

## What is persisted vs recomputed

| Data | Persisted? | Where |
|------|-----------|-------|
| Collector + Dashboard scripts | Yes | Git repository |
| Local Git clone | Yes | `GIT_TARGET_PATH` on server |
| Collector + Dashboard registry | In-memory only | FileStore in the backend process |
| Collected rows | In-memory only | Python process memory, per request |
| SQLite DB (SQL Collector) | No | Destroyed after each `collect()` call |
| API response rows | In-memory only | Browser memory (`app.js`) |
| sql.js filter results | In-memory only | Browser memory, cleared on dashboard switch |
| Filter/sort state | URL params + `localStorage` | Browser |
| Theme preference | `localStorage` | Browser |
| `SYNC_SECRET` (if "remember me") | `localStorage` | Browser |

---

## SQL Collector variant

When `PodDashboard` uses a `SQLCollector` instead of a standard Collector, the pipeline adds one step:

```
... (same up to executor)
        │
        ▼
SQLCollector.collect()
  ├── init_tables(): register PodCollector, NodeCollector
  ├── Collect rows from PodCollector (runs the sandbox for PodCollector)
  ├── Collect rows from NodeCollector (runs the sandbox for NodeCollector)
  ├── Build in-memory SQLite DB: raw tables + views
  ├── Execute user's SELECT ... JOIN ...
  └── Return list[dict] results
        │
        ▼
(same pipeline continues: Dashboard columns, JSON response, browser render)
```

The upstream Collectors each run in their own sandbox invocation. The SQLite DB is created and destroyed within the one `collect()` call.

---

## Navigating deeper

- [GitOps Sync](gitops-sync.md) — the `git pull` and `FileStore.reload()` steps
- [Collector Execution](collector-execution.md) — the RestrictedPython sandbox
- [SQL Layer](sql-layer.md) — the two SQLite execution contexts
- [Dashboard Rendering](dashboard-rendering.md) — filter, sort, URL state
