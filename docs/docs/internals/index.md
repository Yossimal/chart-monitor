# Architecture Overview

Chart-Monitor is a lightweight monitoring platform built from a small set of components. This page gives you the bird's-eye view; each linked page goes deep on one component.

---

## Component map

```
┌────────────────────────────────────────────────────────────────────┐
│  Git Repository (remote)                                           │
│  your-org/your-repo  (Collector + Dashboard .py files)             │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ SSH pull (manual or scheduled)
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│  Backend  (Python 3.11 + FastAPI + uvicorn)                        │
│                                                                    │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────────┐ │
│  │  Poller  │───▶│  FileStore   │───▶│  Engine (pipeline.py)     │ │
│  │(git sync)│    │(load .py     │    │  • YAML parse             │ │
│  └──────────┘    │ files)       │    │  • RestrictedPython sandbox│ │
│                  └──────────────┘    │  • Collector.collect()    │ │
│                                      │  • SQLCollector (DuckDB   │ │
│                                      │    / SQLite)              │ │
│                                      │  • Dashboard.columns()    │ │
│                                      └────────────┬──────────────┘ │
│                                                   │                │
│  ┌──────────────────────────────────────────────┐ │                │
│  │  FastAPI  (routes.py)                        │◀┘                │
│  │  GET  /api/v1/dashboards                     │                  │
│  │  GET  /api/v1/dashboards/{id}/data           │                  │
│  │  POST /api/v1/git/sync                       │                  │
│  │  GET  /api/v1/git/status                     │                  │
│  └──────────────────────┬───────────────────────┘                  │
└─────────────────────────│──────────────────────────────────────────┘
                          │ JSON over HTTP
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│  Browser  (Vanilla JS)                                             │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  app.js                                                     │   │
│  │  • Polls /api/v1/dashboards/{id}/data every scrape_interval │   │
│  │  • Applies column filters or sql.js SQL filter              │   │
│  │  • Renders table DOM, syncs state to URL params             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  sql.js (WASM) — SQLite in the browser for the SQL filter panel    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Component roles

| Component | Role |
|-----------|------|
| **Git repository** | Source of truth for all Collector and Dashboard Python scripts |
| **Poller** | Background task that pulls new commits from Git on a schedule |
| **FileStore** | Scans the local clone directory, imports `.py` files, registers Collector and Dashboard classes |
| **Engine / pipeline** | Orchestrates a full scrape: invokes the Collector, runs the RestrictedPython sandbox, applies the Dashboard column transformations |
| **FastAPI + routes** | HTTP API serving dashboard list, data, and GitOps sync endpoints; serves static files (frontend + docs) |
| **app.js** | Vanilla JavaScript frontend: polls the API, manages filter/sort state, renders the table, serialises state to URL |
| **sql.js (WASM)** | WebAssembly SQLite port running in the browser; executes SQL filter queries entirely client-side |

---

## Deep dives

- [GitOps Sync](gitops-sync.md) — how scripts get from Git to the backend
- [Collector Execution](collector-execution.md) — the sandbox and pipeline
- [SQL Layer](sql-layer.md) — two SQL engines (backend + browser)
- [Dashboard Rendering](dashboard-rendering.md) — filter, sort, and URL state
- [End-to-End Data Flow](data-flow-end-to-end.md) — one complete request cycle
