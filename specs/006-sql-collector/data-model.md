# Data Model: SQL Collector

## Entities

### SQLCollector (extends Collector)

An abstract `Collector` subclass that executes SQL queries across data from other collectors.

**Attributes**:
- `_tables: dict[str, TableDef]` — Private registry of defined logical tables (keyed by table name)
- `_views: dict[str, ViewDef]` — Private registry of defined logical views (keyed by view name)

**Abstract methods**:
- `init_tables() -> None` — User implements to call `define_table()`, `define_view()`, `view_column()`
- `sql() -> str` — User implements to return the SQL query string

**Concrete methods**:
- `define_table(collector, table_name, secrets=None) -> None` — Registers a logical table
- `define_view(view_name, table_name) -> None` — Creates a logical view associated with a table
- `view_column(view_name, column_name, path) -> None` — Adds a column mapping to a view
- `collect(**kwargs) -> list[dict[str, Any]]` — Executes the full SQL pipeline

**Inherited from Collector**:
- `max_data: int`
- `scrape_interval: int`
- `safe_collect() -> list[dict]`

### TableDef

Internal metadata for a registered logical table.

**Attributes**:
- `table_name: str` — SQL table name (used as `raw_{table_name}` internally)
- `collector: type[Collector] | Collector` — Source collector class or instance
- `secrets: dict[str, str] | None` — Optional secrets to pass to the collector

### ViewDef

Internal metadata for a registered logical view.

**Attributes**:
- `view_name: str` — SQL view name
- `table_name: str` — Associated raw table name
- `columns: list[ViewColumnDef]` — Ordered list of column mappings

### ViewColumnDef

A single column mapping within a view.

**Attributes**:
- `column_name: str` — SQL-friendly column alias
- `path: str` — Dot-notation JSON path (e.g., `"metadata.name"`)
- `json_path: str` — Computed SQLite JSON path (e.g., `"$.metadata.name"`)

## Relationships

```
SQLCollector 1──* TableDef     (via _tables dict)
SQLCollector 1──* ViewDef      (via _views dict)
ViewDef      *──1 TableDef     (via table_name reference)
ViewDef      1──* ViewColumnDef (via columns list)
TableDef     *──1 Collector    (via collector reference)
```

## Data Flow (collect() pipeline)

1. `init_tables()` populates `_tables` and `_views` (called once, on first `collect()`)
2. For each `TableDef`: instantiate collector, call `collect(secrets=...)`, get `list[dict]`
3. Create in-memory `sqlite3` connection
4. For each table: `CREATE TABLE raw_{name} (json_text TEXT)`, INSERT rows as JSON
5. For each view: `CREATE VIEW {name} AS SELECT json_text->>'$.path' AS col, ... FROM raw_{name}`
6. Execute `self.sql()` query
7. Return results as `list[dict]`
8. Close connection

## Validation Rules

- `table_name` must be unique across all `define_table()` calls
- `view_name` must be unique across all `define_view()` calls
- `view_column()` must reference an existing `view_name`
- `define_view()` must reference an existing `table_name`
- `sql()` return value must start with SELECT or WITH (read-only enforcement)
- At least one table must be defined before `collect()` executes
