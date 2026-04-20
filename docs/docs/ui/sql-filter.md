# SQL Filter

The SQL filter panel lets you write arbitrary SQL queries to filter and transform the data in the current Dashboard table, directly in your browser.

---

## Opening the SQL panel

The SQL panel is hidden by default. It appears below the table automatically when SQL filter mode is active, or you can activate it by writing and running a query.

---

## Writing a query

The current Dashboard's data is available as a table named **`data`**. Write a `SELECT` query against it:

```sql
SELECT * FROM data WHERE status = 'Running'
```

```sql
SELECT * FROM data WHERE restarts > 5 ORDER BY restarts DESC
```

```sql
SELECT pod_name, status
FROM data
WHERE node LIKE 'prod-%'
  AND status != 'Running'
```

### Column names

Column names in the SQL query must match the **column header labels** from the Dashboard, lowercased and with spaces replaced by underscores. For example:

| Dashboard column header | SQL column name |
|------------------------|-----------------|
| `Pod Name` | `pod_name` |
| `Status` | `status` |
| `CPU Usage (%)` | `cpu_usage_(%)` |

!!! tip "Check column names"
    If a query returns no results or an error, hover over a column header to see its exact name as used in the SQL table.

---

## Running the query

Click **▶ Run SQL** or press **Ctrl+Enter** inside the textarea to execute the query.

- If the query is valid, the table updates immediately to show the filtered results
- If the query has an error, a red error message appears below the textarea and the table is not changed

---

## Filter mode badge

When a SQL filter is active, a badge reading **SQL filter** appears in the table toolbar. The column filter badge reads **Column filter** when column filters are active.

Only one mode is active at a time — see [Column Filter & Sort](column-filter-and-sort.md#interaction-with-sql-filter) for details.

---

## Clearing the SQL filter

To clear the SQL filter:

1. Delete the query from the textarea and press **▶ Run SQL** with an empty query, or
2. Click the **Clear all filters** button in the table toolbar

---

## SQL dialect and limitations

The SQL filter runs on **sql.js** — a WebAssembly port of SQLite running entirely in your browser. No data leaves your browser during filtering.

Supported:

- `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, `OFFSET`
- `JOIN` (if you `SELECT * FROM data` and self-join)
- Aggregate functions: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
- String functions: `UPPER`, `LOWER`, `TRIM`, `SUBSTR`, `REPLACE`, `LIKE`
- `CASE WHEN ... THEN ... END`

Not supported:

- `INSERT`, `UPDATE`, `DELETE` — read-only
- Multiple tables (only `data` is available)
- Window functions
- `ATTACH DATABASE`

---

## Performance note

The SQL filter runs in the browser on the full dataset already loaded from the backend. Very large result sets (thousands of rows) may cause a brief pause while sql.js executes the query. The column filter is generally faster for simple value-selection use cases.
