# Chart-Monitor API Contracts

## `GET /api/v1/dashboards`
Lists all loaded dashboards from the `FileStore`.

**Response (200 OK)**
```json
[
  {
    "id": "kubernetes-nodes",
    "name": "Kubernetes Node Status",
    "description": "Displays health metrics for all k8s nodes.",
    "scrape_interval_seconds": 30
  }
]
```

## `GET /api/v1/dashboards/{dashboard_id}/data`
Executes the `Collector` associated with the dashboard, applies the `TableDashboard` extraction and styling rules, and returns the formatted data.

**Response (200 OK)**
```json
{
  "dashboard_id": "kubernetes-nodes",
  "scrape_interval_seconds": 30,
  "columns": ["Node Name", "CPU", "Status"],
  "rows": [
    {
      "Node Name": {"value": "ip-10-0-0-1", "style": ""},
      "CPU": {"value": "85%", "style": "text-orange-500 font-bold"},
      "Status": {"value": "Ready", "style": "text-green-500"}
    }
  ],
  "error": null
}
```

**Response (500 Internal Server Error / Handled Exception)**
If the `Collector` fails during execution or secret resolution fails.
```json
{
  "dashboard_id": "kubernetes-nodes",
  "scrape_interval_seconds": 30,
  "columns": [],
  "rows": [],
  "error": "KeyError: 'GITHUB_TOKEN' not found in environment or Vault."
}
```
