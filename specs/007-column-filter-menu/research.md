# Research: Per-Column Filter Menu

**Branch**: `007-column-filter-menu` | **Phase**: 0 | **Date**: 2026-04-12

## Decision 1: URL State Encoding Strategy

**Decision**: Encode filter state into `URLSearchParams` with structured keys. On every filter/sort/SQL change, call `history.replaceState()` to update the URL without navigation. On page load, parse these params to restore state.

**Encoding format**:
```
?sort=<colName>:<asc|desc>
&cf_<colName>=<val1>%2C<val2>      (comma-separated, URL-encoded per value)
&sql_mode=1                         (present only when SQL mode is active)
&sql=<url-encoded SQL query>
```

**Rationale**: `URLSearchParams` is native (no deps), produces human-readable URLs, survives refresh, and is shareable. Each filter axis has its own key prefix (`cf_` for column filters, `sort` for sort, `sql`/`sql_mode` for SQL) so partial state is easy to parse and debug.

**Alternatives considered**:
- Base64-encoded JSON blob (`?state=eyJ...`) — simpler to implement but opaque URLs, hard to debug, and breaks when shared across app versions.
- `localStorage` — persists across sessions but isn't shareable and can conflict between tabs.

---

## Decision 2: Column Dropdown Menu Implementation

**Decision**: Render a single floating `<div id="col-menu">` in `<body>`. On column header click: compute `th.getBoundingClientRect()`, set `col-menu`'s `position: fixed; top: <th.bottom>; left: <th.left>`, populate content, show it. Attach a one-time `document` click listener that closes the menu when clicking outside.

**Rationale**: A single reused DOM node avoids per-column menu overhead. `position: fixed` handles table scroll correctly without needing a scroll-offset calculation. The outside-click listener is the standard Vanilla JS dropdown pattern.

**Alternatives considered**:
- `<details>/<summary>` per header — no position control, styling is constrained by browser.
- One `<div>` per column pre-rendered — unnecessary DOM bloat for wide tables.

---

## Decision 3: Distinct Values Computation

**Decision**: At menu open time, iterate `rawData.rows` and extract the display value (`cell.display ?? cell.value ?? ""`) for the target column. Deduplicate with a `Set`, sort alphabetically (case-insensitive), and return as an array. Empty/null values produce a sentinel `"(empty)"` entry.

**Rationale**: Matches spec clarification — distinct values come from the full original dataset, not the current filtered view. Computing at open time (rather than pre-caching) keeps the logic simple and always fresh after a backend data refresh.

**Performance**: For `maxDataValue` rows (default 10,000) and ≤1,000 distinct values, a single-pass Set collection is O(n) and well under 300ms on modern hardware.

**Alternatives considered**:
- Pre-compute and cache on `rawData` change — premature optimization; adds cache invalidation complexity.
- Backend endpoint for distinct values — violates the "frontend-only" constraint from user input.

---

## Decision 4: Filter Application Logic

**Decision**: Maintain two independent filter axes:
1. **Column filter axis**: `columnFilters = { [colName]: Set<string> }` — rows must match selected values in every active column (AND across columns, OR within a column).
2. **Sort axis**: `tableState.sortColumn + sortDirection` — independent of filter, applied after filtering.

Filter mode (`'column'` vs `'sql'`) is determined by which was last applied. The `getFilteredAndSortedRows()` function checks `filterMode`:
- `'column'`: apply `columnFilters`, then sort, then paginate.
- `'sql'`: use `_sqlResultData` directly (no client sort/pagination applied).

**Rationale**: Sort and column filters are orthogonal operations. The last-applied-wins model for column vs SQL mode is the cleanest way to handle the mutual exclusion without complex state merging.

---

## Decision 5: Column Filter Search (Value Search Box)

**Decision**: The search box inside the column menu filters the rendered value list client-side in real-time using `String.includes()` (case-insensitive). It does not affect `columnFilters` — it only controls which checkboxes are visible. Checked values that are hidden by the search remain checked.

**Rationale**: Users expect to be able to narrow the visible list to find a value, check it, then clear the search and see their selection still active. Removing hidden checked values would be surprising behavior.
