# Implementation Plan: Git HTTP Authentication Methods

**Branch**: `012-git-http-auth` | **Date**: 2026-04-27 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/012-git-http-auth/spec.md`

## Summary

Add two HTTP-based git connection methods (`http-token` and `http-user-token`) alongside the existing `ssh` method. The connection method is selected via `GIT_CONNECTION_METHOD` env var driven by `gitops.connection` in Helm values. HTTP credentials are passed to git via a temporary `.netrc` file (never embedded in URLs). The existing flat `gitops.sshUrl`/`gitops.sshKeyMountPath` keys are replaced by a nested `gitops.ssh.*` structure (breaking change). All version strings are bumped to `0.2.0` (chart/app) and image to `3.2.0`.

## Technical Context

**Language/Version**: Python 3.11+ (backend), YAML (Helm chart)  
**Primary Dependencies**: FastAPI, subprocess + tempfile + urllib.parse + shutil (stdlib), Helm 3  
**Storage**: N/A  
**Testing**: pytest  
**Target Platform**: Linux container (Kubernetes / on-prem)  
**Project Type**: Web service + Helm chart  
**Performance Goals**: No overhead vs SSH; temp `.netrc` write/delete is negligible  
**Constraints**: Full backward compat for `connection: ssh` (default); breaking only for Helm values key rename  
**Scale/Scope**: 10 files touched; no new dependencies

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Dynamic Data Engine | ✅ Pass | No change to data extraction pipeline |
| II. Storage Agnostic & GitOps First | ✅ Pass | Extends GitOps with two new auth methods |
| III. Strict Typing & Clean Code | ✅ Pass | New fields typed on `GitOpsConfig`; clean branching |
| IV. Secure Execution Sandbox | ✅ Pass | Credentials in `.netrc` temp file with 0600 perms, not in URLs or process args |
| V. Vanilla Desktop-First UI | ✅ Pass | No UI changes |

**Gate**: All principles pass.

## Project Structure

### Documentation (this feature)

```text
specs/012-git-http-auth/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── environment-variables.md
└── tasks.md
```

### Source Code (files to change)

```text
backend/
├── src/
│   ├── storage/
│   │   └── git_sync.py          # Major: new fields, _build_http_env(), perform_sync() branching
│   └── main.py                  # Minor: version bump 0.1.0 → 0.2.0
└── pyproject.toml               # Minor: version bump 0.1.0 → 0.2.0

helm/chart-monitor/
├── Chart.yaml                   # version 0.1.0→0.2.0, appVersion latest→3.2.0
├── values.yaml                  # Restructure gitops: into nested sections
├── values-local.yaml            # Update to new nested structure
└── templates/
    ├── configmap.yaml           # New env vars; fix GIT_SSH_URL (no longer required)
    └── deployment.yaml          # Conditional SSH key volume mount

DEPLOY.md                        # Migration guide + HTTP auth docs
docs/docs/getting-started/
└── connect-git.md               # Add HTTP auth setup sections
```

---

## Implementation Detail

### Change 1 — `backend/src/storage/git_sync.py`

**a) Module docstring** — add new env vars:
```
GIT_CONNECTION_METHOD : "ssh" (default), "http-token", or "http-user-token".
GIT_REPO_URL          : HTTPS URL of the repository (HTTP methods only).
GIT_HTTP_TOKEN        : Access token or password for HTTP authentication.
GIT_HTTP_USERNAME     : Username for http-user-token method.
```

**b) `GitOpsConfig` dataclass** — add fields:
```python
connection_method: str = "ssh"
git_repo_url: str = ""
git_http_token: str = ""
git_http_username: str = ""
```

**c) `load_gitops_config()`** — method-aware validation:
- Read `GIT_CONNECTION_METHOD` (default `"ssh"`); reject unknown values.
- For `ssh`: require `GIT_SSH_URL`, `GIT_SSH_KEY_PATH`.
- For `http-token`/`http-user-token`: require `GIT_REPO_URL`, `GIT_HTTP_TOKEN`.
- For `http-user-token`: additionally require `GIT_HTTP_USERNAME`.
- `GIT_TARGET_PATH` and `SYNC_SECRET` always required.

**d) New `_build_http_env(repo_url, token, username, skip_verify)` function**:
- Parse hostname from URL with `urllib.parse.urlparse`.
- Write `$TMPDIR/.netrc` with `0600` permissions: `machine <host> login <login> password <token>`.
  - `login = username` for `http-user-token`; `"oauth2"` for `http-token`.
- Set `HOME=<TMPDIR>` so git reads `$HOME/.netrc`.
- If `skip_verify`: set `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=http.sslVerify`, `GIT_CONFIG_VALUE_0=false`.
- Return `(env_dict, tmp_dir)` — caller deletes `tmp_dir` in `finally`.

**e) `perform_sync()`** — branch on `cfg.connection_method`:
- `ssh` → `_build_git_env(cfg.git_ssh_key_path, ...)` as today; URL = `cfg.git_ssh_url`.
- `http-*` → `_build_http_env(...)`; URL = `cfg.git_repo_url`; wrap in `try/finally` to delete `tmp_dir`.

---

### Change 2 — `helm/chart-monitor/values.yaml`

Replace flat `gitops:` with nested:

```yaml
gitops:
  connection: ssh           # ssh | http-token | http-user-token

  ssh:
    url: ""                 # git@host:org/repo.git
    keyMountPath: "/app/secrets"

  httpToken:
    url: ""                 # https://host/org/repo.git

  httpUserToken:
    url: ""                 # https://host/org/repo.git
    username: ""

  skipVerify: false
```

---

### Change 3 — `helm/chart-monitor/templates/configmap.yaml`

```yaml
data:
  CHART_MONITOR_POLL_INTERVAL: {{ .Values.app.pollInterval | quote }}
  CHART_MONITOR_MAX_DATA: {{ .Values.app.maxData | quote }}
  CHART_MONITOR_STORE_DIR: {{ .Values.app.storeDir | quote }}
  GIT_TARGET_PATH: {{ .Values.app.storeDir | quote }}
  GIT_CONNECTION_METHOD: {{ .Values.gitops.connection | default "ssh" | quote }}
  GIT_SSH_URL: {{ .Values.gitops.ssh.url | default "" | quote }}
  GIT_SSH_KEY_PATH: {{ printf "%s/ssh-key" (.Values.gitops.ssh.keyMountPath | default "/app/secrets") | quote }}
  GIT_REPO_URL: {{ coalesce .Values.gitops.httpToken.url .Values.gitops.httpUserToken.url "" | quote }}
  GIT_HTTP_USERNAME: {{ .Values.gitops.httpUserToken.username | default "" | quote }}
  GIT_SKIP_VERIFY: {{ .Values.gitops.skipVerify | default "false" | quote }}
```

Key changes: `required` removed from `GIT_SSH_URL`; three new keys added.

---

### Change 4 — `helm/chart-monitor/templates/deployment.yaml`

Wrap SSH key volumeMount and volume in `{{- if eq .Values.gitops.connection "ssh" }}` conditionals.

---

### Change 5 — `helm/chart-monitor/Chart.yaml`

```yaml
version: 0.2.0
appVersion: "3.2.0"
```

---

### Change 6 — `backend/pyproject.toml`

```toml
version = "0.2.0"
```

---

### Change 7 — `backend/src/main.py`

```python
version="0.2.0",
```

---

### Change 8 — `helm/chart-monitor/values-local.yaml`

```yaml
gitops:
  connection: ssh
  ssh:
    url: "git@github.com:Yossimal/chart-monitor-dashboards.git"
```

---

### Change 9 — `DEPLOY.md`

- Migration guide: `gitops.sshUrl` → `gitops.ssh.url`, `gitops.sshKeyMountPath` → `gitops.ssh.keyMountPath`.
- HTTP token secret example.
- HTTP user+token secret example.
- Per-method values examples.

---

### Change 10 — `docs/docs/getting-started/connect-git.md`

- New "HTTP token" and "HTTP username + token" sections.
- Updated env var table.
- Migration note for 0.1.x → 0.2.0 SSH users.

---

## Complexity Tracking

No constitution violations. No complexity justification needed.
