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

## GitOps — Connecting a Git Repository

Chart-Monitor can sync collector and dashboard scripts from a remote Git repository. Three authentication methods are supported:

| Method | `GIT_CONNECTION_METHOD` | Best for |
|--------|------------------------|----------|
| SSH key | `ssh` (default) | GitHub, GitLab, any server with SSH deploy keys |
| HTTP token | `http-token` | Servers that accept a single bearer/access token |
| HTTP username + token | `http-user-token` | Servers requiring Basic auth (username + password/PAT) |

### SSH

```bash
export GIT_CONNECTION_METHOD=ssh
export GIT_SSH_URL=git@github.com:your-org/your-repo.git
export GIT_SSH_KEY_PATH=/path/to/id_rsa
export GIT_TARGET_PATH=./store
export SYNC_SECRET=your-sync-secret
```

### HTTP token

```bash
export GIT_CONNECTION_METHOD=http-token
export GIT_REPO_URL=https://github.com/your-org/your-repo.git
export GIT_HTTP_TOKEN=ghp_xxxxxxxxxxxx
export GIT_TARGET_PATH=./store
export SYNC_SECRET=your-sync-secret
```

### HTTP username + token

```bash
export GIT_CONNECTION_METHOD=http-user-token
export GIT_REPO_URL=https://gitlab.company.internal/org/repo.git
export GIT_HTTP_USERNAME=svc-account
export GIT_HTTP_TOKEN=glpat-xxxxxxxxxxxx
export GIT_TARGET_PATH=./store
export SYNC_SECRET=your-sync-secret
```

### On-premises servers with self-signed certificates

Add `GIT_SKIP_VERIFY=true` to bypass SSH host key or HTTPS TLS verification on trusted internal networks.

Trigger a manual sync:

```bash
curl -X POST http://localhost:8000/api/v1/git/sync \
  -H "Authorization: Bearer your-sync-secret"
```

---

## Architecture

```
chart-monitor/
├── backend/
│   ├── src/
│   │   ├── api/        # FastAPI routes (GET /dashboards, /dashboards/{id}/data, POST /git/sync)
│   │   ├── engine/     # CodeExecutor, VariableInjector, FieldExtractor, Pipeline
│   │   ├── models/     # Collector & TableDashboard base classes + annotations
│   │   └── storage/    # FileStore, poller background task, git_sync (GitOps)
│   └── tests/
├── frontend/
│   ├── src/            # index.html, app.js, styles.css → output.css
│   ├── package.json    # local Tailwind build (no CDN)
│   └── tailwind.config.js
├── helm/chart-monitor/ # Helm 3 chart for Kubernetes / OpenShift deployment
└── store/              # Drop your .py Collector/Dashboard files here
```

## Environment Variables

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `CHART_MONITOR_STORE_DIR` | `store` | Directory scanned for collector/dashboard `.py` files |
| `CHART_MONITOR_POLL_INTERVAL` | `30` | How often (seconds) the FileStore is re-scanned |
| `CHART_MONITOR_SCRAPE_INTERVAL` | `30` | Default frontend poll interval |
| `CHART_MONITOR_MAX_DATA` | `500` | Default max rows per collector |

### GitOps

| Variable | Default | Description |
|----------|---------|-------------|
| `GIT_CONNECTION_METHOD` | `ssh` | Connection method: `ssh`, `http-token`, `http-user-token` |
| `GIT_TARGET_PATH` | — | Directory where the repo will be cloned/pulled |
| `SYNC_SECRET` | — | Bearer token to authenticate `POST /api/v1/git/sync` |
| `GIT_SKIP_VERIFY` | `false` | Bypass SSH host key or HTTPS TLS verification (on-prem use) |
| `GIT_SSH_URL` | — | SSH clone URL (`ssh` method) |
| `GIT_SSH_KEY_PATH` | — | Absolute path to the SSH private key (`ssh` method) |
| `GIT_REPO_URL` | — | HTTPS clone URL (`http-token` / `http-user-token` methods) |
| `GIT_HTTP_TOKEN` | — | Access token or password (`http-token` / `http-user-token`) |
| `GIT_HTTP_USERNAME` | — | Username (`http-user-token` method only) |

## Running Tests

```bash
cd backend
pytest
```

## Kubernetes / On-Prem Deployment

See [`DEPLOY.md`](DEPLOY.md) for the full deployment guide including Helm chart usage, secret creation, and migration instructions.
