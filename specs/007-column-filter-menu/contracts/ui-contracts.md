# UI Contracts: Per-Column Filter Menu

**Branch**: `007-column-filter-menu` | **Phase**: 1 | **Date**: 2026-04-12

All functions below are additions or modifications to `frontend/src/app.js`.
No backend API changes are required for this feature.

---

## Column Menu Lifecycle

### `openColumnMenu(colName: string, thEl: HTMLElement): void`
Opens the column menu for the given column, anchored below `thEl`.

- Closes any previously open menu first.
- Populates the menu with:
  - **Sort button** — labelled "Sort ▴" (asc active) / "Sort ▾" (desc active) / "Sort" (inactive)
  - **Search input** — empty on open, `oninput` triggers `filterMenuValues()`
  - **Value list** — one checkbox per distinct value from `rawData` (full dataset), checked if value is in `columnFilters[colName]`
- Sets `openMenuColumn = colName`.
- Positions menu via `position: fixed` using `thEl.getBoundingClientRect()`.
- Attaches outside-click listener to `document` (one-time, removed when menu closes).

**Pre-conditions**: `rawData.columns` is non-empty.  
**Post-conditions**: `#col-menu` is visible and populated; `openMenuColumn === colName`.

---

### `closeColumnMenu(): void`
Closes the currently open column menu.

- Adds `hidden` class to `#col-menu`.
- Sets `openMenuColumn = null`.
- Removes the outside-click listener.

**Post-conditions**: `#col-menu` is hidden; `openMenuColumn === null`.

---

## Sort

### `handleColumnSort(colName: string): void`
Replaces existing `handleSort(colName)`.

- If `tableState.sortColumn === colName`: toggles `sortDirection` between `'asc'` and `'desc'`.
- Otherwise: sets `sortColumn = colName`, `sortDirection = 'asc'`.
- Resets `tableState.currentPage = 0`.
- Does NOT change `filterMode`.
- Calls `syncStateToUrl()`, then `renderProcessedTable()`.
- Updates the sort button label inside the open menu (if same column).

---

## Column Value Filtering

### `toggleColumnValue(colName: string, value: string, checked: boolean): void`
Called when a checkbox in the column menu is toggled.

- If `checked`: add `value` to `columnFilters[colName]` (create Set if absent).
- If `!checked`: remove `value` from `columnFilters[colName]`; delete key if Set becomes empty.
- Sets `filterMode = 'column'`.
- Resets `tableState.currentPage = 0`.
- Calls `syncStateToUrl()`, then `renderProcessedTable()`.
- Does NOT close the menu — user may want to check multiple values.

---

### `filterMenuValues(searchText: string): void`
Called on `oninput` of the column menu's search box.

- Filters the visible value list inside `#col-menu` to show only items whose label contains `searchText` (case-insensitive).
- Does NOT modify `columnFilters` — only affects what's visible in the menu.
- Already-checked items that are hidden by the search remain checked.

---

## SQL (relocated to bottom)

### `executeSqlFilter(sqlQuery: string): void` *(unchanged signature)*
Executes a SQL query against `rawData` using sql.js.

- On success: sets `_sqlResultData`, sets `filterMode = 'sql'`.
- On error: displays error message, does NOT change `filterMode` or `_sqlResultData`.
- Calls `syncStateToUrl()`, then `renderProcessedTable()`.

---

## Clear All Filters

### `clearAllFilters(): void`
Resets all active filters.

- `columnFilters = {}`
- `tableState.sortColumn = null`
- `tableState.sortDirection = 'asc'`
- `tableState.currentPage = 0`
- `_sqlResultData = null`
- `filterMode = 'column'`
- Calls `syncStateToUrl()`, then `renderProcessedTable()`.

---

## URL State Sync

### `syncStateToUrl(): void`
Encodes current filter/sort/SQL state into `URLSearchParams` and calls `history.replaceState()`.

- Writes `sort`, `cf_<colName>`, `sql_mode`, `sql` params as defined in data-model.md.
- Omits keys whose values are empty/default (clean URLs).

---

### `restoreStateFromUrl(): void`
Called once at boot (after `rawData` is loaded for the first time).

- Parses `window.location.search` via `URLSearchParams`.
- Restores `tableState.sortColumn/sortDirection`, `columnFilters`, `filterMode`, `_sqlResultData` (SQL text only — re-executes if `sql_mode=1`).
- Calls `renderProcessedTable()`.

---

## Filter Mode Badge

### `renderFilterModeBadge(): string` *(returns HTML snippet)*
Returns a `<div class="filter-mode-badge ...">` element indicating the active mode.

- `filterMode === 'sql'` and `_sqlResultData != null` → `"SQL filter active"` (highlighted style)
- `filterMode === 'column'` and `activeColumnFilterCount > 0` → `"Column filters active (N columns)"` 
- Otherwise → `"No active filter"` (muted style)

Included in the output of `renderProcessedTable()`.

---

## HTML Layout Changes

### `index.html` — SQL editor section relocated

**Before**: SQL toggle button + SQL textarea in the top `.dashboard-controls` bar.  
**After**:
- Top bar contains: **filter mode badge** + **"Clear all filters" button** + max-rows input + refresh interval + Refresh Now button.
- SQL section (textarea + "▶ Run SQL" button + error display) is rendered **below the table card**, always visible when `window._sqlEngine != null`.

---

## CSS Classes (new, in `styles.css`)

| Class | Element | Purpose |
|-------|---------|---------|
| `.col-menu` | `<div>` | Floating column menu container |
| `.col-menu__sort-btn` | `<button>` | Sort button inside menu |
| `.col-menu__search` | `<input>` | Search box inside menu |
| `.col-menu__values` | `<ul>` | Scrollable value list (max-height: 240px, overflow-y: auto) |
| `.col-menu__value-item` | `<li>` | One row: checkbox + label |
| `.col-menu__empty` | `<li>` | "No values match" empty state |
| `.filter-mode-badge` | `<div>` | Active filter mode indicator |
| `.filter-mode-badge--sql` | modifier | SQL mode highlight style |
| `.filter-mode-badge--col` | modifier | Column filter active style |
| `.col-header--filtered` | `<th>` | Visual dot/indicator on headers with active filters |
| `.sql-panel` | `<div>` | Bottom SQL editor container |
