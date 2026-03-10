# Chart-Monitor

**Dynamic data extraction, transformation, and visualization engine.**

Chart-Monitor runs Python data-collection scripts inside a secure sandbox and serves the results as styled, auto-refreshing dashboard tables.

---

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev]"

# Set required environment variables
export CHART_MONITOR_STORE_DIR=../store        # path to your collector/dashboard files
export CHART_MONITOR_SCRAPE_INTERVAL=30        # default polling interval (seconds)
export CHART_MONITOR_MAX_DATA=500              # max rows per collector
export GITHUB_TOKEN=ghp_xxxx                  # example secret used by quickstart

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend (local Tailwind build – no CDN required)

```bash
cd frontend
npm install                    # installs tailwindcss locally
npm run build                  # outputs frontend/src/output.css

# Serve via the backend (already mounted at /)
# Or open frontend/src/index.html directly for quick dev iteration
```

### 3. Open the dashboard

Visit `http://localhost:8000/` — the backend serves the static frontend automatically.

---

## Writing a Collector

Create a `.py` file in your `CHART_MONITOR_STORE_DIR`:

```python
from src.models.collector import Collector, secret

class MyCollector(Collector):
    max_data = 100          # override env default
    scrape_interval = 60   # seconds

    @secret("MY_API_KEY")   # resolves os.environ["MY_API_KEY"]
    def collect(self, secrets=None):
        # fetch data from an external system
        return [{"name": "foo", "status": "ok"}]
```

## Writing a Dashboard

```python
from src.models.dashboard import TableDashboard, dashboardColumn, CellResult

class MyDashboard(TableDashboard):
    def getCollector(self):
        return MyCollector()

    @dashboardColumn("Name")
    def name(self, row) -> CellResult:
        return {"value": row["name"], "style": "font-medium"}

    @dashboardColumn("Status")
    def status(self, row) -> CellResult:
        style = "text-green-400" if row["status"] == "ok" else "text-red-400"
        return {"value": row["status"], "style": style}
```

---

## Architecture

```
chart-monitor/
├── backend/
│   ├── src/
│   │   ├── api/        # FastAPI routes (GET /dashboards, /dashboards/{id}/data)
│   │   ├── engine/     # CodeExecutor, VariableInjector, FieldExtractor, Pipeline
│   │   ├── models/     # Collector & TableDashboard base classes + annotations
│   │   └── storage/    # FileStore (auto-polls store dir), poller background task
│   └── tests/
├── frontend/
│   ├── src/            # index.html, app.js, styles.css → output.css
│   ├── package.json    # local Tailwind build (no CDN)
│   └── tailwind.config.js
└── store/              # Drop your .py Collector/Dashboard files here
```

## Environment Variables

| Variable                        | Default | Description                                         |
| ------------------------------- | ------- | --------------------------------------------------- |
| `CHART_MONITOR_STORE_DIR`       | `store` | Directory scanned for collector/dashboard .py files |
| `CHART_MONITOR_POLL_INTERVAL`   | `30`    | How often (seconds) the FileStore is re-scanned     |
| `CHART_MONITOR_SCRAPE_INTERVAL` | `30`    | Default frontend poll interval                      |
| `CHART_MONITOR_MAX_DATA`        | `500`   | Default max rows per collector                      |

## Running Tests

```bash
cd backend
pytest
```
