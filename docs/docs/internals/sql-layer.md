# SQL Layer

Chart-Monitor has **two distinct SQL execution contexts**. This page explains both, why they exist, and how they differ.

---

## Two SQL engines

| | Backend SQL | Frontend SQL |
|---|---|---|
| **Where it runs** | Python backend | Browser (WebAssembly) |
| **Engine** | SQLite (stdlib `sqlite3`) | sql.js (SQLite compiled to WASM) |
| **Purpose** | SQL Collectors — join data from multiple upstream Collectors | UI SQL filter — ad-hoc queries on already-loaded data |
| **When it runs** | At collect time, on every scrape | When the user runs a query in the SQL panel |
| **Data source** | Other Collectors' `collect()` output | The current Dashboard's loaded rows |
| **Persistent?** | No — in-memory SQLite, destroyed after each `collect()` call | No — in-memory, destroyed when the dashboard changes |
| **Results go to** | JSON API response | Rendered table in the UI |

---

## Backend SQL (SQL Collectors)

SQL Collectors use Python's built-in `sqlite3` module to create an **in-memory SQLite database** per `collect()` call:

```
SQLCollector.collect() called
    ↓
init_tables() — register upstream Collectors as tables
    ↓
For each table: run upstream Collector, collect rows
    ↓
Build in-memory SQLite DB:
  • CREATE TABLE raw_pods (json_text TEXT)
  • INSERT ... (JSON-serialised rows)
  • CREATE VIEW pods_view AS SELECT json_text->>'$.name' AS pod_name ...
    ↓
Execute user's SELECT query
    ↓
Return list[dict] results
    ↓
SQLite connection closed, DB destroyed
```

The SQLite DB exists only for the duration of one `collect()` call. Nothing is persisted to disk.

### JSON path extraction

Each row from an upstream Collector is stored as a JSON string in the raw table. Views use `json_text->>'$.path'` (SQLite JSON path syntax) to extract fields into named columns.

---

## Frontend SQL (sql.js)

sql.js is a **WebAssembly build of SQLite** that runs entirely in the browser. No server call is needed for SQL filter queries.

When a user opens a Dashboard:

1. The browser fetches the full row set from `/api/v1/dashboards/{id}/data`
2. If the user types a query and clicks **▶ Run SQL**, `app.js` loads sql.js (lazy-loaded once)
3. A fresh in-memory SQLite DB is created in the browser
4. All Dashboard rows are inserted into a table named `data`
5. The query is executed against `data`
6. The results replace the visible table rows
7. When the user switches to a different Dashboard or clears the filter, the DB is discarded

### Why sql.js instead of server-side filtering?

- **Responsiveness**: No round-trip to the backend — filter results appear immediately
- **Offline capability**: Works even when the backend is temporarily unreachable
- **Separation of concerns**: The backend serves canonical data; the browser can slice and dice it without affecting the underlying data

### sql.js loading

sql.js is bundled as a local WASM file (`frontend/src/assets/sql-wasm.js` + `sql-wasm.wasm`). No CDN is used. The WASM file is loaded once on first use and cached for the session.

---

## Comparison with backend SQL

Both engines use SQLite syntax, but they operate on different data:

| | Backend (`SQLCollector`) | Frontend (SQL filter) |
|---|---|---|
| Input data | Raw rows from upstream Collectors | Styled `CellResult` rows (after Dashboard column extraction) |
| Column names | Field names from Collector dicts | Dashboard column header labels |
| Joins | Join across multiple Collector outputs | Only `data` table available |
| Persistence | None | None |
