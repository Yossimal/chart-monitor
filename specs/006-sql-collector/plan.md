# Implementation Plan: SQL Collector

**Branch**: `006-sql-collector` | **Date**: 2026-03-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-sql-collector/spec.md`

## Summary

Add `SQLCollector` — an abstract `Collector` subclass that lets dashboard authors define logical tables from other collectors, create views with JSON path mappings, and run SQL queries across their data using Python's stdlib `sqlite3` (in-memory). Additionally, add a frontend SQL filter mode using bundled sql.js that lets dashboard viewers run ad-hoc SQL queries against displayed table data client-side.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), Vanilla JS (Frontend)
**Primary Dependencies**: FastAPI, RestrictedPython, sqlite3 (stdlib), sql.js (bundled WASM v1.13)
**Storage**: In-memory SQLite (ephemeral per collect() call, backend), in-memory sql.js (ephemeral per query, frontend)
**Testing**: pytest
**Target Platform**: Linux server (backend), Desktop browser (frontend)
**Project Type**: Web application (monitoring dashboard)
**Performance Goals**: SQL queries against <500 rows should complete in <100ms
**Constraints**: No CDN usage, no npm, sql.js assets downloaded via setup script at build/deploy time
**Scale/Scope**: Typical 1-10 source collectors per SQLCollector, <500 rows per table (enforced by max_data)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Dynamic Data Engine | PASS | SQLCollector extends the data extraction engine with SQL-based transformations |
| II. Storage Agnostic & GitOps First | PASS | In-memory sqlite3, no persistent storage. SQLCollector files live in `store/` (GitOps) |
| III. Strict Typing & Clean Code | PASS (backend) / KNOWN DEVIATION (frontend) | Backend uses strict Python typing. Frontend is vanilla JS — pre-existing project-wide deviation, not introduced by this feature |
| IV. Secure Execution Sandbox | PASS | sqlite3 runs in-memory with SELECT-only validation. No host access. Frontend sql.js is ephemeral |
| V. Vanilla Desktop-First UI | PASS | Vanilla JS + bundled sql.js WASM. No frameworks. Desktop-first filter UI |

**Post-design re-check**: All gates pass. The frontend JS deviation is pre-existing (all prior features use vanilla JS).

## Project Structure

### Documentation (this feature)

```text
specs/006-sql-collector/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── sql-collector-api.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── collector.py          # Add SQLCollector class + internal types (TableDef, ViewDef, ViewColumnDef)
│   └── ...                       # No other backend files modified
└── tests/

frontend/
├── src/
│   ├── app.js                    # Add SQL filter mode (toggle, query execution, state management)
│   ├── index.html                # Add sql.js script tag, SQL filter toggle UI elements
│   ├── styles.css                # Add SQL filter mode styles
│   └── assets/
│       ├── sql-wasm.js           # Downloaded at build/deploy time (git-ignored)
│       └── sql-wasm.wasm         # Downloaded at build/deploy time (git-ignored)
└── scripts/
    └── download-sqljs.ps1        # Setup script to fetch sql.js from GitHub releases

store/
└── sql_example_dashboard.py      # Example SQLCollector dashboard for testing
```

**Structure Decision**: Existing web application structure (backend/ + frontend/). `SQLCollector` is added to the existing `collector.py` file alongside `Collector`. Internal types (`TableDef`, `ViewDef`, `ViewColumnDef`) are defined as dataclasses in the same file to keep the module self-contained.

## Implementation Architecture

### Backend: SQLCollector collect() Pipeline

```
User calls collect()
    │
    ├─ 1. init_tables() [once, on first call]
    │     ├── define_table() → stores TableDef in _tables
    │     ├── define_view() → stores ViewDef in _views
    │     └── view_column() → appends ViewColumnDef to ViewDef.columns
    │
    ├─ 2. Validate sql() → must start with SELECT/WITH
    │
    ├─ 3. For each TableDef:
    │     ├── Instantiate collector (if class, call ())
    │     ├── Call collector.collect(secrets=...) → list[dict]
    │     └── Store rows temporarily
    │
    ├─ 4. Create sqlite3 in-memory connection
    │     ├── For each table: CREATE TABLE raw_{name} (json_text TEXT)
    │     ├── For each table: INSERT rows as json.dumps(row)
    │     └── For each view: CREATE VIEW {name} AS SELECT json_text->>'$.path' AS col, ... FROM raw_{name}
    │
    ├─ 5. Execute sql() query
    │     ├── cursor.execute(sql)
    │     └── Build list[dict] from column descriptions + fetchall()
    │
    └─ 6. Close connection, return results
```

### Frontend: SQL Filter Mode

```
User clicks "SQL" toggle
    │
    ├─ 1. Switch state to SQL mode
    │     ├── Hide per-column filter inputs
    │     └── Show SQL input textarea + run button
    │
    ├─ 2. User types SQL query, clicks Run / presses Enter
    │
    ├─ 3. Build in-memory sql.js database
    │     ├── Create table `data` with columns from table headers
    │     ├── INSERT all current rows
    │     └── Execute user query
    │
    ├─ 4. Render query results in table
    │     └── Replace table body with result rows
    │
    └─ User clicks "Simple" toggle → restore original data
```

### sql.js Asset Setup Script

`frontend/scripts/download-sqljs.ps1`:
- Downloads `sqljs.zip` from `https://github.com/sql-js/sql.js/releases/download/v1.13.0/sqljs.zip`
- Extracts `sql-wasm.js` and `sql-wasm.wasm` to `frontend/src/assets/`
- Skipped if files already exist (idempotent)
- Added to `.gitignore`
