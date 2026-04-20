---
description: "Task list for Per-Column Filter Menu"
---

# Tasks: Per-Column Filter Menu

**Input**: Design documents from `/specs/007-column-filter-menu/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-contracts.md, quickstart.md

**Tests**: Tests were NOT explicitly requested in the spec. Validation is manual via `quickstart.md` (desktop browser). No automated test tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Web app structure (from plan.md §Project Structure): all changes are confined to `frontend/src/`. Backend is untouched.

- `frontend/src/app.js` — all JS logic
- `frontend/src/index.html` — structural layout
- `frontend/src/styles.css` — styling

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inventory the existing top-bar + SQL code paths so the refactor does not drop functionality.

- [x] T001 Audit current global filter input, SQL toggle, and `handleSort` code paths in `frontend/src/app.js` and note every reference (DOM IDs, listeners, state reads). Record findings inline as a short comment block at the top of `app.js` or in a scratch note.
- [x] T002 Audit current top-bar markup (`.dashboard-controls`) and SQL section in `frontend/src/index.html`; list the elements to remove and the insertion points for the new badge, "Clear all filters" button, and bottom `.sql-panel` container.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Replace the old state shape with the new one (`columnFilters`, `filterMode`, `openMenuColumn`) and introduce the reusable column-menu DOM node plus URL sync plumbing. Every user story depends on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Remove `tableState.filterText` and `_sqlFilterMode`; add `columnFilters = {}`, `filterMode = 'column'`, `openMenuColumn = null` at module scope in `frontend/src/app.js` per data-model.md §State Changes.
- [x] T004 Add a `distinctValues(colName)` helper in `frontend/src/app.js` that iterates `rawData.rows`, extracts `cell.display ?? cell.value ?? ""`, substitutes empty values with the sentinel `"(empty)"`, dedupes via `Set`, and returns a case-insensitive A–Z sorted array (research.md Decision 3).
- [x] T005 Add a `getFilteredAndSortedRows()` helper in `frontend/src/app.js` that branches on `filterMode`: for `'column'` applies `columnFilters` (AND across columns, OR within), then sort via `tableState.sortColumn/sortDirection`, then pagination; for `'sql'` returns `_sqlResultData` directly without client sort/pagination (research.md Decision 4).
- [x] T006 Wire `renderProcessedTable()` in `frontend/src/app.js` to consume `getFilteredAndSortedRows()` and drop all references to the removed `filterText`/`_sqlFilterMode` fields.
- [x] T007 Add a single reusable `<div id="col-menu" class="col-menu hidden">` to `frontend/src/index.html` (appended to `<body>`) with inner structure: `.col-menu__sort-btn`, `.col-menu__search`, `.col-menu__values` (empty `<ul>`).
- [x] T008 Remove the global filter `<input>`, SQL toggle button, SQL `<textarea>`, and Run button from the top `.dashboard-controls` in `frontend/src/index.html`; keep max-rows input, interval select, Refresh Now.
- [x] T009 Insert the new bottom `.sql-panel` container (`<textarea>`, "▶ Run SQL" button, error display) below the table card in `frontend/src/index.html` (hidden when `window._sqlEngine == null`).
- [x] T010 Add a placeholder for the filter-mode badge and a "Clear all filters" `<button id="clear-all-filters">` in the top `.dashboard-controls` of `frontend/src/index.html` (wiring comes in Polish phase).
- [x] T011 [P] Add base CSS for `.col-menu`, `.col-menu.hidden`, `.col-menu__sort-btn`, `.col-menu__search`, `.col-menu__values`, `.col-menu__value-item`, `.col-menu__empty` in `frontend/src/styles.css` per ui-contracts.md §CSS Classes (floating container, `position: fixed`, `max-height: 240px` scrollable list).
- [x] T012 [P] Add base CSS for `.sql-panel`, `.filter-mode-badge`, `.filter-mode-badge--sql`, `.filter-mode-badge--col`, `.col-header--filtered` in `frontend/src/styles.css`.
- [x] T013 Implement `openColumnMenu(colName, thEl)` and `closeColumnMenu()` in `frontend/src/app.js`: position via `thEl.getBoundingClientRect()` + `position: fixed`, set/clear `openMenuColumn`, attach/remove one-shot outside-click listener on `document` (FR-013, FR-014, ui-contracts §Column Menu Lifecycle).
- [x] T014 Change each `<th>` render in `frontend/src/app.js` so the header is a clickable button that calls `openColumnMenu(col, this)`; remove the old `handleSort` click binding.
- [x] T015 Implement `syncStateToUrl()` in `frontend/src/app.js` that serializes `sort=<col>:<dir>`, `cf_<col>=<v1,v2,...>` (per-value `encodeURIComponent`), `sql_mode=1`, `sql=<encoded>` into `URLSearchParams` and calls `history.replaceState` (data-model.md §URL State Schema, FR-015).
- [x] T016 Implement `restoreStateFromUrl()` in `frontend/src/app.js`, invoked once after the first `rawData` load; parses params and rehydrates `tableState.sortColumn/Direction`, `columnFilters` (each value `decodeURIComponent`), `filterMode`; if `sql_mode=1` and `sql` is present, re-invokes `executeSqlFilter(sql)`; then calls `renderProcessedTable()`.
- [x] T017 In `selectDashboard` (or equivalent dashboard-switch path) in `frontend/src/app.js`, reset `columnFilters = {}`, `tableState.sortColumn = null`, `tableState.sortDirection = 'asc'`, `_sqlResultData = null`, `filterMode = 'column'`, `tableState.currentPage = 0`, then `syncStateToUrl()` (data-model.md §State Transitions).

**Checkpoint**: Foundation ready — header clicks open an empty-but-positioned menu; filtered/sorted rendering pipeline in place; URL sync round-trips cleanly. All user stories can now be implemented in parallel.

---

## Phase 3: User Story 1 - Sort a Column via Header Menu (Priority: P1) 🎯 MVP

**Goal**: Clicking a column header opens the menu; the Sort button sorts ascending on first click, descending on second click; opening a different column's menu and sorting moves the sort to that column and clears the old one.

**Independent Test**: Open a table, click a header, click Sort → rows reorder ascending; click Sort again → descending; open another column's menu and click Sort → sort transfers, previous sort cleared.

### Implementation for User Story 1

- [x] T018 [US1] Implement `handleColumnSort(colName)` in `frontend/src/app.js`: if `tableState.sortColumn === colName` toggle direction, else set `sortColumn = colName` and `sortDirection = 'asc'`; reset `currentPage = 0`; do NOT mutate `filterMode`; call `syncStateToUrl()` then `renderProcessedTable()` (FR-003, FR-004, ui-contracts §handleColumnSort).
- [x] T019 [US1] In `openColumnMenu()` in `frontend/src/app.js`, populate the `.col-menu__sort-btn` label based on current sort state for the target column (`"Sort ▴"` when asc-active, `"Sort ▾"` when desc-active, `"Sort"` otherwise) and wire its click handler to `handleColumnSort(colName)` followed by re-labelling the button in place.
- [x] T020 [US1] Ensure the sort indicator is still rendered inside the header text in `frontend/src/app.js` (existing indicator relocated if needed) so the sorted column is visible even when its menu is closed.

**Checkpoint**: User Story 1 is fully functional. Sort works via the header menu; second click reverses; switching columns transfers sort. No other filtering capabilities active yet.

---

## Phase 4: User Story 2 - Filter by Column Values via Checkboxes (Priority: P2)

**Goal**: The column menu lists all distinct values for that column as checkboxes (pulled from the full `rawData`, not the current filtered view). Checking values restricts rows to matching values (OR within a column). Multiple columns combine with AND.

**Independent Test**: Open a column menu, check one value → table shows only rows with that value; check another value in same column → OR within column; open another column and check a value → AND across columns; uncheck all → filter clears.

### Implementation for User Story 2

- [x] T021 [US2] In `openColumnMenu()` in `frontend/src/app.js`, populate `.col-menu__values` using `distinctValues(colName)`; render one `<li class="col-menu__value-item">` per value with a `<label><input type="checkbox">` reflecting `columnFilters[colName]?.has(value)` (FR-005, FR-006).
- [x] T022 [US2] Implement `toggleColumnValue(colName, value, checked)` in `frontend/src/app.js`: add/remove `value` in `columnFilters[colName]` (create `Set` if absent; delete key when the set becomes empty); set `filterMode = 'column'`; reset `currentPage = 0`; call `syncStateToUrl()` then `renderProcessedTable()`; do NOT close the menu (FR-008, FR-009, FR-012, ui-contracts §toggleColumnValue).
- [x] T023 [US2] Wire each rendered value checkbox's `change` event in `openColumnMenu()` to `toggleColumnValue(colName, value, e.target.checked)` in `frontend/src/app.js`.
- [x] T024 [US2] Add a visual `.col-header--filtered` class toggle in `renderProcessedTable()` in `frontend/src/app.js` for any column present in `columnFilters` with a non-empty Set (indicator dot per ui-contracts §CSS Classes).
- [x] T025 [US2] In `getFilteredAndSortedRows()` in `frontend/src/app.js`, confirm the `'column'` branch applies multi-column AND / within-column OR correctly against `cell.display ?? cell.value ?? ""` (mirrors `distinctValues` so `"(empty)"` filtering works).

**Checkpoint**: User Stories 1 and 2 both work independently. Sort + column-value filtering can also combine (they are orthogonal axes).

---

## Phase 5: User Story 3 - Search Within Column Value List (Priority: P2)

**Goal**: Typing in the search box at the top of the column menu narrows the visible value checkboxes (case-insensitive substring). Already-checked values that are hidden remain checked and remain in `columnFilters`.

**Independent Test**: Open a column menu with many distinct values, type into the search box → list shrinks in real time; clear the search → list returns; check a visible value, clear the search → that value's filter stays applied.

### Implementation for User Story 3

- [x] T026 [US3] Implement `filterMenuValues(searchText)` in `frontend/src/app.js` that toggles visibility of `.col-menu__value-item` children under `.col-menu__values` using case-insensitive `String.includes()`; does NOT mutate `columnFilters` (research.md Decision 5, ui-contracts §filterMenuValues).
- [x] T027 [US3] Wire the `.col-menu__search` input's `oninput` in `openColumnMenu()` in `frontend/src/app.js` to `filterMenuValues(e.target.value)`; reset the input to empty on each menu open.
- [x] T028 [US3] When all visible items are hidden by the search, append/show a `<li class="col-menu__empty">No values match</li>` placeholder inside `.col-menu__values` (edge case from spec §Edge Cases).

**Checkpoint**: Searching within a column's value list filters the list smoothly; selections survive searching.

---

## Phase 6: User Story 4 - Execute SQL as an Alternative Filter (Priority: P3)

**Goal**: The SQL editor lives at the bottom of the page. Clicking "▶ Run SQL" executes the query and displays its result rows, switching `filterMode` to `'sql'`. Applying a column checkbox or sort afterward switches the mode back to `'column'` (last-applied wins).

**Independent Test**: Type a valid SQL query in the bottom editor, click Run SQL → table shows the SQL result rows; then check a value in a column menu → table returns to showing the column-filter result (mode flipped back).

### Implementation for User Story 4

- [x] T029 [US4] Update `executeSqlFilter(sqlQuery)` in `frontend/src/app.js`: on success set `_sqlResultData` and `filterMode = 'sql'`; on error show the error message in `.sql-panel` without mutating `filterMode` or `_sqlResultData`; always call `syncStateToUrl()` then `renderProcessedTable()` (FR-011, FR-012, ui-contracts §executeSqlFilter).
- [x] T030 [US4] Wire the bottom "▶ Run SQL" button (from T009) in `frontend/src/app.js` to read the textarea value and invoke `executeSqlFilter(sql)`; show/hide `.sql-panel` based on `window._sqlEngine != null`.
- [x] T031 [US4] Ensure `toggleColumnValue` (T022) and `handleColumnSort` (T018) set `filterMode = 'column'` so any column/sort interaction after a SQL run flips the mode back (verify, no new code required if already set).
- [x] T032 [US4] Style the bottom `.sql-panel` in `frontend/src/styles.css` so it is visually grouped (border, padding, monospace textarea) and does not overlap the table card when the table grows.

**Checkpoint**: All four user stories work independently and together under the last-applied-wins rule.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Wire the filter-mode badge, "Clear all filters" action, finalize URL restore edge cases, and run the manual validation checklist.

- [x] T033 Implement `renderFilterModeBadge()` in `frontend/src/app.js` returning the badge HTML per ui-contracts §Filter Mode Badge (`"SQL filter active"` when `filterMode==='sql' && _sqlResultData!=null`; `"Column filters active (N columns)"` when `filterMode==='column' && activeColumnFilterCount>0`; `"No active filter"` otherwise). Inject it into the top-bar placeholder from T010 via `renderProcessedTable()` (FR-016).
- [x] T034 Implement `clearAllFilters()` in `frontend/src/app.js`: reset `columnFilters = {}`, `tableState.sortColumn = null`, `tableState.sortDirection = 'asc'`, `tableState.currentPage = 0`, `_sqlResultData = null`, `filterMode = 'column'`; clear the SQL textarea; call `syncStateToUrl()` then `renderProcessedTable()` (FR-017, ui-contracts §clearAllFilters).
- [x] T035 Wire `#clear-all-filters` click in `frontend/src/app.js` to `clearAllFilters()`; show/hide the button based on `hasAnyActiveFilter` derived value (data-model.md §Derived Values).
- [x] T036 [P] Polish CSS for `.filter-mode-badge--sql` vs `--col` variants and the "Clear all filters" button in `frontend/src/styles.css` so the active mode is obvious at a glance.
- [x] T037 [P] Polish `.col-menu` positioning/z-index in `frontend/src/styles.css`: ensure it floats above the table on scroll, has a visible shadow, and its max-height + overflow do not clip the search box.
- [x] T038 Confirm URL state round-trip in `frontend/src/app.js`: (a) encoded values with commas/URL-reserved chars survive, (b) `sql_mode=1` with `sql=` restores and re-executes, (c) `selectDashboard` still clears state per T017. Fix any encoding/order-of-operations bugs discovered.
- [x] T039 Run the `specs/007-column-filter-menu/quickstart.md` manual validation checklist end-to-end in a desktop browser (Chrome/Firefox/Edge) and record pass/fail per scenario; fix any regressions before marking the feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all user stories.
- **User Stories (Phases 3–6)**: All depend on Foundational completion. Within each, implementation is largely linear because most tasks touch the same files (`app.js`, `index.html`, `styles.css`).
- **Polish (Phase 7)**: Depends on all user stories (or at least US1+US2+US4) being complete.

### User Story Dependencies

- **US1 (P1, Sort)**: Depends only on Phase 2. Independently testable.
- **US2 (P2, Checkboxes)**: Depends only on Phase 2. Independently testable; combines orthogonally with US1's sort if US1 is also present.
- **US3 (P2, Search box)**: Depends on Phase 2 and on US2 (search box filters the value list produced by US2). If you skip US2, the search box has nothing meaningful to filter — US3 should be built after US2.
- **US4 (P3, SQL)**: Depends only on Phase 2. Independently testable; last-applied-wins interaction with US1/US2 is verified by T031 when those stories are present.

### Within Each User Story

- Follow the task order shown. Tasks that edit the same file (typically `frontend/src/app.js`) are sequential by nature.
- Commit after each task or logical group so you can roll back a single step.

### Parallel Opportunities

- Phase 2: `T011` and `T012` are `[P]` (CSS-only, different rule blocks than JS tasks).
- Phase 7: `T036` and `T037` are `[P]` (CSS only).
- Across user stories: with multiple developers, US1 and US4 can proceed in parallel after Phase 2 because they touch largely distinct code paths (`handleColumnSort` vs `.sql-panel`). US2 and US3 share `openColumnMenu()` internals, so pair them.

---

## Parallel Example: Phase 2 CSS

```bash
# After JS/HTML tasks T003–T010 are done, two CSS tasks can run in parallel:
Task: "Add base CSS for .col-menu and value-list classes in frontend/src/styles.css"   # T011
Task: "Add base CSS for .sql-panel, .filter-mode-badge, .col-header--filtered in frontend/src/styles.css"  # T012
```

## Parallel Example: Polish CSS

```bash
Task: "Polish .filter-mode-badge variants and Clear-all button styling in frontend/src/styles.css"  # T036
Task: "Polish .col-menu positioning/z-index/shadow in frontend/src/styles.css"                      # T037
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001–T002).
2. Complete Phase 2: Foundational (T003–T017). Do not skip — every story depends on it.
3. Complete Phase 3: US1 Sort (T018–T020).
4. **STOP and VALIDATE**: Walk through spec.md §US1 acceptance scenarios 1–4 in a browser.
5. Ship the MVP if it stands on its own.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 Sort → validate → demo (MVP).
3. US2 Checkbox filter → validate → demo.
4. US3 Search within value list → validate → demo (depends on US2).
5. US4 SQL relocation & Run button → validate → demo.
6. Polish phase → final badge, clear-all, URL edge cases, quickstart walkthrough.

### Parallel Team Strategy

With multiple developers after Phase 2:

- Developer A: US1 (T018–T020) → then assist on Polish.
- Developer B: US2 (T021–T025) → hand off to Developer C for US3.
- Developer C: picks up US3 (T026–T028) once US2 lands.
- Developer D: US4 (T029–T032) in parallel with A/B/C.
- Team converges on Phase 7 together.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks.
- [Story] label maps each task to a specific user story for traceability.
- Every user story delivers an independently demoable slice; do not bundle them into one mega-PR.
- No automated tests were requested; validation is manual via `quickstart.md`.
- Keep commits scoped to a single task or logical group so reverts are cheap.
- Avoid re-introducing the old `filterText` / `_sqlFilterMode` fields — they are removed deliberately (T003).
