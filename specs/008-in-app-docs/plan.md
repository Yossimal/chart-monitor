# Implementation Plan: In-App Documentation (/docs)

**Branch**: `008-in-app-docs` | **Date**: 2026-04-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-in-app-docs/spec.md`

## Summary

Add a rich, MkDocs-powered documentation site served at `/docs` that covers every user-facing capability of Chart-Monitor. MkDocs Material provides the content tree, in-page search, syntax highlighting, and dark/light mode out-of-the-box. FastAPI mounts the built static output at `/docs`. The existing FastAPI Swagger UI moves from `/docs` to `/api/docs` to free up the `/docs` path. A "Docs" link is added to every page of the main Vanilla app.

## Technical Context

**Language/Version**: Python 3.11+ (backend/build), Vanilla HTML/CSS/JS (main frontend)
**Primary Dependencies**: MkDocs ≥1.5, mkdocs-material ≥9.5, FastAPI (existing), Pygments (transitive via mkdocs-material)
**Storage**: File-system only — docs source in `docs/docs/*.md`, build output in `docs/site/` (gitignored)
**Testing**: Manual smoke tests (navigate to `/docs`, verify search, ToC, dark mode, deep links); `pytest` integration test for route availability
**Target Platform**: Linux server (Docker) + local dev (Windows/Mac)
**Project Type**: Web service + static documentation site
**Performance Goals**: Docs page first load < 1s (SC-007); MkDocs build < 30s
**Constraints**: No CDN — all assets bundled; docs must render without GitOps configured; no Node.js dependency

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Dynamic Data Engine | ✅ Pass | Docs feature does not affect the data engine |
| II. GitOps First | ✅ Pass | Docs source is committed to the repo — inherently GitOps-friendly |
| III. Strict Typing & Clean Code | ✅ Pass | No new Python code beyond a two-line main.py change; MkDocs config is YAML |
| IV. Secure Execution Sandbox | ✅ Pass | Static file serving only; no sandboxed execution involved |
| V. Vanilla Desktop-First UI | ✅ Pass | MkDocs generates standard HTML/CSS/JS at build time; the main app UI change is a single `<a>` tag |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/008-in-app-docs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # N/A — static content feature, no data model
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
docs/                          # NEW — MkDocs project root
├── mkdocs.yml                 # MkDocs configuration
├── docs/                      # MkDocs docs_dir (markdown sources)
│   ├── index.md               # Landing page / overview
│   ├── getting-started/
│   │   └── connect-git.md     # US2 — connecting a Git repository
│   ├── concepts/
│   │   ├── collectors.md                # US3 — what a Collector is
│   │   ├── dashboards.md                # US3 — what a Dashboard is
│   │   └── secrets.md                   # US3/US6 — what Secrets are and how they flow
│   ├── how-to/
│   │   ├── create-collector.md       # US4 — standard Collector
│   │   ├── create-sql-collector.md   # US5 — SQL Collector
│   │   ├── load-secrets.md           # US6 — secrets
│   │   └── create-dashboard.md       # US7 — Dashboard
│   ├── concepts/
│   │   ├── collectors.md                # US3 — what a Collector is
│   │   ├── dashboards.md                # US3 — what a Dashboard is
│   │   └── secrets.md                   # US3/US6 — what Secrets are and how they flow
│   ├── ui/
│   │   ├── index.md                     # US8 — UI overview and layout
│   │   ├── sidebar-and-navigation.md    # US8 — sidebar, search, dashboard selection
│   │   ├── column-filter-and-sort.md    # US8 — per-column filter menu, multi-value filter, sort
│   │   ├── sql-filter.md                # US8 — SQL filter panel, writing queries, filter modes
│   │   ├── data-amount-and-paging.md    # US8 — row counts, paging / virtual scroll behaviour
│   │   ├── sync-and-refresh.md          # US8 — manual sync modal, auto-refresh, connection banners
│   │   └── theme-and-settings.md        # US8 — dark/light toggle, persistent preferences
│   └── internals/
│       ├── index.md                     # US9 — architecture overview, component map
│       ├── gitops-sync.md               # US9 — Git sync flow, polling, deploy keys
│       ├── collector-execution.md       # US9 — YAML parse → RestrictedPython sandbox → result shape
│       ├── sql-layer.md                 # US9 — backend SQL (DuckDB) and frontend SQL (sql.js WASM)
│       ├── dashboard-rendering.md       # US9 — Dashboard YAML → table render → filter/sort pipeline
│       └── data-flow-end-to-end.md      # US9 — full flow diagram: Git → sandbox → SQL → UI
└── site/                      # Build output — gitignored

backend/
├── pyproject.toml             # MODIFIED — add [docs] optional dependency group
└── src/
    └── main.py                # MODIFIED — docs_url="/api/docs", mount /docs

frontend/
└── src/
    └── index.html             # MODIFIED — add "Docs" link in header
```

**Structure Decision**: MkDocs project lives in `docs/` at the repository root, keeping all documentation tooling self-contained. FastAPI mounts `docs/site/` at `/docs`; the existing Vanilla frontend mount at `/` remains the catch-all. The `StaticFiles` mount for `/docs` is registered BEFORE the `/` mount so it takes priority.

## Implementation Details

### 1. MkDocs Configuration (`docs/mkdocs.yml`)

Key settings:
- `site_name: Chart-Monitor Docs`
- `docs_dir: docs` (markdown sources)
- `site_dir: site` (build output — served by FastAPI)
- Theme: `material` with `palette:` toggle for light/dark, `features:` including `navigation.sections`, `navigation.tabs`, `navigation.top`, `toc.integrate`, `content.code.copy`, `search.highlight`
- `nav:` explicitly defined to group pages into: Getting Started / Concepts / How-To Guides / Using the UI / How It Works
- Extensions: `pymdownx.highlight`, `pymdownx.superfences`, `pymdownx.inlinehilite`, `admonition`, `toc` (with `permalink: true` for FR-004/FR-005 deep-link anchors)
- Plugins: `search` (built-in, satisfies FR-022's search requirement)

### 2. FastAPI changes (`backend/src/main.py`)

Two changes:
```python
# Change 1: move Swagger/ReDoc to /api/docs
app = FastAPI(
    ...
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Change 2: mount MkDocs built output at /docs (before the / catch-all)
_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "site"
if _DOCS_DIR.exists():
    app.mount("/docs", StaticFiles(directory=str(_DOCS_DIR), html=True), name="docs")
```

### 3. "Docs" link in main app (`frontend/src/index.html`)

Add `<a href="/docs" class="nav-btn" style="width:auto;padding:4px 8px;margin-right:8px;">Docs</a>` to:
- The `header-right` div inside `<header class="app-header">` (main app, FR-021)
- The `gitops-setup-header` div (GitOps-unconfigured page, FR-021)

### 4. Dependencies (`backend/pyproject.toml`)

```toml
[project.optional-dependencies]
docs = [
    "mkdocs>=1.5",
    "mkdocs-material>=9.5",
]
dev = [
    ...existing...
]
```

Build command (CI / local): `cd docs && mkdocs build`
Dev command (local preview): `cd docs && mkdocs serve`

### 5. Gitignore

Add `docs/site/` to `.gitignore` (build output must not be committed).

## Content Outline

Each Markdown file covers the section documented in its User Story. Minimum required content per file:

### Getting Started

| File | Required content |
|------|-----------------|
| `index.md` | What Chart-Monitor is; one-liner on Collectors, Dashboards, Secrets; quick-start links to every major section |
| `getting-started/connect-git.md` | SSH key generation, GitHub/GitLab/Bitbucket deploy key setup (tabbed), all 4 required env vars, restart note, troubleshooting |

### Concepts

| File | Required content |
|------|-----------------|
| `concepts/collectors.md` | What a Collector is; its role in the pipeline; Collector vs SQL Collector distinction; file location in repo; minimal YAML skeleton |
| `concepts/dashboards.md` | What a Dashboard is; how it references Collectors; column binding; file location in repo; minimal YAML skeleton |
| `concepts/secrets.md` | What Secrets are; why they exist (keep credentials out of YAML); where they come from (env vars / secrets backend); how they flow into a Collector script |

### How-To Guides

| File | Required content |
|------|-----------------|
| `how-to/create-collector.md` | Full YAML schema (required vs optional fields), RestrictedPython sandbox constraints & allowed helpers/modules, expected return shape (list of dicts), typing rules, complete worked example |
| `how-to/create-sql-collector.md` | Differences from standard Collector, how upstream inputs are declared, SQL dialect notes & limits (sql.js SQLite dialect), worked example joining two upstream Collectors |
| `how-to/load-secrets.md` | Where secrets are defined (env var / vault), reference syntax inside a script (`secrets["KEY"]`), missing-secret error behaviour, security notes (never logged, never in YAML) |
| `how-to/create-dashboard.md` | Full YAML schema, referencing one or multiple Collectors, column definitions (name, type, display options), worked example end-to-end |

### Using the UI

| File | Required content |
|------|-----------------|
| `ui/index.md` | UI layout overview (header, sidebar, main content area, SQL panel); labelled screenshot or ASCII diagram |
| `ui/sidebar-and-navigation.md` | Dashboard list, search box behaviour, selecting a dashboard, loading state |
| `ui/column-filter-and-sort.md` | Opening the per-column menu, multi-value checkbox filter, active-filter indicator (dot), clearing column filters, single-column sort, sort direction toggle |
| `ui/sql-filter.md` | Opening the SQL panel, writing a query, table name reference, running the query, switching between column-filter mode and SQL-filter mode, error display, clearing SQL filter |
| `ui/data-amount-and-paging.md` | How many rows are shown by default, scroll behaviour for large result sets, row count display |
| `ui/sync-and-refresh.md` | Manual sync button, sync secret modal, "Remember me" option, auto-refresh / polling interval, disconnected banner, reconnecting banner |
| `ui/theme-and-settings.md` | Dark/light toggle (header button), persistence in browser storage, how it affects the docs page |

### How It Works (Internals)

| File | Required content |
|------|-----------------|
| `internals/index.md` | High-level architecture map: GitOps repo → backend poller → engine → FastAPI → browser; component list with one-line role descriptions |
| `internals/gitops-sync.md` | How the backend polls the Git repo, SSH deploy key authentication, sync-to-disk flow, manual sync endpoint, what triggers a re-render |
| `internals/collector-execution.md` | YAML parsing → Collector model validation → RestrictedPython sandbox setup → script execution → result extraction → typing/coercion; what is allowed and blocked in the sandbox |
| `internals/sql-layer.md` | Two SQL contexts: backend DuckDB (for SQL Collectors, runs at collect time) and frontend sql.js WASM (for UI SQL filter, runs in browser); how data crosses the boundary; ephemeral vs persistent |
| `internals/dashboard-rendering.md` | Dashboard YAML → column schema → row binding → table DOM render; filter pipeline (column filters vs SQL filter, last-applied-wins); sort pipeline; URL state serialisation |
| `internals/data-flow-end-to-end.md` | Full narrative of one request cycle: user opens Dashboard → browser requests data → backend collects → SQL Collector optional → response → frontend filters/sorts → renders; annotated ASCII flow diagram |

## Complexity Tracking

No constitution violations — complexity tracking not required.
