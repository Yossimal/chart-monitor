# GitOps Sync

Chart-Monitor loads all monitoring scripts from a Git repository. This page explains how that synchronisation works from end to end.

---

## Configuration

Four environment variables control GitOps:

| Variable | Description |
|----------|-------------|
| `GIT_SSH_URL` | SSH clone URL of the remote repository |
| `GIT_SSH_KEY_PATH` | Path to the private SSH key on the server |
| `GIT_TARGET_PATH` | Local directory where the repo is cloned/pulled |
| `SYNC_SECRET` | Secret used to authenticate manual sync API calls |

If any variable is missing, GitOps is considered **disabled** and the setup page is shown.

---

## Initial clone

On first startup (when `GIT_TARGET_PATH` is empty or does not exist), the backend performs a full `git clone` of `GIT_SSH_URL` into `GIT_TARGET_PATH` using `GIT_SSH_KEY_PATH` for authentication.

---

## Polling

The **Poller** (`backend/src/storage/poller.py`) runs as an async background task. It periodically performs a `git pull` on the local clone to pick up new commits.

After a successful pull, the Poller calls `FileStore.reload()` to re-import all `.py` files and refresh the in-memory registry of Collectors and Dashboards.

---

## Manual sync

A manual sync is triggered by a `POST /api/v1/git/sync` request with a `Authorization: Bearer <SYNC_SECRET>` header. This is what the **↕ Sync Scripts** button in the UI sends.

The backend:

1. Validates the `SYNC_SECRET`
2. Runs `git pull` on the local clone
3. Calls `FileStore.reload()`
4. Returns `{"success": true, "message": "...", "details": "..."}`

---

## FileStore: loading scripts

`FileStore` (`backend/src/storage/store.py`) scans `GIT_TARGET_PATH` recursively for `.py` files and imports each one. For every imported module, it inspects all classes and registers:

- Classes that inherit from `Collector` → added to the collectors registry
- Classes that inherit from `TableDashboard` → added to the dashboards registry

Files with syntax errors or import failures are logged as warnings and skipped. Valid files continue to be served.

---

## Deploy key security

The SSH private key (`GIT_SSH_KEY_PATH`) is used only to authenticate pull operations against the remote Git repository. It is:

- Never sent over the network except as part of the SSH handshake
- Never exposed via API responses
- Read-only by default (Chart-Monitor never pushes to the repository)

!!! tip "Minimal permissions"
    Create a deploy key with **read-only** access unless your scripts need to write back to the repo. Read-only keys reduce risk if the key is ever compromised.

---

## GitOps status endpoint

`GET /api/v1/git/status` returns `{"enabled": true}` or `{"enabled": false}` based on whether all four environment variables are present. The frontend uses this to decide whether to show the setup page or the main app.
