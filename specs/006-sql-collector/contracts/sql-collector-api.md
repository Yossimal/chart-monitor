# Contract: SQLCollector Python API

## Interface: SQLCollector (abstract class)

**Location**: `backend/src/models/collector.py`
**Extends**: `Collector`

### User-facing API

```python
from src.models.collector import SQLCollector, Collector

class MySQLDashboardCollector(SQLCollector):
    """User extends this class."""

    def init_tables(self) -> None:
        """Define tables, views, and view columns."""
        self.define_table(PodsCollector, "pods", secrets={"K8S_TOKEN": token})
        self.define_table(NodesCollector(), "nodes")

        self.define_view("pods_view", "pods")
        self.view_column("pods_view", "pod_name", "metadata.name")
        self.view_column("pods_view", "namespace", "metadata.namespace")
        self.view_column("pods_view", "node_name", "spec.nodeName")

        self.define_view("nodes_view", "nodes")
        self.view_column("nodes_view", "node_name", "metadata.name")
        self.view_column("nodes_view", "region", "metadata.labels.region")

    def sql(self) -> str:
        return """
            SELECT p.pod_name, p.namespace, n.region
            FROM pods_view p
            JOIN nodes_view n ON p.node_name = n.node_name
            WHERE p.namespace != 'kube-system'
            ORDER BY n.region
        """
```

### Method Signatures

#### `define_table(collector, table_name, secrets=None)`
- `collector: type[Collector] | Collector` — Collector class or instance
- `table_name: str` — Name for the logical table (alphanumeric + underscore)
- `secrets: dict[str, str] | None` — Optional secrets dict passed to collector's `collect()`
- **Raises**: `ValueError` if `table_name` already defined

#### `define_view(view_name, table_name)`
- `view_name: str` — Name for the SQL view
- `table_name: str` — Must reference a previously defined table
- **Raises**: `ValueError` if `view_name` already defined or `table_name` not found

#### `view_column(view_name, column_name, path)`
- `view_name: str` — Must reference a previously defined view
- `column_name: str` — SQL column alias
- `path: str` — Dot-notation path into the JSON row (e.g., `"metadata.name"`)
- **Raises**: `ValueError` if `view_name` not found

#### `init_tables()` [abstract]
- User implements to call `define_table`, `define_view`, `view_column`
- Called once on first `collect()` invocation

#### `sql()` [abstract]
- Returns the SQL query string
- Must be a SELECT or WITH statement (read-only)

#### `collect(**kwargs)` [concrete, overrides Collector]
- Executes the full pipeline: init_tables → collect sources → create DB → run SQL
- Returns `list[dict[str, Any]]`

## Integration with TableDashboard

```python
class MyDashboard(TableDashboard):
    def getCollector(self) -> Collector:
        return MySQLDashboardCollector()

    @dashboardColumn("Pod Name")
    def pod_name(self, row: dict) -> CellResult:
        # row is a flat dict from SQL result — no nesting
        return {"value": row["pod_name"], "style": ""}
```

The `@dashboardColumn` methods receive flat dicts (SQL result rows), not nested collector data. This simplifies dashboard column definitions.

## Contract: Frontend SQL Filter

**Location**: `frontend/src/app.js`

### Behavior

1. A toggle button switches between "Simple" and "SQL" filter modes
2. In SQL mode, a text input replaces per-column filter inputs
3. Table data is loaded into an in-memory sql.js database as table `data`
4. Column names are derived from the table headers
5. User enters SELECT query, presses Enter/button to execute
6. Table re-renders with query results
7. Toggling back restores original data

### sql.js Initialization

```javascript
// sql-wasm.js loaded via <script> tag from local assets
initSqlJs({ locateFile: f => `./assets/${f}` }).then(SQL => {
    window._sqlEngine = SQL;
});
```

### Data Loading

```javascript
// columns: ["pod_name", "namespace", "status"]
// rows: [{"pod_name": "x", "namespace": "y", "status": "Running"}, ...]
const db = new window._sqlEngine.Database();
const cols = columns.map(c => `"${c}" TEXT`).join(', ');
db.run(`CREATE TABLE data (${cols})`);
for (const row of rows) {
    const vals = columns.map(c => row[c] ?? null);
    db.run(`INSERT INTO data VALUES (${columns.map(() => '?').join(',')})`, vals);
}
```
