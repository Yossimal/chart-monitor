# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

The GitOps Support feature (`002-gitops-sync`) adds the ability to synchronize Python script definitions (dashboards/collectors) directly from a remote Git repository. Instead of automatic polling, users will trigger a manual "Sync" via the UI. The system will pull the latest scripts from the configured Git repo (using environment variables for SSH URL, Key Path, and Target Directory), validate that only `.py` and `.txt` files exist, and rerender them for immediate use. Strict error handling will surface connection, authentication, and parsing errors directly to the user in the UI, falling back to previous working versions if parsing fails.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript/Vanilla (Frontend)
**Primary Dependencies**: FastAPI, RestrictedPython, Pytest (Backend)
**Storage**: Git repository (remote), Local Filesystem (target path)
**Testing**: Pytest (backend unit/integration tests)
**Target Platform**: Linux Server / Kubernetes (via Volume Mounts)
**Project Type**: Web Service + UI
**Performance Goals**: Manual sync should complete within seconds; no impact on core monitoring uptime.
**Constraints**: 
- Must use SSH for Git authentication.
- Must reject fetches containing non-`.py` and non-`.txt` files.
- UI must remain Vanilla (HTML/CSS/JS).
- Git fetches MUST use pure system shell commands (`subprocess.run(['git', ...])`) executed directly within `GIT_TARGET_PATH`.
- Manual sync trigger MUST be exposed as `POST /api/git/sync`, authenticated via `Bearer <SYNC_SECRET>`.
- The UI MUST place the "Sync" button at the bottom of the dashboards sidebar and prompt for the `SYNC_SECRET`.

**Scale/Scope**: Supports syncing scripts from a single remote Git repository.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Dynamic Data Engine**: Complies. This feature enhances the dynamic engine by allowing external script syncing.
- **II. Storage Agnostic & GitOps First**: Complies perfectly. This implements the "Pure GitOps" file-system/Git approach.
- **III. Strict Typing & Clean Code**: Will enforce strict typing on new Git sync services.
- **IV. Secure Execution Sandbox**: Complies. File extension whitelist (`.py`/`.txt`) adds a layer of security before RestrictedPython parsing.
- **V. Vanilla Desktop-First UI**: Complies. The "Sync" UI and error alerts will use Vanilla HTML/CSS/JS.

**Status**: PASSED.

## Project Structure

## Project Structure

### Documentation (this feature)

```text
specs/002-gitops-sync/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/routes.py              # Expose manual sync REST endpoint
│   ├── engine/pipeline.py         # Ensure renderer uses synced paths
│   └── storage/git_sync.py        # [NEW] Git operations and validation logic
└── tests/
    └── unit/test_git_sync.py      # [NEW] Unit tests for GitOps behavior

frontend/
├── src/
│   ├── app.js                     # Update API calls for sync trigger & error alerts
│   ├── index.html                 # Add GitOps UI (Sync button + instructions)
│   └── styles.css                 # Styling for the sync button and alerts
```

**Structure Decision**: Web application split (backend/frontend). A new `storage/git_sync.py` module will handle the Git implementation cleanly decoupled from the general poller.

## Phase 0: Outline & Research

The following unknowns from the Technical Context must be resolved in `specs/002-gitops-sync/research.md`:

1. **Git Library Implementation**:
   - *Task*: Research the best approach for pulling from a Git repository over SSH using pure shell commands in the target directory.
   - *Context*: The system must authenticate via `GIT_SSH_KEY_PATH` and target a raw `GIT_SSH_URL`.
   - *Candidates*: Pure system shell `subprocess.run(['git', ...])`.

2. **API Contract for Manual Sync**:
   - *Task*: Determine the exact REST API endpoint (`POST /api/git/sync`) for triggering a manual sync, implementing `SYNC_SECRET` Bearer token auth, and standardizing the error response structure.
   - *Context*: FastAPI backend. The endpoint needs to block until the sync is complete, returning success or detailed error payload.

3. **UI Integration Details**:
   - *Task*: Decide the best way to implement the "Sync" button at the bottom of the dashboards sidebar, the `SYNC_SECRET` prompt with "Remember me", and the configuration guides.
   - *Context*: Vanilla JS frontend interacting with the new authenticated endpoint.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| [e.g., 4th project]        | [current need]     | [why 3 projects insufficient]        |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient]  |
