# Data Model: Per-Column Filter Menu

**Branch**: `007-column-filter-menu` | **Phase**: 1 | **Date**: 2026-04-12

## Existing State (unchanged)

```js
// Raw data from the backend API — never mutated by filters
let rawData = { columns: [], rows: [] };
// rawData.rows[i][colName] = { value, display, style }

// Pagination
tableState.currentPage   // int
tableState.pageSize      // int (default 50)

// SQL results (set when SQL executes successfully)
let _sqlResultData = null; // { columns: string[], rows: RowMap[] }
```

## State Changes

### Removed
```js
tableState.filterText    // REMOVED — global text filter is gone
_sqlFilterMode           // REMOVED — replaced by filterMode below
```

### Added / Modified
```js
// Sort state (field moved out of tableState for clarity, or kept in tableState)
tableState.sortColumn    // string | null  — unchanged
tableState.sortDirection // 'asc' | 'desc' — unchanged

// NEW: Per-column value filters
// Map from column name → Set of selected display values
// An absent key or empty Set means no filter on that column
let columnFilters = {};
// Example: { "status": new Set(["Running", "Pending"]), "namespace": new Set(["prod"]) }

// NEW: Active filter mode — 'column' or 'sql'
// Determined by which was last applied (last-applied-wins)
let filterMode = 'column'; // 'column' | 'sql'
```

## Derived Values (computed, not stored)

| Name | Type | Derived From | Purpose |
|------|------|-------------|---------|
| `distinctValues(col)` | `string[]` | `rawData.rows` | All unique display values for a column, sorted A-Z, from full dataset |
| `activeColumnFilterCount` | `int` | `columnFilters` | Number of columns with at least one value selected |
| `hasAnyActiveFilter` | `bool` | `columnFilters`, `filterMode`, `_sqlResultData` | Used to show/hide "Clear all" button |

## State Transitions

```
Initial load
  └─▶ filterMode = 'column', columnFilters = {}, tableState.sortColumn = null

User checks a value checkbox
  └─▶ add to columnFilters[col], filterMode = 'column', re-render

User unchecks all values in a column
  └─▶ delete columnFilters[col] (or keep empty Set), re-render

User clicks Sort on column X
  └─▶ tableState.sortColumn = X, toggle direction (or set asc first time)
      filterMode stays unchanged (sort is orthogonal)

User clicks "Run SQL"
  └─▶ _sqlResultData = result, filterMode = 'sql', re-render

User clicks "Clear all filters"
  └─▶ columnFilters = {}, tableState.sortColumn = null, _sqlResultData = null,
      filterMode = 'column', sync URL, re-render

Dashboard switch (selectDashboard)
  └─▶ Full reset: all of the above + tableState.currentPage = 0

URL load / refresh
  └─▶ Parse URLSearchParams → restore columnFilters, sort, sql/filterMode
```

## URL State Schema

```
sort=<colName>:<asc|desc>
cf_<colName>=<val1>,<val2>,...      (each value URL-encoded; comma-separated)
sql_mode=1                          (only present when filterMode === 'sql')
sql=<url-encoded-sql-string>
```

**Encoding rules**:
- Column names with special characters are URI-component-encoded as the param key suffix.
- Values are individually `encodeURIComponent`-encoded then joined with `,`.
- On parse, split on `,` then `decodeURIComponent` each value.

## Column Menu UI State (ephemeral, not stored)

```js
// Tracks which column menu is open (if any)
let openMenuColumn = null; // string | null — name of the column whose menu is open

// The single reused menu DOM node (created once, reused)
// <div id="col-menu" class="col-menu hidden"> ... </div>
```

This ephemeral state is NOT encoded in the URL — menus are always closed on page load.
