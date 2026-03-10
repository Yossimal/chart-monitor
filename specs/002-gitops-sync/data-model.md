# Data Model: GitOps Support

## Configuration Entities

### `GitOpsConfig`
This entity represents the configuration required to synchronize scripts from a remote Git repository. This data is entirely sourced from the environment variables, meaning there is no database persistence required for this entity.

**Attributes:**
- `git_ssh_url` (string): The remote SSH URL for the repository (e.g., `git@github.com:user/repo.git`). Sourced from `GIT_SSH_URL`.
- `git_ssh_key_path` (string): Absolute path on the host representing the private SSH key used to authenticate. Sourced from `GIT_SSH_KEY_PATH`.
- `target_path` (string): Absolute path on the host where the cloned/fetched repository should reside. Sourced from `GIT_TARGET_PATH`.
- `sync_secret` (string): Secret token required to authenticate the sync API request. Sourced from `SYNC_SECRET`.

**Validation Rules:**
- All three variables must be present to enable the "Sync" feature. If any are missing, the feature operates in a degraded/informational mode indicating configuration is required.
- `target_path` must be a directory the application has write permissions to.

### `SyncResult`
This entity represents the result of a manual sync operation, returned to the UI.

**Attributes:**
- `status` (string): Either `"success"` or `"error"`.
- `message` (string): A human-readable description of the result (e.g., "15 scripts synced", "Connection refused").
- `error_type` (string, optional): Categorization of the error if `status == "error"` (e.g., `"auth_failure"`, `"malicious_file"`, `"syntax_error"`).
- `failed_files` (list of strings, optional): If `error_type == "syntax_error"`, a list of files that failed to parse during rerendering.

**State Transitions:**
- When a `fetch` is triggered, the engine transitions to a `Syncing` state.
- If verification (file extension check) fails, transitions immediately to `Error`.
- If fetch succeeds but parsing fails, transitions to `Error` and triggers a `Rollback` of the target path.
- If fetch and parsing succeed, transitions to `Success`.
