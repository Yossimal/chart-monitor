# Tasks: UI Enhancements

**Input**: Design documents from `/specs/001-ui-enhancements/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-contracts.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

*(No major setup tasks required for this feature, as it builds entirely upon the existing frontend and backend structure.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented
**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Update `CellResult` and `DashboardMeta` Pydantic models to include `display` and `set_name` respectively in `backend/src/api/routes.py`
- [x] T002 Update pipeline logic to safely extract `set_name` (throw error string if >150 chars) and supply `display` values in `backend/src/engine/pipeline.py` / `backend/src/engine/executor.py`

**Checkpoint**: Backend API foundation ready - frontend user story implementation can now begin.

---

## Phase 3: User Story 1 - Advanced Data Filtering and Sorting (Priority: P1) 🎯 MVP

**Goal**: Filter text columns with autocomplete and sort data by numeric, alphabetic, or date values (`value`) while showing formatted (`display`) data.
**Independent Test**: Load a table, type into text filter to see autocomplete, apply filter to see exact matches, and click headers to sort rows correctly.

### Implementation for User Story 1

- [ ] T003 [P] [US1] Update Table Render function to render `display` text but attach base `value` as data attributes in `frontend/src/app.js`
- [ ] T004 [US1] Implement Client-side Pagination logic (slicing 10k rows) in `frontend/src/app.js`
- [ ] T005 [P] [US1] Implement exact-match Textual Filtering logic with empty result state handling in `frontend/src/app.js`
- [ ] T006 [US1] Implement Autocomplete `<datalist>` generation from unique column values in `frontend/src/app.js`
- [ ] T007 [US1] Implement Bidirectional Sorting logic (evaluating nulls as lowest, defaulting mixed types to string) on raw `value` in `frontend/src/app.js`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Real-time Dashboard Controls (Priority: P1)

**Goal**: Manually refresh data, adjust the refresh rate, and change the max data value from the UI.
**Independent Test**: Click "Refresh Now", change the refresh rate dropdown, and modify the max data value (setting `<0` to see auto-clamp to 0 and empty table).

### Implementation for User Story 2

- [x] T008 [P] [US2] Add "Refresh Now" button and manual API trigger logic in `frontend/src/app.js`
- [x] T009 [P] [US2] Add Auto-refresh Interval UI and polling `setInterval` updates in `frontend/src/app.js`
- [x] T010 [US2] Add Max Data Value input and dataset clipping logic (handle `<0` condition) in `frontend/src/app.js`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Visual Customization and Theming (Priority: P2)

**Goal**: View dashboard with appropriate `set_name`, toggle light/dark mode, and see human-readable time strings.
**Independent Test**: Toggle the theme switch to see color changes, view the dashboard title to confirm it's not the class name, and check time columns for readable formats.

### Implementation for User Story 3

- [x] T011 [P] [US3] Update Frontend to render Dashboard Title from API `name` instead of class name in `frontend/src/app.js`
- [x] T012 [P] [US3] Define Light/Dark Mode CSS variables (`data-theme="dark"`) in `frontend/src/styles.css`
- [x] T013 [US3] Add Theme Toggle button and `localStorage` persistence in `frontend/src/app.js`
- [x] T014 [US3] Format time strings using `Intl.DateTimeFormat` during cell rendering in `frontend/src/app.js`

**Checkpoint**: All visual and theming customizations should now be independently functional.

---

## Phase 6: User Story 4 - Search Dashboard (Priority: P2)

**Goal**: Search for specific dashboards to quickly navigate to the view needed.
**Independent Test**: Type a dashboard name in the sidebar search bar and verify only matching names are shown.

### Implementation for User Story 4

- [x] T015 [P] [US4] Add search input above the dashboard list in `frontend/src/app.js`
- [x] T016 [US4] Implement name-matching filter logic for dashboard sidebar list elements in `frontend/src/app.js`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T017 [P] Code cleanup and refactoring in `frontend/src/app.js` to ensure clean separation of UI components.
- [x] T018 Run manual tests per the scenarios in `quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: N/A
- **Foundational (Phase 2)**: Starts immediately - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel if desired, but sequential execution is recommended starting with MVP US1.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Parallel Opportunities

- Foundational tasks T001 and T002 can be executed concurrently.
- All User Stories can technically be implemented in parallel by different developers once Phase 2 is complete.
- Within US1, T003 and T005 can be implemented concurrently.
- Within US2, T008 and T009 can be implemented concurrently.
- Within US3, T011 and T012 can be implemented concurrently.

---

## Implementation Strategy

### MVP First (User Story 1 & 2)

1. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
2. Complete Phase 3: User Story 1 (Core table features)
3. Complete Phase 4: User Story 2 (Core dashboard controls)
4. **STOP and VALIDATE**: Test User Stories 1 and 2 independently
5. Move onto Polish P2 stories (Phase 5 and 6)
