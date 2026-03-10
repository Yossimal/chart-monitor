# Phase 0: Research Findings - GitOps Support

## 1. Git Library Implementation

The system needs to fetch Python scripts from a remote Git repository over SSH cleanly and securely.

**Decision**: Use pure system shell commands (`subprocess.run(['git', 'fetch', ...])`) executed directly within the target directory specified by `GIT_TARGET_PATH`.

**Rationale**: 
1. `GitPython` has known security vulnerabilities regarding command injection if remote URLs are untrusted. While we assume the `GIT_SSH_URL` from the environment is trusted, relying on standard `subprocess` with strict argument passing is simpler and avoids an extra heavy dependency.
2. `pygit2` requires OS-level package installations (`libgit2-dev`) which complicates the baseline Docker/deployment requirements for a Python backend.
3. The `subprocess` approach using a custom wrapper (`storage/git_sync.py`) allows us to explicitly pass the `GIT_SSH_KEY_PATH` via the `GIT_SSH_COMMAND` environment variable natively supported by Git.

**Alternatives considered**: 
- `GitPython`: Rejected due to being overkill for a simple fetch-and-check operation.
- `pygit2`: Rejected due to native C-library dependencies.

## 2. API Contract for Manual Sync

The frontend needs a way to securely trigger the synchronization and handle specific error states.

**Decision**: Implement a new `POST /api/git/sync` endpoint in `backend/src/api/routes.py`. It requires a Bearer token matching the backend's `SYNC_SECRET`.

**Rationale**:
- **Request**: Empty payload (it reads from backend environment variables `GIT_SSH_URL`, `GIT_SSH_KEY_PATH`, `GIT_TARGET_PATH`).
- **Processing**: The endpoint is synchronous. It invokes the Git fetch logic.
- **Validation**:
  1. If connection fails -> `400 Bad Request` with `{"detail": "Connection to Git repository failed: <reason>"}`.
  2. If non-`py`/`txt` files found -> `400 Bad Request` with `{"detail": "Malicious files detected. Only .py and .txt allowed."}`.
  3. If rendering syntax error -> `400 Bad Request` with `{"detail": "Syntax error in scripts. Rollback successful: <reason>"}`.
- **Success**: `200 OK` with `{"status": "success", "message": "Scripts synced and rerendered successfully."}`.

**Alternatives considered**:
- Async background task (Return 202 Accepted and poll for status): Overly complex for a fetch operation that is expected to take < 5 seconds over SSH. A synchronous block is simpler and easier to handle in Vanilla JS.

## 3. UI Integration Details

The UI requires a manual "Sync" button, an authentication prompt, an area for error alerts, and instructions for SSH key setup.

**Decision**: 
1. Add a primary "Sync" button at the bottom of the dashboards sidebar.
2. When the user clicks the Sync button, display a prompt modal asking for the `SYNC_SECRET`. Include a "Remember me" checkbox to save the secret into `localStorage`. If already remembered, bypass the prompt.
3. Add a hidden `<div id="sync-alert">` banner for displaying detailed error/success messages.
4. Add a new `gitops-guide.html` (or modal integration) that provides pre-written instructions for setting up SSH keys. Provide a link to this guide near the Sync button or inside the prompt.

**Rationale**:
- Placing the Sync button globally in the header ensures it is always accessible, as script syncing affects the entire monitoring system.
- Vanilla JS `fetch()` will call the new `POST /api/dashboards/sync` endpoint and inject the `error.detail` directly into the `#sync-alert` container, satisfying the user's request for explicit failure reasons.

**Alternatives considered**:
- Disabling the whole app until GitOps is configured: Rejected, as GitOps is an optional feature. Local file storage is still a valid use case.
