# Quickstart: Per-Column Filter Menu

**Branch**: `007-column-filter-menu` | **Phase**: 1 | **Date**: 2026-04-12

## What Changes

This is a **frontend-only** feature. No backend changes, no new dependencies, no new files.

| File | Change Type | Summary |
|------|-------------|---------|
| `frontend/src/app.js` | Modify | Replace global filter + sort with per-column menus; relocate SQL to bottom; add URL state sync; add clear-all; add filter mode badge |
| `frontend/src/index.html` | Modify | Remove filter input from top bar; add SQL panel below table; add filter-mode badge container |
| `frontend/src/styles.css` | Modify | Add column menu styles, filter mode badge styles, active column header indicator |

## Files NOT Changed

- All backend files (`backend/src/`) — no changes.
- `frontend/src/assets/` — sql.js WASM stays as-is.
- Any YAML dashboard configs.

## Dev Setup

No new install steps. Serve the frontend as usual:

```bash
# Backend (if needed for real data)
cd backend && uvicorn src.main:app --reload

# Frontend — open directly or use any static server
# e.g., open frontend/src/index.html in a browser
# or: python -m http.server 3000 --directory frontend/src
```

## Manual Testing Checklist

### Column Sort
- [ ] Click any column header → menu opens with Sort button
- [ ] Click Sort → table sorts ascending, sort indicator (▴) appears on header
- [ ] Click Sort again → table sorts descending (▾)
- [ ] Open a different column's menu, click Sort → previous column's sort clears

### Column Value Filter
- [ ] Open column menu → value list shows all distinct values from full dataset
- [ ] Check one value → table shows only matching rows
- [ ] Check multiple values → table shows rows matching any of the selected values (OR)
- [ ] Open a second column's menu, check a value → both column filters apply (AND)
- [ ] Uncheck all values in a column → that column's filter clears

### Value Search (inside menu)
- [ ] Type in search box → value list narrows in real-time
- [ ] Clear search box → full value list returns
- [ ] Check a value while search is active → value stays checked after clearing search

### SQL at Bottom
- [ ] SQL editor is visible at the bottom of the page, not the top
- [ ] Type a valid SQL query, click "▶ Run SQL" → table shows SQL results
- [ ] Filter mode badge updates to "SQL filter active"
- [ ] Apply a checkbox filter after SQL → table switches to column filter results
- [ ] Filter mode badge updates to "Column filters active"

### Clear All Filters
- [ ] Apply some checkbox filters and a sort → click "Clear all filters" → table resets to full unfiltered view
- [ ] Run SQL → click "Clear all filters" → SQL results cleared, column filter mode restored

### URL State
- [ ] Apply a filter → copy the URL → open in a new tab → same filter state restored
- [ ] Refresh the page with active filters → state survives the refresh
- [ ] Apply SQL filter → URL contains `sql_mode=1&sql=...`

### Edge Cases
- [ ] Column with all null values → value list shows "(empty)" entry
- [ ] Search term with no matches → "No values match" message shown in menu
- [ ] Invalid SQL → error message shown below SQL editor, table unchanged
- [ ] Click outside open menu → menu closes, filter unchanged

## Key State Variables (for debugging in browser console)

```js
columnFilters       // { colName: Set<string> } — active checkbox selections
filterMode          // 'column' | 'sql'
tableState          // { sortColumn, sortDirection, currentPage, pageSize }
rawData             // { columns, rows } — full dataset from backend
_sqlResultData      // { columns, rows } | null — last SQL result
```
