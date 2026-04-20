# Create a SQL Collector

A **SQL Collector** joins or transforms data from other Collectors using SQL. Instead of writing Python logic to merge data, you register upstream Collectors as named tables and write a `SELECT` query.

**Prerequisites**: [Create a standard Collector](create-collector.md) · [Understand Collectors](../concepts/collectors.md)

---

## How SQL Collectors differ from standard Collectors

| | Standard Collector | SQL Collector |
|---|---|---|
| Data source | External system (API, DB, file) | Other Collectors |
| Implementation | `collect()` method | `init_tables()` + `sql()` methods |
| Base class | `Collector` | `SQLCollector` |
| Output | `list[dict]` | `list[dict]` (same shape) |
| When it runs | On every scrape | On every scrape (runs upstream Collectors first) |

---

## Anatomy of a SQL Collector

```python
from src.models.collector import SQLCollector
from pods import PodCollector
from nodes import NodeCollector

class PodsByRegion(SQLCollector):

    def init_tables(self):
        # Register upstream Collectors as named tables
        self.define_table(PodCollector, "pods")
        self.define_table(NodeCollector, "nodes")

        # Define a view that extracts fields from the pods table
        self.define_view("pods_view", "pods")
        self.view_column("pods_view", "pod_name", "name")
        self.view_column("pods_view", "node_name", "node")

        # Define a view over the nodes table
        self.define_view("nodes_view", "nodes")
        self.view_column("nodes_view", "node_name", "name")
        self.view_column("nodes_view", "region", "labels.region")

    def sql(self):
        return """
            SELECT p.pod_name, n.region
            FROM pods_view p
            JOIN nodes_view n ON p.node_name = n.node_name
        """
```

---

## Step-by-step

### 1. Import `SQLCollector` and upstream Collectors

```python
from src.models.collector import SQLCollector
from my_collector import MyCollector
```

### 2. Implement `init_tables()`

Call these three methods to define your data schema:

#### `define_table(collector, table_name)`

Registers an upstream Collector as a raw data table.

```python
self.define_table(PodCollector, "pods")
```

| Parameter | Description |
|-----------|-------------|
| `collector` | Collector class (or instance) |
| `table_name` | SQL-safe name (alphanumeric + underscore) |

#### `define_view(view_name, table_name)`

Creates a SQL view over a registered table. The view extracts JSON fields as named columns.

```python
self.define_view("pods_view", "pods")
```

#### `view_column(view_name, column_name, path)`

Adds a column to a view, using dot-notation to reference fields in each row dict.

```python
self.view_column("pods_view", "pod_name", "name")
self.view_column("pods_view", "node", "spec.nodeName")  # nested path
```

### 3. Implement `sql()`

Return a `SELECT` or `WITH` query. Use the **view names** (not the raw table names) as your FROM targets.

```python
def sql(self):
    return "SELECT pod_name, node FROM pods_view WHERE node LIKE 'prod-%'"
```

!!! warning "Read-only queries only"
    Only `SELECT` and `WITH` statements are allowed. `INSERT`, `UPDATE`, `DELETE`, `DROP`, and DDL statements raise a `ValueError` at runtime.

---

## Nested field paths

The `path` parameter in `view_column` supports dot-notation for nested dicts:

| Row dict | Path | Extracted value |
|----------|------|----------------|
| `{"metadata": {"name": "pod-1"}}` | `metadata.name` | `"pod-1"` |
| `{"spec": {"nodeName": "node-a"}}` | `spec.nodeName` | `"node-a"` |
| `{"status": "Running"}` | `status` | `"Running"` |

---

## SQL dialect

SQL Collectors use an **in-memory SQLite database**. Supported features:

- `SELECT`, `WHERE`, `JOIN` (all types), `GROUP BY`, `ORDER BY`, `LIMIT`
- Aggregate functions: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
- String functions: `UPPER`, `LOWER`, `TRIM`, `LENGTH`, `SUBSTR`, `REPLACE`
- `CASE WHEN ... THEN ... END`
- `WITH` (CTEs)
- JSON extraction: `json_extract(col, '$.path')`

Not supported: window functions, stored procedures, DDL, DML.

---

## Common errors

??? failure "Table 'pods' not found"
    You called `define_view('pods_view', 'pods')` before `define_table(PodCollector, 'pods')`. Always call `define_table` first.

??? failure "View 'pods_view' already defined"
    Each view name must be unique within one SQL Collector. Use distinct names.

??? failure "sql() must return a SELECT or WITH statement"
    The `sql()` method returned a non-read statement. Only `SELECT` and `WITH` are allowed.

??? failure "Failed to collect data for table 'pods'"
    The upstream `PodCollector` raised an error. Check that Collector independently first.
