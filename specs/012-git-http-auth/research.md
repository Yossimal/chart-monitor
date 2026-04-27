# Research: Git HTTP Authentication Methods

**Feature**: 012-git-http-auth  
**Phase**: 0 — Research & Unknowns Resolution

---

## Finding 1: `.netrc` credential injection — implementation pattern

**Decision**: Write a temporary `.netrc` file to an isolated temp directory, set `HOME` to that directory in the git subprocess environment, then delete it immediately after the git operation completes (success or failure).

**Rationale**:
- git natively reads `$HOME/.netrc` without any extra configuration.
- Isolating `HOME` to a temp directory prevents interference with the container's real home directory.
- Using `tempfile.mkdtemp()` + cleanup in a `try/finally` block guarantees deletion even on exception.
- This avoids credentials in subprocess arguments (`ps` visible) and git error messages.

**`.netrc` format**:
```
machine <hostname> login <username> password <token>
```

- For `http-token`: login = `oauth2` (universally accepted by GitLab, Gitea, GitHub, Bitbucket).
- For `http-user-token`: login = the operator-supplied username.

**Hostname extraction**: use `urllib.parse.urlparse(url).hostname` to extract the hostname from `GIT_REPO_URL`.

**Alternatives considered**:
- URL embedding (`https://token@host/repo.git`): Rejected — credentials in process args and git error messages.
- `GIT_ASKPASS` script: Rejected — adds file creation complexity and race conditions in temp script.
- `git credential-store`: Rejected — requires persistent file, not ephemeral.

---

## Finding 2: `GIT_CONNECTION_METHOD` env var as the method selector

**Decision**: Add `GIT_CONNECTION_METHOD` env var (values: `ssh`, `http-token`, `http-user-token`; default: `ssh`). The backend reads this at startup to determine which credential path to activate.

**Rationale**: Single env var cleanly drives all branching in `load_gitops_config()` and `perform_sync()`. Default of `ssh` preserves full backward compatibility — existing deployments that do not set this var continue to work identically.

---

## Finding 3: `GIT_HTTP_TOKEN` in Secret, `GIT_HTTP_USERNAME` in ConfigMap

**Decision**:
- `GIT_HTTP_TOKEN` — sensitive, stored in the Kubernetes Secret (alongside `SYNC_SECRET` and `ssh-key`).
- `GIT_HTTP_USERNAME` — non-sensitive (just a username string), stored in ConfigMap via Helm values.

**Rationale**: The existing deployment uses `envFrom: secretRef` which injects all Secret keys as env vars. Adding `GIT_HTTP_TOKEN` to the Secret is consistent with how `SYNC_SECRET` is handled. Username is not secret and is more conveniently set via Helm values without re-creating the Secret.

---

## Finding 4: Conditional SSH volume mount in `deployment.yaml`

**Decision**: Wrap the `ssh-key` volume mount and volume definition in `{{- if eq .Values.gitops.connection "ssh" }}` Helm conditionals.

**Rationale**: When using HTTP methods, there is no SSH key and no Secret key named `ssh-key`. Keeping the mount unconditional would cause a `FailedMount` error for operators who only provide an HTTP token in their Secret.

---

## Finding 5: `GIT_SSH_URL` remains required only for `connection: ssh`

**Decision**: Remove the `required` gate on `GIT_SSH_URL` from `configmap.yaml`. Instead, validate per-method in the backend's `load_gitops_config()` — each method checks only its own required env vars.

**Rationale**: The current `{{ required "gitops.sshUrl is required" .Values.gitops.sshUrl }}` in the ConfigMap template fails for HTTP operators who do not provide an SSH URL. Per-method validation in the backend produces a descriptive error that names exactly which variable is missing.

---

## Finding 6: TLS skip-verify for HTTP — `http.sslVerify=false`

**Decision**: When `GIT_SKIP_VERIFY=true` and the connection method is HTTP, pass `-c http.sslVerify=false` to every `_run_git()` call via a shared prefix in the args list, or via git env vars `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_0`, `GIT_CONFIG_VALUE_0`.

**Rationale**: SSH `StrictHostKeyChecking` and HTTP `http.sslVerify` are orthogonal git settings. The env-var approach (`GIT_CONFIG_COUNT`) does not require modifying the args of every `_run_git()` call and is cleaner than a global `git config`.

**Implementation**:
```python
env["GIT_CONFIG_COUNT"] = "1"
env["GIT_CONFIG_KEY_0"] = "http.sslVerify"
env["GIT_CONFIG_VALUE_0"] = "false"
```

---

## Finding 7: Versioning — all locations to bump

**Decision**: Bump all three version locations from `0.1.0` → `0.2.0` (app/chart) and set `appVersion` to `3.2.0` (image tag convention used since 3.1.0 was the last shipped image):

| File | Field | Old | New |
|------|-------|-----|-----|
| `helm/chart-monitor/Chart.yaml` | `version` | `0.1.0` | `0.2.0` |
| `helm/chart-monitor/Chart.yaml` | `appVersion` | `"latest"` | `"3.2.0"` |
| `backend/pyproject.toml` | `version` | `0.1.0` | `0.2.0` |
| `backend/src/main.py` | FastAPI `version=` | `"0.1.0"` | `"0.2.0"` |

---

## Finding 8: Files requiring changes

| File | Change |
|------|--------|
| `backend/src/storage/git_sync.py` | Add `GitOpsConfig` fields; extend `load_gitops_config()`; add `_build_http_env()`; update `perform_sync()` |
| `helm/chart-monitor/values.yaml` | Restructure `gitops:` into nested sections |
| `helm/chart-monitor/templates/configmap.yaml` | Add `GIT_CONNECTION_METHOD`, `GIT_REPO_URL`, `GIT_HTTP_USERNAME`; fix `GIT_SSH_URL` (no longer required) |
| `helm/chart-monitor/templates/deployment.yaml` | Conditional SSH key volume mount |
| `helm/chart-monitor/Chart.yaml` | Version bump |
| `backend/pyproject.toml` | Version bump |
| `backend/src/main.py` | FastAPI version bump |
| `DEPLOY.md` | Document HTTP auth methods and new values structure |
| `docs/docs/getting-started/connect-git.md` | Add HTTP auth setup guide |
| `helm/chart-monitor/values-local.yaml` | Update to nested structure |
