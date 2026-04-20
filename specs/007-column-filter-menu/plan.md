# Implementation Plan: Per-Column Filter Menu

**Branch**: `007-column-filter-menu` | **Date**: 2026-04-12 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/007-column-filter-menu/spec.md`

## Summary

Replace the existing global text filter input with per-column contextual menus that expose sort, value-checkbox filtering, and a search-within-values box. Relocate the SQL editor to the bottom of the page. Add a filter mode badge, a "Clear all filters" button, and URL-encoded state persistence. All logic is implemented client-side in `frontend/src/app.js` with supporting CSS in `styles.css` — no backend changes required.

## Technical Context

**Language/Version**: Vanilla JS (ES6+)  
**Primary Dependencies**: sql.js (already bundled as `frontend/src/assets/sql-wasm.*`) — no new dependencies  
**Storage**: `URLSearchParams` + `history.replaceState()` (browser-native, no external storage)  
**Testing**: Manual browser testing per `quickstart.md` checklist  
**Target Platform**: Desktop browser (Chrome/Firefox/Edge, desktop-first per Constitution §V)  
**Performance Goals**: Menu open + values render <300ms; search filter <100ms; table re-render <500ms  
**Constraints**: Pure Vanilla JS — no frameworks, no new npm packages, no backend changes  
**Scale/Scope**: Up to 1,000 distinct values per column; overall rows capped by `maxDataValue` (default 10,000)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Dynamic Data Engine | ✅ Pass | Enhances data presentation; does not alter extraction pipeline |
| II. Storage Agnostic & GitOps First | ✅ Pass | Frontend-only; no storage layer changes |
| III. Strict Typing & Clean Code | ✅ Pass | Vanilla JS per existing frontend convention; clean code required |
| IV. Secure Execution Sandbox | ✅ Pass | No new script execution surface; SQL still runs in sql.js sandbox |
| V. Vanilla Desktop-First UI | ✅ Pass | Pure HTML/CSS/JS; desktop viewport prioritized in menu layout |

**No violations. No Complexity Tracking entry required.**

## Project Structure

### Documentation (this feature)

```text
specs/007-column-filter-menu/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── ui-contracts.md  ← Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
└── src/
    ├── app.js        ← primary implementation file (all JS changes)
    ├── index.html    ← minor structural changes (SQL moved to bottom, badge added)
    └── styles.css    ← new CSS for column menus, badges, active header indicators

backend/              ← NO CHANGES
tests/                ← NO CHANGES (frontend manual testing only)
```

**Structure Decision**: Single web application (Option 2 — frontend/backend split already in place). All changes confined to `frontend/src/`. Backend is read-only for this feature.

---

## Phase 0: Research Findings

*See [research.md](research.md) for full decisions and rationale.*

| Unknown | Decision | Rationale |
|---------|----------|-----------|
| URL state encoding | `URLSearchParams` with `cf_`, `sort`, `sql`, `sql_mode` key prefixes | Native, readable, shareable |
| Column menu positioning | Single reused `<div>`, `position: fixed`, `getBoundingClientRect()` | Standard Vanilla JS dropdown; handles table scroll |
| Distinct values source | Full `rawData` (not current filtered view) | Per clarification A2; stable and predictable |
| Filter application logic | `columnFilters` (AND across cols, OR within) + orthogonal sort + last-applied-wins mode | Cleanest state model; no complex merge |
| Value search behavior | Filters visible list only; checked-but-hidden items remain checked | Prevents surprising deselection on search clear |

---

## Phase 1: Design Artifacts

### State Changes (from [data-model.md](data-model.md))

**Removed**:
- `tableState.filterText` — global text filter gone
- `_sqlFilterMode` boolean — replaced by `filterMode`

**Added**:
- `columnFilters = {}` — `{ [colName]: Set<string> }`
- `filterMode = 'column'` — `'column' | 'sql'`
- `openMenuColumn = null` — ephemeral, which column menu is open

### UI Function Contracts (from [contracts/ui-contracts.md](contracts/ui-contracts.md))

| Function | Replaces / New | Responsibility |
|----------|---------------|----------------|
| `openColumnMenu(col, thEl)` | New | Open dropdown, populate sort+search+values |
| `closeColumnMenu()` | New | Close dropdown, remove listener |
| `handleColumnSort(col)` | Replaces `handleSort(col)` | Toggle sort, sync URL, re-render |
| `toggleColumnValue(col, val, checked)` | New | Update `columnFilters`, set mode='column', sync URL, re-render |
| `filterMenuValues(text)` | New | Filter visible value list in open menu |
| `executeSqlFilter(sql)` | Unchanged signature | Set `_sqlResultData`, set mode='sql', sync URL, re-render |
| `clearAllFilters()` | New | Full reset, sync URL, re-render |
| `syncStateToUrl()` | New | Encode state to `URLSearchParams` |
| `restoreStateFromUrl()` | New | Parse URL on load, restore state |
| `renderFilterModeBadge()` | New | Returns badge HTML for current mode |

### Layout Changes (from [contracts/ui-contracts.md](contracts/ui-contracts.md))

**Top controls bar** (`.dashboard-controls`):
- Remove: global filter `<input>`, SQL toggle button, SQL `<textarea>` + Run button
- Add: filter mode badge, "Clear all filters" button
- Keep: max-rows input, interval select, Refresh Now button

**Table headers** (`<th>`):
- Each header becomes a clickable button that calls `openColumnMenu(col, this)`
- Active-filtered headers get `.col-header--filtered` class (visual indicator dot)
- Sort indicator moves into the header text (as before)

**Below table** (new `.sql-panel` div):
- SQL textarea + "▶ Run SQL" button + error display
- Always visible when `window._sqlEngine != null`

### New CSS Classes

See [contracts/ui-contracts.md](contracts/ui-contracts.md) CSS section for full list. Key additions:
- `.col-menu` — floating menu container with shadow and z-index
- `.col-menu__values` — scrollable list, max-height 240px
- `.filter-mode-badge` — inline badge, two modifier variants (`--sql`, `--col`)
- `.col-header--filtered` — small dot indicator on filtered column headers
- `.sql-panel` — bottom SQL editor container
