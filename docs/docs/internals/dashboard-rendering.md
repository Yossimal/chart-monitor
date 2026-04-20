# Dashboard Rendering

This page explains how the browser turns an API response into an interactive table, including the filter pipeline, sort pipeline, and URL state management.

---

## Data flow in the browser

```
GET /api/v1/dashboards/{id}/data
        ↓
{ columns: [...], rows: [{col: {value, style}}, ...] }
        ↓
app.js: store raw rows in memory
        ↓
getFilteredAndSortedRows()  ←── column filters OR sql filter (last-applied-wins)
        ↓
sort (single column, stable)
        ↓
renderProcessedTable(columns, filteredRows)
        ↓
DOM: <table> with styled <td> cells
```

---

## Filter pipeline

Two filter modes exist but only one is active at a time. The active mode is tracked by `filterMode` in `app.js`:

### Column filter mode (`filterMode = 'column'`)

An object `columnFilters` maps each column name to the set of values that should be **shown**. A row is included if, for every filtered column, the row's value for that column is in the allowed set.

```javascript
columnFilters = {
  "Status": new Set(["Running", "Pending"]),  // "CrashLoopBackOff" excluded
}
```

Null/empty values are normalised to the sentinel string `"(empty)"` so they can be included or excluded just like any other value.

### SQL filter mode (`filterMode = 'sql'`)

When the user runs a SQL query in the SQL panel, `app.js` loads sql.js, creates an in-memory SQLite DB, inserts all rows, executes the query, and stores the result as the filtered row set. The column filter object is cleared.

### Last-applied-wins

Switching filter modes is implicit:

- Applying a column filter sets `filterMode = 'column'` and clears any SQL result
- Running a SQL query sets `filterMode = 'sql'` and clears `columnFilters`

This ensures the two modes never conflict.

---

## Sort pipeline

Sorting is single-column and stable. State is tracked by `sortColumn` (string or null) and `sortDir` (`'asc'` | `'desc'` | `null`).

The sort runs after filtering, on the already-filtered row set:

```javascript
rows.sort((a, b) => {
    const va = a[sortColumn]?.value ?? "";
    const vb = b[sortColumn]?.value ?? "";
    // numeric sort if both values are numbers, otherwise string sort
    return sortDir === 'asc' ? compare(va, vb) : compare(vb, va);
});
```

Clicking the sort button in a column menu cycles: off → asc → desc → off. Clicking a new column's sort button removes the sort from the previous column.

---

## URL state serialisation

Filter and sort state is encoded in the URL query string so users can bookmark and share specific views:

| State | URL parameter | Format |
|-------|--------------|--------|
| Selected dashboard | `dashboard` | `dashboard=pod_dashboard` |
| Column filters | `cf_<column>` | `cf_Status=Running,Pending` (comma-separated, URL-encoded values) |
| Sort column | `sort` | `sort=Status` |
| Sort direction | `sortDir` | `sortDir=asc` |

State is read from the URL on first load (`restoreStateFromUrl()`) and written back on every change (`syncStateToUrl()`), using `history.replaceState` so the browser history is not polluted.

---

## Re-render triggers

The table re-renders when:

1. New data arrives from the backend (auto-poll or manual refresh)
2. The user applies or clears a filter
3. The user changes the sort column or direction
4. The user selects a different Dashboard

When a new Dashboard is selected, all filter and sort state is reset to defaults before the new data is loaded.

---

## Column menu lifecycle

The per-column filter menu (`#col-menu`) is a single DOM element reused across all columns. Opening a menu:

1. Populates the values list with distinct values from that column's data
2. Positions the element below the clicked column header
3. Attaches a one-time outside-click listener (via `setTimeout(0)`) to close the menu

The outside-click handler checks `openMenuColumn !== colName` before closing to handle re-renders that may have replaced the original trigger element.
