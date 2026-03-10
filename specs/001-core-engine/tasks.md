# Tasks: Core Chart-Monitor Application

**Feature Branch**: `001-core-engine`
**Input**: Design documents from `/specs/001-core-engine/`
**Prerequisites**: `spec.md`, `plan.md`, `data-model.md`, `contracts/api.md`, `research.md`, `quickstart.md`

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Tests are included as explicitly requested.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Reverse Tailwind setup: delete `frontend/package.json`, `frontend/tailwind.config.js`, and `frontend/src/output.css` (no external build step required)
- [ ] T002 Configure FastAPI to serve static files from `frontend/src` at the root path `/` in `backend/src/main.py`
- [ ] T003 [P] Download required Inter/JetBrains fonts locally into `frontend/src/assets/fonts/` (no CDNs allowed)

---

## Phase 2: User Story 3 - Frontend Display & Polling (Priority: P2)

**Goal**: UI polls the backend server at a customizable frequency defined by the Source configuration and renders the processed data in dynamic tables using pure Vanilla CSS.

**Independent Test**: Can be tested using mock backend responses to ensure the frontend successfully polls at intervals and renders tables correctly.

### Implementation for User Story 3

- [ ] T004 [US3] Create `frontend/src/styles.css` with pure Vanilla CSS, focusing on a dark desktop-first monitoring aesthetic (glassmorphism tabs, subtle borders, data-table layout)
- [ ] T005 [US3] Rewrite `frontend/src/index.html` to remove Tailwind utility classes and use semantic BEM/component CSS classes defined in `styles.css`. Update link to local font assets.
- [ ] T006 [US3] Rewrite DOM generation logic in `frontend/src/app.js` to assign semantic CSS classes instead of Tailwind utilities for dynamic tables, error banners, and sidebar navigation
- [ ] T007 [US3] Adjust `TableDashboard` examples (e.g. `quickstart.md` and `store/github_dashboard.py` and `store/pods_dashboard.py`) to output raw hex colors/css strings in `style` instead of Tailwind classes.

**Checkpoint**: Full end-to-end functionality including frontend polling should be operational with a customized Vanilla UI served directly by FastAPI.

---

## Phase 3: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and edge cases

- [ ] T008 [P] Validate visually that the pod metrics and GitHub dashboard quickstarts render correctly mapped CSS in the frontend.
- [ ] T009 Update `README.md` to remove npm/Tailwind build instructions and document the new single-command Python backend startup.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Must run first to clean up old Tailwind artifacts and mount the static directory.
- **User Stories (Phase 2)**: Depends on Phase 1 FastAPI routing to view changes.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.
