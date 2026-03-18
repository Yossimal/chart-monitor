# Tasks: SQL Collector

**Input**: Design documents from `/specs/006-sql-collector/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — gitignore updates and sql.js download script

- [X] T001 Add sql.js asset patterns (`frontend/src/assets/sql-wasm.js`, `frontend/src/assets/sql-wasm.wasm`) and `frontend/src/assets/*.zip` to `.gitignore`
- [X] T002 [P] Create `frontend/scripts/download-sqljs.ps1` — PowerShell script that downloads `sqljs.zip` from `https://github.com/sql-js/sql.js/releases/download/v1.13.0/sqljs.zip`, extracts `sql-wasm.js` and `sql-wasm.wasm` to `frontend/src/assets/`, skips if files already exist (idempotent)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Internal dataclasses and SQLCollector abstract class skeleton — MUST complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add `dataclasses`, `json`, `sqlite3` imports and define `TableDef`, `ViewDef`, `ViewColumnDef` as `@dataclass` classes at module level in `backend/src/models/collector.py` — per data-model.md entity definitions (TableDef: table_name, collector, secrets; ViewDef: view_name, table_name, columns list; ViewColumnDef: column_name, path, json_path computed as `'$.' + path`)
- [X] T004 Add `SQLCollector` abstract class skeleton extending `Collector` in `backend/src/models/collector.py` — private attributes `_tables: dict[str, TableDef]`, `_views: dict[str, ViewDef]`, `_initialized: bool = False`; abstract methods `init_tables()` and `sql()`; empty method stubs for `define_table()`, `define_view()`, `view_column()`, and concrete `collect()` that raises NotImplementedError placeholder

**Checkpoint**: Foundation ready — SQLCollector skeleton exists, user story implementation can begin

---

## Phase 3: User Story 1 - Define Tables and Run SQL Across Collectors (Priority: P1) 🎯 MVP

**Goal**: Dashboard authors can create SQLCollector subclasses, define tables from other collectors, and execute SQL queries that return `list[dict]` results

**Independent Test**: Create a SQLCollector subclass with two test collectors returning flat dicts, run a JOIN query, verify correct result rows

### Implementation for User Story 1

- [X] T005 [US1] Implement `define_table(collector, table_name, secrets=None)` in `backend/src/models/collector.py` — accepts both collector classes and instances, validates table_name uniqueness, stores `TableDef` in `_tables` dict. Raise `ValueError` if table_name already defined
- [X] T006 [US1] Implement `collect()` pipeline in `backend/src/models/collector.py` — calls `init_tables()` once (guarded by `_initialized` flag), validates `sql()` starts with SELECT/WITH (case-insensitive, stripped), collects data from each source collector (instantiate class if needed, pass secrets to `collect()` as kwargs), creates `sqlite3.connect(':memory:')`, creates `raw_{table_name}` tables with single `json_text TEXT` column, inserts rows as `json.dumps(row)`, executes `self.sql()`, builds `list[dict]` from `cursor.description` + `fetchall()`, closes connection
- [X] T007 [US1] Add error handling to `collect()` in `backend/src/models/collector.py` — wrap source collector calls with try/except that re-raises with table name context ("Failed to collect data for table '{name}': {error}"), wrap SQL execution with try/except that includes the SQL query in the error message, raise `ValueError("No tables defined")` if `_tables` is empty after `init_tables()`

**Checkpoint**: SQLCollector works with raw tables — `SELECT json_text->>'$.key' FROM raw_name` queries execute correctly

---

## Phase 4: User Story 2 - View Columns for Nested Data Access (Priority: P2)

**Goal**: Dashboard authors can create views with column-to-JSON-path mappings so SQL queries use friendly column names instead of raw JSON extraction

**Independent Test**: Create a view on a table with nested dict data, define view_column mappings, run SELECT on view and verify flattened values. Verify missing keys resolve to NULL

### Implementation for User Story 2

- [X] T008 [US2] Implement `define_view(view_name, table_name)` and `view_column(view_name, column_name, path)` in `backend/src/models/collector.py` — define_view validates view_name uniqueness and table_name existence in `_tables`, stores `ViewDef` in `_views`; view_column validates view_name existence in `_views`, creates `ViewColumnDef` with `json_path = '$.' + path`, appends to the view's columns list
- [X] T009 [US2] Add CREATE VIEW generation to `collect()` pipeline in `backend/src/models/collector.py` — after creating/populating raw tables, iterate `_views` dict: for each ViewDef build `CREATE VIEW {view_name} AS SELECT {comma-separated: json_text->>'{json_path}' AS {column_name}} FROM raw_{table_name}` and execute it. Missing JSON keys naturally resolve to NULL via SQLite's `->>` operator

**Checkpoint**: SQL queries against views return correct flattened values — `SELECT pod_name, namespace FROM pods_view` works with nested source data

---

## Phase 5: User Story 3 - SQLCollector Used in TableDashboard (Priority: P3)

**Goal**: SQLCollector subclasses work as drop-in replacements in `TableDashboard.getCollector()`, with an example dashboard demonstrating the full integration

**Independent Test**: The example dashboard file loads and renders via the existing pipeline, producing flat SQL result rows for `@dashboardColumn` methods

### Implementation for User Story 3

- [X] T010 [P] [US3] Create test source collectors in `store/test_collectors.py` — `TestPodsCollector(Collector)` returning 3 rows of nested pod-like dicts (metadata.name, metadata.namespace, spec.nodeName), `TestNodesCollector(Collector)` returning 2 rows of nested node-like dicts (metadata.name, metadata.labels.region) — per quickstart.md scenario 1
- [X] T011 [US3] Create example SQL dashboard in `store/sql_example_dashboard.py` — `PodsByRegionCollector(SQLCollector)` with init_tables defining pods/nodes tables and views with view_columns, sql() returning JOIN query; `PodsByRegionDashboard(TableDashboard)` with getCollector returning PodsByRegionCollector instance and @dashboardColumn methods for pod_name, namespace, region — per quickstart.md scenario 2 and contracts/sql-collector-api.md

**Checkpoint**: Example dashboard loads in the app, shows SQL-joined data rendered through @dashboardColumn methods

---

## Phase 6: User Story 4 - Frontend SQL Filter Mode (Priority: P4)

**Goal**: Dashboard viewers can toggle to SQL filter mode, type ad-hoc SQL queries against displayed table data, and see filtered results — all client-side using bundled sql.js

**Independent Test**: Load any dashboard, toggle to SQL mode, enter `SELECT * FROM data WHERE column = 'value'`, verify table shows filtered rows. Toggle back to Simple mode, verify original data restored

### Implementation for User Story 4

- [X] T012 [US4] Run `frontend/scripts/download-sqljs.ps1` to download sql.js v1.13 assets (`sql-wasm.js`, `sql-wasm.wasm`) to `frontend/src/assets/`
- [X] T013 [US4] Add sql.js `<script>` tag and initialization to `frontend/src/index.html` — add `<script src="./assets/sql-wasm.js"></script>` before app.js, add inline init script: `initSqlJs({ locateFile: f => './assets/' + f }).then(SQL => { window._sqlEngine = SQL; }).catch(() => { window._sqlEngine = null; });`
- [X] T014 [US4] Add SQL filter toggle button and SQL input textarea HTML to `frontend/src/index.html` — inside the main content area (near existing filter controls), add a toggle button (Simple/SQL), a hidden SQL input textarea with placeholder `SELECT * FROM data WHERE ...`, and a Run button. Elements use IDs: `sql-filter-toggle`, `sql-filter-input`, `sql-filter-run`, `sql-filter-error`
- [X] T015 [P] [US4] Add SQL filter mode CSS styles to `frontend/src/styles.css` — styles for `.sql-filter-toggle` (active/inactive states), `.sql-filter-input` (monospace textarea), `.sql-filter-error` (red error text), `.sql-filter-bar` (container), transition animations for mode switching
- [X] T016 [US4] Implement SQL filter state management in `frontend/src/app.js` — add state variables `_sqlFilterMode = false`, `_sqlOriginalData = null`; implement `toggleSqlFilterMode()` that switches between Simple/SQL modes, shows/hides appropriate UI elements, and stores original table data before SQL filtering; implement `resetSqlFilter()` that restores original data when switching back to Simple mode
- [X] T017 [US4] Implement `buildSqlDatabase(columns, rows)` and `executeSqlFilter(sqlQuery)` functions in `frontend/src/app.js` — buildSqlDatabase creates sql.js Database, creates `data` table with TEXT columns from table headers, inserts all rows; executeSqlFilter calls buildSqlDatabase, runs user query, extracts results, re-renders table with results, shows error message on failure (including SQL syntax errors), shows empty state if zero rows returned
- [X] T018 [US4] Handle sql.js load failure in `frontend/src/app.js` — if `window._sqlEngine` is null after init, hide the SQL filter toggle button entirely so simple filters remain the only option; add check in `toggleSqlFilterMode()` as guard

**Checkpoint**: Frontend SQL filter works end-to-end — toggle, query, results, error handling, and graceful degradation if WASM fails

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and cleanup

- [X] T019 Validate quickstart.md scenarios 1-4 end-to-end in running application
- [X] T020 Verify all error messages include table/view/query context per SC-004 requirements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2). Core SQL pipeline
- **US2 (Phase 4)**: Depends on US1 (Phase 3). Adds view layer on top of raw tables
- **US3 (Phase 5)**: Depends on US2 (Phase 4). Example dashboard uses views
- **US4 (Phase 6)**: Depends on Setup (Phase 1) only — frontend is independent of backend US1-US3. T012 depends on T002 (download script)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 only — core MVP
- **User Story 2 (P2)**: Depends on US1 — extends the collect() pipeline with views
- **User Story 3 (P3)**: Depends on US2 — example dashboard uses views
- **User Story 4 (P4)**: Independent of backend stories — depends only on Phase 1 setup (download script). Can be developed in parallel with US1-US3

### Within Each User Story

- Models/dataclasses before implementation methods
- Core pipeline before error handling
- Backend implementation before example dashboard

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T010 (test collectors) can run in parallel with T008-T009 (different files)
- T015 (CSS) can run in parallel with T013-T014 (different files)
- US4 (frontend) can run in parallel with US1-US3 (backend) — completely independent codebases

---

## Parallel Example: User Story 4

```bash
# Frontend work can start as soon as Phase 1 is complete:
Task T012: Download sql.js assets
Task T013: Add script tag to index.html
Task T014: Add toggle UI to index.html
Task T015: Add CSS styles (parallel with T013-T014, different file)
Task T016-T018: app.js implementation (sequential, same file)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (.gitignore + download script)
2. Complete Phase 2: Foundational (dataclasses + SQLCollector skeleton)
3. Complete Phase 3: User Story 1 (define_table + collect pipeline)
4. **STOP and VALIDATE**: Test with raw table SQL queries
5. Can demo basic SQL across collectors

### Incremental Delivery

1. Setup + Foundational → skeleton ready
2. Add US1 → raw SQL works → validate
3. Add US2 → views with JSON paths → validate
4. Add US3 → example dashboard → validate with real UI
5. Add US4 → frontend SQL filter → full feature complete

### Parallel Strategy

Backend developer works on US1 → US2 → US3 sequentially.
Frontend developer works on US4 in parallel starting from Phase 1 completion.

---

## Notes

- All backend tasks (T003-T011) modify `backend/src/models/collector.py` — these MUST be sequential
- Frontend tasks (T012-T018) touch 4 different files — some can be parallelized
- sql.js assets are git-ignored and downloaded via script — not committed
- The `->>` SQLite operator extracts JSON values as SQL primitives (TEXT, INTEGER, etc.)
- Missing JSON keys naturally return NULL — no special handling needed in view column extraction
