# Feature Specification: SQL Collector

**Feature Branch**: `006-sql-collector`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description: "SQLCollector — a new Collector subclass that lets users define logical tables from other collectors and execute SQL queries across their data, enabling complex joins, aggregations, and transformations."

## Clarifications

### Session 2026-03-18

- Q: Is the frontend sql.js filter mode (client-side SQL against displayed table data) in scope for this feature? → A: Yes — include frontend sql.js filter mode with toggle between simple/SQL filtering in the browser.
- Q: How should sql.js assets be included in the project? → A: Downloaded at build/deploy time via a script, not checked into the repo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Tables and Run SQL Across Collectors (Priority: P1)

A dashboard author wants to combine data from multiple collectors (e.g., pods and GitHub PRs) into a single dashboard using SQL. They create a class that extends `SQLCollector`, define logical tables by referencing other collectors, then write a SQL query that joins or filters across those tables. The `collect()` method executes the SQL and returns the result rows.

**Why this priority**: This is the core value of the feature — enabling SQL-based data manipulation across collectors is the entire purpose of `SQLCollector`.

**Independent Test**: Can be fully tested by creating a `SQLCollector` subclass with two in-memory test collectors, defining tables and views, running a JOIN query, and verifying the returned rows match expected output.

**Acceptance Scenarios**:

1. **Given** a user creates a class extending `SQLCollector` and implements `init_tables()` with `define_table()` calls referencing two existing collectors, **When** the user implements `sql()` returning a JOIN query across those tables, **Then** `collect()` returns the joined result as a list of dicts with the correct columns and values.
2. **Given** a user defines a table from a collector that returns nested dict data, **When** the user defines a view with `view_column()` mapping column names to JSON paths within the dict, **Then** the SQL query can reference those column names and retrieve the correct nested values.
3. **Given** a user defines a table from a collector that requires secrets (via `@secret`), **When** the user passes the `secrets` parameter to `define_table()`, **Then** the source collector receives those secrets during data collection.

---

### User Story 2 - View Columns for Nested Data Access (Priority: P2)

Collectors often return deeply nested dictionaries (e.g., Kubernetes API responses with `metadata.namespace`, `status.containerStatuses[0].ready`). A dashboard author wants to flatten these nested structures into simple column names usable in SQL queries without manually extracting each field.

**Why this priority**: Most real-world collector data is nested. Without views, SQL queries would be limited to flat data only, severely limiting the feature's usefulness.

**Independent Test**: Can be tested by creating a view on a table whose collector returns nested dicts, defining `view_column()` mappings for nested paths, and verifying SQL queries against the view return correct flattened values.

**Acceptance Scenarios**:

1. **Given** a table backed by a collector returning rows like `{"metadata": {"name": "pod-1", "namespace": "default"}}`, **When** the user creates a view with `view_column("pods_view", "pod_name", "metadata.name")` and `view_column("pods_view", "ns", "metadata.namespace")`, **Then** `SELECT pod_name, ns FROM pods_view` returns `[{"pod_name": "pod-1", "ns": "default"}]`.
2. **Given** a view column path points to a key that does not exist in some rows, **When** the SQL query selects that column, **Then** the missing values appear as `NULL` in the result.

---

### User Story 3 - SQLCollector Used in TableDashboard (Priority: P3)

A dashboard author wants to use a `SQLCollector` subclass as the data source for a `TableDashboard`, just like any other `Collector`. The `SQLCollector` is a drop-in replacement — `getCollector()` returns an instance of it, and `@dashboardColumn` methods render the SQL result rows.

**Why this priority**: Integration with the existing dashboard system is essential but builds on top of the core SQL functionality.

**Independent Test**: Can be tested by creating a `TableDashboard` whose `getCollector()` returns a `SQLCollector` subclass instance, and verifying the dashboard renders correctly with the SQL-produced data.

**Acceptance Scenarios**:

1. **Given** a `TableDashboard` class with `getCollector()` returning an instance of a `SQLCollector` subclass, **When** the backend processes the dashboard, **Then** it collects data via the SQL query and renders columns using `@dashboardColumn` methods on the SQL result rows.
2. **Given** a `SQLCollector` subclass is used in a dashboard, **When** `max_data` and `scrape_interval` are set on the subclass, **Then** they are respected as with any other `Collector`.

---

### User Story 4 - Frontend SQL Filter Mode (Priority: P4)

A dashboard viewer wants to run ad-hoc SQL queries against the data already displayed in a dashboard table. The frontend provides a toggle between the existing simple column filters and a SQL filter mode. In SQL mode, the user types a SQL query that runs client-side against the current table data using a bundled SQL engine (sql.js). The table re-renders with the query results.

**Why this priority**: Adds powerful ad-hoc filtering for end users viewing dashboards, but depends on the core backend SQL infrastructure being stable first.

**Independent Test**: Can be tested by loading any existing dashboard with data, switching to SQL filter mode, entering a `SELECT * FROM data WHERE column = 'value'` query, and verifying the table updates to show only matching rows.

**Acceptance Scenarios**:

1. **Given** a dashboard is displayed with table data, **When** the user toggles to SQL filter mode, **Then** a SQL input area appears replacing the simple column filters.
2. **Given** the user is in SQL filter mode, **When** the user types a valid SQL query and executes it, **Then** the table re-renders showing only the query results.
3. **Given** the user is in SQL filter mode, **When** the user types an invalid SQL query, **Then** an error message is shown and the table remains unchanged.
4. **Given** the user is in SQL filter mode, **When** the user toggles back to simple filter mode, **Then** the original unfiltered data is restored and simple column filters reappear.

---

### Edge Cases

- What happens when a source collector's `collect()` raises an error? The `SQLCollector` should propagate the error with context about which table failed.
- What happens when the SQL query is syntactically invalid? A clear error should be raised with the SQL and the parse error message.
- What happens when `define_table()` is called with a collector class vs. an instance? Both should be accepted — classes are instantiated automatically.
- What happens when `view_column()` references a `view_name` that was not created via `define_view()`? An error should be raised immediately.
- What happens when `init_tables()` defines no tables? The SQL query should fail with a clear "no tables defined" error.
- What happens when a JSON path in `view_column()` is invalid or points to a non-existent nested key? The value should resolve to `NULL`.
- What happens when the frontend SQL query returns zero rows? The table should show an empty state with a message.
- What happens when sql.js WASM fails to load? The SQL filter toggle should be hidden and simple filters remain available.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `SQLCollector` abstract class that extends `Collector`.
- **FR-002**: `SQLCollector` MUST expose a `define_table(collector, table_name, secrets=None)` method that registers a logical table backed by another collector's data.
- **FR-003**: `SQLCollector` MUST expose a `define_view(view_name, table_name)` method that creates a logical view associated with one table.
- **FR-004**: `SQLCollector` MUST expose a `view_column(view_name, column_name, path)` method that maps a SQL column name to a dot-notation JSON path within the source data dicts.
- **FR-005**: `SQLCollector` MUST define an abstract `init_tables()` method where users call `define_table`, `define_view`, and `view_column`.
- **FR-006**: `SQLCollector` MUST define an abstract `sql()` method that returns the SQL query string to execute.
- **FR-007**: `SQLCollector`'s `collect()` MUST execute the SQL query against the defined tables/views and return results as `list[dict]`.
- **FR-008**: `SQLCollector` MUST accept both collector classes and collector instances in `define_table()`.
- **FR-009**: When a source collector requires secrets, `define_table()` MUST accept a `secrets` parameter and pass it through to the source collector's `collect()` method.
- **FR-010**: `SQLCollector` MUST support standard SQL operations: SELECT, WHERE, JOIN, GROUP BY, ORDER BY, aggregate functions (COUNT, SUM, AVG, MIN, MAX).
- **FR-011**: View columns with paths pointing to non-existent keys MUST resolve to `NULL`.
- **FR-012**: `SQLCollector` MUST raise clear errors for: invalid SQL syntax, undefined view names in `view_column()`, no tables defined.
- **FR-013**: The frontend MUST provide a toggle to switch between simple column filters and SQL filter mode on any dashboard table.
- **FR-014**: In SQL filter mode, the frontend MUST execute user SQL queries client-side against the current table data using a bundled sql.js engine (no CDN).
- **FR-015**: The sql.js WASM files MUST be served as local assets, not loaded from any external CDN. They are downloaded at build/deploy time via a setup script and NOT checked into the repository.
- **FR-016**: In SQL filter mode, the current table data MUST be loaded into an in-memory SQLite database with a single table named `data`.
- **FR-017**: Switching back to simple filter mode MUST restore the original unfiltered table data.

### Key Entities

- **SQLCollector**: Abstract subclass of `Collector` providing SQL-based data collection from other collectors. Owns tables, views, and view columns.
- **Logical Table**: A named reference to a source collector whose data becomes queryable via SQL. Associated with one collector.
- **Logical View**: A named projection of a logical table that maps SQL column names to JSON paths within the source data. Associated with one table.
- **View Column**: A single column mapping within a view, linking a SQL-friendly column name to a dot-notation path in the source dict.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A dashboard author can create a `SQLCollector` subclass, define tables from two source collectors, and execute a JOIN query — all within a single Python file in the `store/` directory.
- **SC-002**: SQL queries against views with nested JSON paths return correct flattened values for 100% of defined column mappings.
- **SC-003**: `SQLCollector` subclasses work as drop-in replacements for `Collector` in any `TableDashboard.getCollector()` call.
- **SC-004**: Errors from invalid SQL, missing views, or failed source collectors produce user-readable messages that include the relevant table/view/query context.
- **SC-005**: Dashboard viewers can toggle to SQL filter mode, run a WHERE query against displayed data, and see filtered results — all client-side with no backend round-trip.

## Assumptions

- The SQL engine used internally is an implementation detail — the spec is engine-agnostic. The planning phase will determine whether to use Python's built-in `sqlite3` or another engine.
- Collectors referenced in `define_table()` are assumed to be importable from the `store/` directory or `src/` directory.
- The `secrets` parameter in `define_table()` follows the same pattern as the `@secret` decorator — environment variables resolved at call time.
- View columns use dot-notation for path traversal (e.g., `"metadata.name"`). Array indexing is not required for MVP.
- The sql.js assets (`sql-wasm.js`, `sql-wasm.wasm`) are fetched from GitHub releases at build/deploy time via a setup script. They are git-ignored, not committed to the repository.
