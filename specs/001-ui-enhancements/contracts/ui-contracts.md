# Phase 1: API Contracts (UI Enhancements)

These enhancements extend the existing `001-core-engine/contracts/api.md` without breaking backwards compatibility.

## 1. Dashboard Listing Endpoint Extended

**Endpoint**: `GET /api/v1/dashboards`

The list of dashboards will now resolve `set_name` if provided by the dashboard class. If a `set_name` is > 150 characters, it should be intercepted (likely at the pipeline level) and either flagged with an error or rejected.

```json
[
  {
    "id": "pods-dashboard",
    "name": "Pods Health Dashboard", // If set_name exists, it maps here. If > 150 chars, throw exception/error string here.
    "scrape_interval_seconds": 30
  }
]
```

## 2. Cell Data Extended (`presentValue`)

**Endpoint**: `GET /api/v1/dashboards/{dashboard_id}/data`

The `rows` array introduces the optional `display` key within each cell object.

```json
{
  "dashboard_id": "pods-dashboard",
  "scrape_interval_seconds": 30,
  "columns": ["Pod Name", "CPU Usage", "Created At"],
  "rows": [
    {
      "Pod Name": {
        "value": "nginx-xyz", 
        "style": ""
      },
      "CPU Usage": {
        "value": 0.85, 
        "display": "85%", 
        "style": "text-danger"
      },
      "Created At": {
        "value": "2026-03-10T12:00:00Z",
        "display": "10 minutes ago",
        "style": ""
      }
    }
  ],
  "error": null
}
```

**Sorting Contract (Frontend)**:
1. When sorting a column, the frontend MUST use `value` instead of `display`.
2. The UI simply renders `display` to the user; if `display` is `null` or missing, it falls back to rendering `value`.
3. If the entire column evaluates as mixed numbers and strings based on `value`, fallback to standard string sorting.
4. If a cell contains literal `null` for `value`, it is treated as the lowest possible sort value.
