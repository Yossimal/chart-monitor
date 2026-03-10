---
description: "Task list for GitOps Support implementation"
---

# Tasks: GitOps Support

**Input**: Design documents from `/specs/002-gitops-sync/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup

**Purpose**: Project initialization and basic structure updates

- [ ] T001 Update environment configuration loading in `backend/src/config.py` (or equivalent) to support `GIT_SSH_URL`, `GIT_SSH_KEY_PATH`, `GIT_TARGET_PATH`, and `SYNC_SECRET`.
- [ ] T002 Add `SyncResult` and `GitOpsConfiguration` models to `backend/src/models/`.

---

## Phase 2: Foundational

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T003 Implement the `backend/src/storage/git_sync.py` module with an empty outline.
- [ ] T004 Create UI banner alert container `<div id="sync-alert">` in `frontend/src/index.html`.

**Checkpoint**: Foundation ready - user story implementation can now begin sequence.

---

## Phase 3: User Story 1 - Configure Git Repository (Priority: P1)

**Goal**: The system administrator can configure a Git repository using environment variables so the system knows where to fetch the Python scripts from.

**Independent Test**: Can be fully tested by providing valid and invalid SSH credentials via environment variables and verifying if the system successfully connects or correctly logs an authentication failure.

### Implementation for User Story 1

- [ ] T005 [US1] Implement startup validation in `backend/src/main.py` (or equivalent) to check for GitOps environment variables.
- [ ] T006 [US1] Implement root route (`/`) replacement in `frontend/src/app.js` to show "How to connect your repo" tutorial if GitOps is disabled by the backend.
- [ ] T007 [US1] Create the "How to connect your repo" HTML structure in `frontend/src/index.html` (hidden by default).
- [ ] T008 [US1] Add a basic endpoint in `backend/src/api/routes.py` to allow the frontend to query if GitOps is enabled.

**Checkpoint**: At this point, User Story 1 should be fully functional; the app disables and shows the tutorial if variables are missing.

---

## Phase 4: User Story 2 - Manual Sync / Rerender (Priority: P1)

**Goal**: The system provides a manual "Sync" button in the UI. When triggered with the correct secret, it executes a shell Git fetch, validates extensions, and rerenders the scripts.

**Independent Test**: Push a new commit, click "Sync", enter the `SYNC_SECRET`, and observe the system fetching and rerendering.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US2] Create unit test in `backend/tests/unit/test_git_sync.py` to verify shell command execution.
- [ ] T010 [P] [US2] Create unit test in `backend/tests/unit/test_git_sync.py` to verify file extension validation (`.py`, `.txt` only).

### Implementation for User Story 2

- [ ] T011 [P] [US2] Implement Git shell operations (clone/pull) in `backend/src/storage/git_sync.py`.
- [ ] T012 [P] [US2] Implement file extension validation (`.py`, `.txt`) in `backend/src/storage/git_sync.py`.
- [ ] T013 [US2] Implement the `POST /api/git/sync` endpoint in `backend/src/api/routes.py` with Bearer token authentication mapping to `SYNC_SECRET`.
- [ ] T014 [US2] Connect the sync endpoint to the script rerendering engine in `backend/src/engine/pipeline.py`.
- [ ] T015 [P] [US2] Add the "Sync" button to the bottom of the dashboards sidebar in `frontend/src/index.html`.
- [ ] T016 [P] [US2] Create the secret prompt modal (with "Remember me" checkbox) in `frontend/src/index.html`.
- [ ] T017 [US2] Implement JS logic in `frontend/src/app.js` to handle modal interactions, `localStorage` for the secret, and the `fetch` call to `/api/git/sync`.
- [ ] T018 [US2] Implement logic in `frontend/src/app.js` to render the API error/success responses into the `#sync-alert` banner.
- [ ] T019 [P] [US2] Apply styling for the button, modal, and alerts in `frontend/src/styles.css`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

*(No specific tasks defined for this phase yet)*

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 should be verified first as it gates access to the app.
  - User Story 2 implements the core logic.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2).
- **User Story 2 (P1)**: Can start after Foundational (Phase 2). Integrates with US1's configuration variables.

### Parallel Opportunities

- Unit tests (`T009`, `T010`) can run in parallel.
- Backend Git logic (`T011`, `T012`) and Frontend UI scaffolding (`T015`, `T016`, `T019`) can run in parallel.
