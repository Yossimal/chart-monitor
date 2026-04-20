# Tasks: In-App Documentation (/docs)

**Input**: Design documents from `/specs/008-in-app-docs/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the MkDocs project, wire FastAPI, and update the main app — everything needed before any content can be written or served.

- [x] T001 Create `docs/` directory structure at repo root: `docs/mkdocs.yml`, `docs/docs/index.md` placeholder, `docs/docs/getting-started/`, `docs/docs/concepts/`, `docs/docs/how-to/`, `docs/docs/ui/`, `docs/docs/internals/`
- [x] T002 Add `docs = ["mkdocs>=1.5", "mkdocs-material>=9.5"]` optional dependency group to `backend/pyproject.toml`
- [x] T003 Add `docs/site/` to `.gitignore` at repo root
- [x] T004 Write `docs/mkdocs.yml` with: `site_name`, `docs_dir: docs`, `site_dir: site`, Material theme (light/dark palette toggle, `navigation.sections`, `navigation.tabs`, `navigation.top`, `toc.integrate`, `content.code.copy`, `search.highlight`), `pymdownx.highlight`, `pymdownx.superfences`, `pymdownx.inlinehilite`, `admonition`, `toc` with `permalink: true`, `search` plugin, and full `nav:` tree mapping all 22 pages listed in `specs/008-in-app-docs/plan.md`
- [x] T005 Modify `backend/src/main.py`: set `docs_url="/api/docs"`, `redoc_url="/api/redoc"`, `openapi_url="/api/openapi.json"` on the `FastAPI(...)` constructor
- [x] T006 Modify `backend/src/main.py`: resolve `_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "site"` and mount `StaticFiles(directory=str(_DOCS_DIR), html=True)` at `/docs` BEFORE the existing `/` catch-all mount, guarded by `if _DOCS_DIR.exists()`
- [x] T007 [P] Add `<a href="/docs" class="nav-btn" style="width:auto;padding:4px 8px;margin-right:8px;">Docs</a>` to the `header-right` div in `frontend/src/index.html` (main app header, FR-021)
- [x] T008 [P] Add `<a href="/docs" class="nav-btn" style="margin-top:12px;display:inline-block;">Docs</a>` to the `gitops-setup-header` div in `frontend/src/index.html` (GitOps-unconfigured page, FR-021)

**Checkpoint**: Run `pip install -e "backend[docs]" && cd docs && mkdocs build` — build must succeed. Open `http://localhost:8000/docs` — placeholder index page renders. Open `http://localhost:8000/api/docs` — Swagger UI renders (not the old `/docs`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Landing page and MkDocs nav skeleton — must exist before any section page can be meaningfully verified in context.

- [x] T009 Write `docs/docs/index.md`: What Chart-Monitor is (2–3 sentences), one-liner descriptions of Collectors / Dashboards / Secrets, a "Quick Start" section with links to `getting-started/connect-git.md`, `how-to/create-collector.md`, `how-to/create-dashboard.md`, and navigation cards or an admonition block pointing to each section of the docs

**Checkpoint**: Build docs and open `/docs` — landing page renders with working internal links to all major sections.

---

## Phase 3: US2 — Connecting a Git Repository (Priority: P1) 🎯 MVP

**Goal**: A new user can follow the Git repo connection guide end-to-end without leaving the docs.

**Independent Test**: Navigate to `/docs/getting-started/connect-git/`. Verify: SSH key generation command is present, GitHub/GitLab/Bitbucket tabs or sections are present, all 4 env vars (`GIT_SSH_URL`, `GIT_SSH_KEY_PATH`, `GIT_TARGET_PATH`, `SYNC_SECRET`) are documented with descriptions, restart instruction is present.

- [x] T010 [US2] Write `docs/docs/getting-started/connect-git.md`: intro paragraph explaining why Git connection is required; SSH key generation command (copyable code block); three provider sub-sections (GitHub, GitLab, Bitbucket) each covering deploy-key registration steps; table of all 4 required environment variables with name, example value, and description; "Restart the backend" note; troubleshooting admonition for common errors (wrong key type, missing write access, wrong URL format)

**Checkpoint**: Page renders at `/docs/getting-started/connect-git/`. All code blocks are syntax-highlighted. Deep link to `#environment-variables` anchors correctly.

---

## Phase 4: US3 — Concepts: Collectors, Dashboards, Secrets (Priority: P1)

**Goal**: A reader understands the three core concepts and how they relate before writing any YAML.

**Independent Test**: Read all three concept pages. Verify each answers its key question: (collectors.md) what a Collector produces; (dashboards.md) what a Dashboard consumes and how it references a Collector; (secrets.md) how a secret value reaches a Collector script without appearing in YAML or logs.

- [x] T011 [P] [US3] Write `docs/docs/concepts/collectors.md`: definition of a Collector; its role in the pipeline (data source); distinction between standard Collector and SQL Collector; where the file lives in the repo (`store/<name>/collector.yaml` or equivalent); minimal YAML skeleton with annotations; link to the How-To guide
- [x] T012 [P] [US3] Write `docs/docs/concepts/dashboards.md`: definition of a Dashboard; how it references one or more Collectors; column binding concept; where the file lives in the repo; minimal YAML skeleton with annotations; Collector → Dashboard relationship described (one or many Collectors, one Dashboard); link to the How-To guide
- [x] T013 [P] [US3] Write `docs/docs/concepts/secrets.md`: what Secrets are and why they exist; how they are supplied (environment variables / secrets backend); how they flow into a Collector script (`secrets["KEY"]` access pattern); what happens when a secret is missing (error surfaced, not silent); security guarantees (never logged, never in YAML); link to `how-to/load-secrets.md`

**Checkpoint**: All three concept pages render. Internal links between concept pages and their How-To counterparts resolve.

---

## Phase 5: US4 — Creating a Standard Collector (Priority: P1)

**Goal**: A user can write, commit, and sync a working standard Collector using only this page.

**Independent Test**: Navigate to `/docs/how-to/create-collector/`. Verify: full YAML schema is documented (every required and optional field), RestrictedPython constraints are listed (allowed/blocked modules), return shape is specified (list of dicts), a complete worked example is present and syntax-highlighted, the page is self-contained without requiring other pages.

- [x] T014 [US4] Write `docs/docs/how-to/create-collector.md`: prerequisites section (link to connecting Git, concept page); full YAML schema as a table (field name, type, required/optional, description) covering all fields supported by `backend/src/models/collector.py`; RestrictedPython sandbox section listing: allowed stdlib modules, blocked capabilities (no `os`, no `subprocess`, no `open` for write), available helpers (`requests`-style HTTP, `json`, `datetime`); return shape specification (list of dicts, column name keys, supported value types); step-by-step walkthrough creating a Collector that fetches a public JSON API; complete annotated YAML + script example in fenced code blocks; common errors admonition (wrong return type, import not allowed, missing field)

**Checkpoint**: Page renders with syntax-highlighted YAML and Python code blocks. Table of schema fields is readable. Deep links to specific sub-sections (e.g., `#return-shape`) work.

---

## Phase 6: US5 — Creating a SQL Collector (Priority: P1)

**Goal**: A user can write a SQL Collector that joins two upstream Collectors using only this page.

**Independent Test**: Navigate to `/docs/how-to/create-sql-collector/`. Verify: the page explains how SQL Collectors differ from standard Collectors, how upstream inputs are declared, the SQL dialect (SQLite via sql.js), and contains a worked example joining two Collectors.

- [x] T015 [US5] Write `docs/docs/how-to/create-sql-collector.md`: intro explaining what makes a SQL Collector different (no Python script body, SQL query instead); YAML schema for SQL Collector type (all fields, highlighting differences from standard Collector); upstream input declaration syntax (how to reference other Collectors as named tables); SQL dialect notes (SQLite-compatible, available functions, row limits, no DDL); complete worked example: two upstream Collector inputs + a `SELECT ... JOIN ...` query producing a new result set; result shape (same as standard Collector: list of dicts); common errors admonition (undefined table name, unsupported SQL syntax, circular dependency)

**Checkpoint**: Page renders at `/docs/how-to/create-sql-collector/`. YAML and SQL code blocks are syntax-highlighted.

---

## Phase 7: US6 — Loading Secrets (Priority: P1)

**Goal**: A user can configure and use a secret in a Collector without the value appearing in YAML or logs.

**Independent Test**: Navigate to `/docs/how-to/load-secrets/`. Verify: env var sourcing is documented, `secrets["KEY"]` reference syntax is shown in a code example, missing-secret behaviour is described, and security guarantees are stated.

- [x] T016 [US6] Write `docs/docs/how-to/load-secrets.md`: what Secrets are (link to concept page); where secrets are defined (environment variables on the host; note on future secrets-backend support); the reference syntax inside a Collector script (`secrets["MY_API_KEY"]`); a complete example Collector that calls an authenticated API using a secret; what happens when a secret is missing (collect fails with a named error, not silently); security section: secret values are never written to YAML, never logged, never included in Dashboard output; admonition warning against hardcoding secrets in the script body

**Checkpoint**: Page renders at `/docs/how-to/load-secrets/`. Python code block showing `secrets["KEY"]` usage is syntax-highlighted.

---

## Phase 8: US7 — Creating a Dashboard (Priority: P1)

**Goal**: A user can create a working Dashboard YAML that displays Collector data using only this page.

**Independent Test**: Navigate to `/docs/how-to/create-dashboard/`. Verify: full Dashboard YAML schema is documented, Collector reference syntax is shown, column definitions are covered, a complete worked example is present.

- [x] T017 [US7] Write `docs/docs/how-to/create-dashboard.md`: prerequisites section (working Collector, link to create-collector); full YAML schema as a table (every field in `backend/src/models/dashboard.py` — required/optional, type, description); Collector reference syntax (single Collector and multiple Collector patterns); column definition section (name, type options, display options); complete end-to-end worked example: a Dashboard YAML referencing an existing Collector with 3+ columns; expected result when synced (appears in sidebar, data renders); common errors admonition (Collector not found, column name mismatch, invalid type)

**Checkpoint**: Page renders at `/docs/how-to/create-dashboard/`. YAML code blocks are syntax-highlighted. Table of schema fields is correct.

---

## Phase 9: US8 — Using the UI (Priority: P2)

**Goal**: A user understands every interactive element of the Chart-Monitor UI from the docs alone.

**Independent Test**: Navigate through all 7 UI sub-pages. Verify each covers its topic with enough detail that a user who has never opened the app can operate it: sidebar search, column filter menu steps, SQL filter mode switch, sync modal, theme toggle.

- [x] T018 [P] [US8] Write `docs/docs/ui/index.md`: UI layout overview with labelled ASCII diagram showing header / sidebar / main content / SQL panel; one-sentence description of each area; links to each sub-page
- [x] T019 [P] [US8] Write `docs/docs/ui/sidebar-and-navigation.md`: dashboard list rendering; search box (type to filter); selecting a dashboard (click, keyboard); loading state; empty sidebar (no dashboards configured)
- [x] T020 [P] [US8] Write `docs/docs/ui/column-filter-and-sort.md`: how to open the per-column menu (click column header arrow); multi-value checkbox filter; search within the filter menu; applying a filter (active-filter dot indicator on header); clearing a single column's filter; clearing all filters (clear-all button); single-column sort (ascending/descending toggle); interaction between sort and filter
- [x] T021 [P] [US8] Write `docs/docs/ui/sql-filter.md`: opening the SQL panel; the `data` table reference; writing a `SELECT` query; running the query (Run SQL button); filter mode switching (column filter mode vs SQL filter mode, last-applied-wins); error display; clearing the SQL filter; limitations (SQLite dialect, ephemeral — result lost on dashboard switch)
- [x] T022 [P] [US8] Write `docs/docs/ui/data-amount-and-paging.md`: how many rows are shown (default, max); scroll behaviour for large result sets; row count display in the UI; performance note for very large Collector outputs
- [x] T023 [P] [US8] Write `docs/docs/ui/sync-and-refresh.md`: manual sync button (sidebar bottom); sync secret modal (entering `SYNC_SECRET`, "Remember me" checkbox); sync success / failure feedback; auto-refresh / polling interval (how often data refreshes automatically); disconnected banner (what it means, what to do); reconnecting banner
- [x] T024 [P] [US8] Write `docs/docs/ui/theme-and-settings.md`: dark/light toggle button in header; persistence in `localStorage`; how the theme affects the docs page (`prefers-color-scheme` default); keyboard accessibility of the toggle

**Checkpoint**: All 7 UI pages render. Navigation tabs and ToC entries are present on each page.

---

## Phase 10: US9 — How It Works (Priority: P3)

**Goal**: A power user can trace the full data flow from a Git commit to a rendered Dashboard row.

**Independent Test**: Navigate through all 6 internals pages. Verify: the architecture overview names every component, each sub-page covers its component's role, and the end-to-end flow page connects all sub-pages into a coherent narrative with a flow diagram.

- [x] T025 [P] [US9] Write `docs/docs/internals/index.md`: high-level architecture map listing every component (Git repo, poller, YAML parser, Collector engine, RestrictedPython sandbox, DuckDB SQL layer, FastAPI, sql.js WASM, Dashboard renderer, URL state manager) with one-line role descriptions; links to each detailed sub-page
- [x] T026 [P] [US9] Write `docs/docs/internals/gitops-sync.md`: how the backend polls the Git repo (interval, SSH authentication); what "sync" means (pull latest, write to local store path); the manual sync endpoint (`POST /api/v1/sync`); what triggers a re-render in connected browser clients; deploy key security model
- [x] T027 [P] [US9] Write `docs/docs/internals/collector-execution.md`: YAML parsing and model validation (Pydantic); Collector model → `executor.py` pipeline; RestrictedPython sandbox setup (what is allowed, what is blocked, why); script execution lifecycle; result extraction and type coercion; error handling (script exception → surfaced as Collector error, not crash)
- [x] T028 [P] [US9] Write `docs/docs/internals/sql-layer.md`: two distinct SQL contexts — (1) backend DuckDB used by SQL Collectors at collect time (server-side, ephemeral per `collect()` call), (2) frontend sql.js WASM used by the UI SQL filter panel (client-side, ephemeral per query, no server call); how data crosses the boundary (JSON over REST); why two separate engines are used; limitations of each
- [x] T029 [P] [US9] Write `docs/docs/internals/dashboard-rendering.md`: Dashboard YAML → column schema validation; data binding (Collector output rows → typed table rows); filter pipeline (column filters object vs SQL result, last-applied-wins logic, `filterMode` state); sort pipeline (single-column, stable sort); URL state serialisation (`URLSearchParams` encoding of active filters and sort); re-render triggers
- [x] T030 [US9] Write `docs/docs/internals/data-flow-end-to-end.md`: full annotated ASCII flow diagram covering one complete request cycle (user opens Dashboard → browser fetches `/api/v1/collect/{name}` → backend runs Collector → optional SQL Collector → JSON response → frontend deserialises → applies filters/sort → renders table rows); prose walkthrough of each step cross-referencing the detailed sub-pages; "What is persisted vs recomputed" summary table

**Checkpoint**: All 6 internals pages render. ASCII flow diagram in `data-flow-end-to-end.md` is legible in both light and dark themes.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Finalise integration, verify all quickstart scenarios, and confirm FR compliance.

- [x] T031 Run `cd docs && mkdocs build --strict` — zero warnings, zero errors; fix any broken internal links or missing nav entries
- [x] T032 [P] Verify all 7 quickstart scenarios from `specs/008-in-app-docs/quickstart.md` pass: docs load at `/docs`, Swagger at `/api/docs`, deep links work, "Docs" link in header, "Docs" link on GitOps-unconfigured page, dark mode, MkDocs dev server
- [x] T033 [P] Verify FR-004/FR-005: open at least 5 deep links (`/docs/how-to/create-collector/#return-shape`, etc.) — each scrolls to the correct heading and the URL fragment updates
- [x] T034 [P] Verify FR-006: scroll each multi-section page manually — the ToC active entry updates to track the visible section
- [x] T035 [P] Verify FR-007: resize viewport below 960px — content tree collapses to Material's mobile drawer; verify it is accessible via the hamburger toggle
- [x] T036 [P] Verify FR-016: toggle dark mode in Material — all prose, code blocks, tables, and admonitions render with adequate contrast
- [x] T037 [P] Verify FR-024: inspect code blocks on `create-collector.md`, `create-sql-collector.md`, and `data-flow-end-to-end.md` — YAML, Python, bash, and SQL blocks each show distinct syntax colouring; no CDN requests in browser network tab
- [x] T038 Update `specs/008-in-app-docs/checklists/requirements.md` — mark all items as passing post-implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (MkDocs build must work first)
- **Phase 3–8 (US2–US7, P1 stories)**: Depend on Phase 2; can proceed in parallel with each other
- **Phase 9 (US8, P2)**: Depends on Phase 1 only (UI pages reference no other docs pages); can run in parallel with P1 stories
- **Phase 10 (US9, P3)**: Depends on Phase 2 (references concept and how-to pages in prose); can run after Phase 2
- **Phase 11 (Polish)**: Depends on all content phases complete

### User Story Dependencies

- **US2–US7 (P1)**: All independent of each other — content-only, different files
- **US8 (P2)**: Independent — no prose cross-dependencies on P1 pages (links only)
- **US9 (P3)**: References P1 concept/how-to pages by name in prose — write after P1 pages exist, or use placeholder links

### Within Each Phase

- Tasks marked `[P]` within the same phase touch different files and can run in parallel
- `T030` (end-to-end flow page) depends on T025–T029 existing so cross-references are accurate

### Parallel Opportunities

All content-writing tasks in Phases 3–10 (`T010`–`T029`) touch different Markdown files and can run fully in parallel once Phase 2 is complete.

---

## Parallel Example: Content Writing (Phases 3–10)

```
After T009 (index.md) is done, launch all of these together:

T010  getting-started/connect-git.md
T011  concepts/collectors.md
T012  concepts/dashboards.md
T013  concepts/secrets.md
T014  how-to/create-collector.md
T015  how-to/create-sql-collector.md
T016  how-to/load-secrets.md
T017  how-to/create-dashboard.md
T018  ui/index.md
T019  ui/sidebar-and-navigation.md
T020  ui/column-filter-and-sort.md
T021  ui/sql-filter.md
T022  ui/data-amount-and-paging.md
T023  ui/sync-and-refresh.md
T024  ui/theme-and-settings.md
T025  internals/index.md
T026  internals/gitops-sync.md
T027  internals/collector-execution.md
T028  internals/sql-layer.md
T029  internals/dashboard-rendering.md

Then T030 (data-flow-end-to-end.md) after T025–T029 exist.
```

---

## Implementation Strategy

### MVP (US1 + US2 only — Phases 1–3)

1. Complete Phase 1: Setup (T001–T008) — MkDocs wired, Swagger moved, "Docs" link added
2. Complete Phase 2: Foundational (T009) — landing page live
3. Complete Phase 3: US2 (T010) — Git connection guide live
4. **STOP and VALIDATE**: Build docs, open `/docs`, verify Git guide is reachable and correct
5. Ship MVP — users can now find setup instructions inside the product

### Incremental Delivery

1. Phases 1–2 → infrastructure done, landing page live
2. Phase 3 (T010) → Git setup guide live
3. Phases 4–8 (T011–T017, all P1) → full conceptual + how-to coverage live
4. Phase 9 (T018–T024, P2) → UI guide live
5. Phase 10 (T025–T030, P3) → internals/architecture live
6. Phase 11 (T031–T038) → polish and FR validation complete

---

## Notes

- `[P]` tasks = different files, no cross-dependencies — safe to run in parallel
- All content tasks (T010–T030) are Markdown authoring — no code changes
- Only T005, T006 modify backend Python; T007, T008 modify `index.html`; T002, T003 modify `pyproject.toml`/`.gitignore`
- Run `mkdocs build --strict` after every batch of content tasks to catch broken links early
- Material theme's `toc.integrate` feature embeds the ToC into the right-side nav column — satisfies FR-003 (content tree) automatically
- Material theme's built-in `search` plugin satisfies FR-022 (in-page search) automatically
- `permalink: true` on headings satisfies FR-004/FR-005 (deep-link anchors) automatically
