# Research: SQL Collector

## Decision 1: Backend SQL Engine — Python stdlib `sqlite3`

**Decision**: Use Python's built-in `sqlite3` module with in-memory databases.

**Rationale**: Python 3.11+ ships with SQLite 3.39+ which includes JSON1 functions enabled by default. This means `json_text->>'$.path.to.key'` syntax works out of the box — zero additional dependencies. DuckDB was rejected because `con.register()` cannot accept plain Python `list[dict]`.

**Key details**:
- Python 3.11 ships SQLite 3.39.4, Python 3.12 ships SQLite 3.41+
- JSON1 is enabled by default since SQLite 3.38.0 (2022-02-22)
- `->>` operator extracts as SQL primitive types (TEXT, INTEGER, REAL, NULL)
- `->` operator returns JSON representation (useful for nested objects)
- Path syntax: `'$.key'`, `'$.nested.key'`, `'$.array[0].key'`
- Each `collect()` call creates a fresh `:memory:` connection — no persistence

**Pattern for data ingestion** (per user specification):
```python
conn = sqlite3.connect(':memory:')
# Create raw table with single JSON column
conn.execute('CREATE TABLE raw_pods (json_text TEXT)')
# Insert each row as serialized JSON
conn.executemany('INSERT INTO raw_pods VALUES (?)', [(json.dumps(row),) for row in rows])
# Create view that extracts fields via JSON path
conn.execute("""
    CREATE VIEW pods AS
    SELECT json_text->>'$.metadata.name' AS pod_name,
           json_text->>'$.metadata.namespace' AS namespace
    FROM raw_pods
""")
```

**Alternatives considered**:
- DuckDB: Cannot accept `list[dict]` natively — requires pandas/pyarrow (heavy dependencies)
- DuckDB with temp JSON files: File I/O in sandbox is a security concern
- pandas + sqlalchemy: Massive dependency for simple SQL needs

## Decision 2: Frontend SQL Engine — sql.js (bundled WASM)

**Decision**: Use sql.js v1.13 with locally bundled WASM files.

**Rationale**: sql.js compiles SQLite to WebAssembly, providing the same SQL dialect as the backend. Files are downloaded from GitHub releases at build/deploy time — no CDN, no npm.

**Key details**:
- Latest version: sql.js v1.13 (SQLite 3.49, Emscripten 4)
- Download URL: `https://github.com/sql-js/sql.js/releases/download/v1.13.0/sqljs.zip`
- Files: `sql-wasm.js` (~90KB), `sql-wasm.wasm` (~1.5MB)
- Initialization (vanilla, no CDN):
  ```html
  <script src="./assets/sql-wasm.js"></script>
  <script>
    initSqlJs({ locateFile: f => `./assets/${f}` }).then(SQL => {
      const db = new SQL.Database();
      // ... use db
    });
  </script>
  ```

**Alternatives considered**:
- Official SQLite WASM (sqlite.org/wasm): More complex API, larger payload
- CDN delivery: Violates constitution
- npm package: Violates vanilla JS requirement

## Decision 3: JSON Path Translation (dot-notation → SQLite JSON path)

**Decision**: Convert user-facing dot-notation paths to SQLite `$`-prefixed JSON paths at view creation time.

**Rationale**: Users write `view_column("v", "col", "metadata.name")` which is more natural. Internally this becomes `json_text->>'$.metadata.name'` in the CREATE VIEW statement. The translation is a simple string operation: prepend `$.` and the dot-notation maps directly.

**Key details**:
- User writes: `"metadata.name"` → Internal: `'$.metadata.name'`
- User writes: `"status.containerStatuses"` → Internal: `'$.status.containerStatuses'`
- Array indexing not in MVP scope but SQLite supports `'$.array[0]'` for future use

## Decision 4: SQL Safety — SELECT-only Validation

**Decision**: Validate that user SQL queries contain only SELECT statements before execution.

**Rationale**: SQLCollector SQL should be read-only — no INSERT, UPDATE, DELETE, DROP, or DDL. The in-memory database is ephemeral per `collect()` call so mutations wouldn't persist, but validation prevents accidental misuse and aligns with the Secure Execution Sandbox principle.

**Key details**:
- Parse SQL string and reject if it starts with anything other than SELECT/WITH
- The sqlite3 connection is created fresh each `collect()` and closed after — truly ephemeral
- Frontend sql.js also uses ephemeral databases — same safety model
