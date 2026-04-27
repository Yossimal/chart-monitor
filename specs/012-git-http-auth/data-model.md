# Data Model: Git HTTP Authentication Methods

**Feature**: 012-git-http-auth

---

## Entity: GitOpsConfig (extended)

**Location**: `backend/src/storage/git_sync.py` — `GitOpsConfig` dataclass

**Current fields** (unchanged):

| Field | Type | Source env var | Required for SSH |
|-------|------|----------------|-----------------|
| `git_ssh_url` | `str` | `GIT_SSH_URL` | Yes |
| `git_ssh_key_path` | `str` | `GIT_SSH_KEY_PATH` | Yes |
| `git_target_path` | `str` | `GIT_TARGET_PATH` | Always |
| `sync_secret` | `str` | `SYNC_SECRET` | Always |
| `git_skip_verify` | `bool` | `GIT_SKIP_VERIFY` | No (default False) |

**New fields**:

| Field | Type | Source env var | Required for method |
|-------|------|----------------|---------------------|
| `connection_method` | `str` | `GIT_CONNECTION_METHOD` | No (default `"ssh"`) |
| `git_repo_url` | `str` | `GIT_REPO_URL` | `http-token`, `http-user-token` |
| `git_http_token` | `str` | `GIT_HTTP_TOKEN` | `http-token`, `http-user-token` |
| `git_http_username` | `str` | `GIT_HTTP_USERNAME` | `http-user-token` only |

**Validation rules** (in `load_gitops_config()`):

| Connection method | Required env vars |
|-------------------|-------------------|
| `ssh` | `GIT_SSH_URL`, `GIT_SSH_KEY_PATH`, `GIT_TARGET_PATH`, `SYNC_SECRET` |
| `http-token` | `GIT_REPO_URL`, `GIT_HTTP_TOKEN`, `GIT_TARGET_PATH`, `SYNC_SECRET` |
| `http-user-token` | `GIT_REPO_URL`, `GIT_HTTP_TOKEN`, `GIT_HTTP_USERNAME`, `GIT_TARGET_PATH`, `SYNC_SECRET` |

**Invalid `GIT_CONNECTION_METHOD`** values cause a startup error listing valid options.

---

## Entity: Helm Values (restructured)

**Location**: `helm/chart-monitor/values.yaml` — `gitops:` block

**New nested structure**:

```yaml
gitops:
  connection: ssh          # ssh | http-token | http-user-token

  ssh:
    url: ""                # git@host:org/repo.git  →  GIT_SSH_URL
    keyMountPath: "/app/secrets"  →  GIT_SSH_KEY_PATH = keyMountPath/ssh-key

  httpToken:
    url: ""                # https://host/org/repo.git  →  GIT_REPO_URL
    # token: from Secret key GIT_HTTP_TOKEN

  httpUserToken:
    url: ""                # https://host/org/repo.git  →  GIT_REPO_URL
    username: ""           # →  GIT_HTTP_USERNAME (ConfigMap, non-sensitive)
    # token: from Secret key GIT_HTTP_TOKEN

  skipVerify: false        # GIT_SKIP_VERIFY — applies to both SSH and HTTPS
```

**Breaking changes vs current**:

| Old key | New key | Notes |
|---------|---------|-------|
| `gitops.sshUrl` | `gitops.ssh.url` | Renamed |
| `gitops.sshKeyMountPath` | `gitops.ssh.keyMountPath` | Renamed |

---

## Entity: Kubernetes Secret (extended)

**New key** to add alongside existing `SYNC_SECRET` and `ssh-key`:

| Key | Description | Required for |
|-----|-------------|-------------|
| `GIT_HTTP_TOKEN` | Repository access token or password | `http-token`, `http-user-token` |

**ConfigMap additions** (non-sensitive):

| Key | Value source | Required for |
|-----|-------------|-------------|
| `GIT_CONNECTION_METHOD` | `.Values.gitops.connection` | Always |
| `GIT_REPO_URL` | `.Values.gitops.httpToken.url` or `.Values.gitops.httpUserToken.url` | HTTP methods |
| `GIT_HTTP_USERNAME` | `.Values.gitops.httpUserToken.username` | `http-user-token` |

---

## Runtime Behaviour: HTTP credential flow

**When `connection_method` is `http-token` or `http-user-token`**:

1. Parse hostname from `GIT_REPO_URL` using `urllib.parse.urlparse`.
2. Determine login: `"oauth2"` for `http-token`; operator-supplied username for `http-user-token`.
3. Write `$TMPDIR/.netrc` containing: `machine <hostname> login <login> password <token>`.
4. Set `HOME=<TMPDIR>` in the git subprocess environment so git reads `$HOME/.netrc`.
5. If `git_skip_verify=True`, additionally set `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=http.sslVerify`, `GIT_CONFIG_VALUE_0=false`.
6. Execute all git operations with this environment.
7. Delete temp directory in `finally` block (always, even on exception).

**When `connection_method` is `ssh`** (unchanged):
- `_build_git_env()` sets `GIT_SSH_COMMAND` as before.
- SSH key volume mount active in pod.

---

## Version Bump Summary

| File | Field | Old | New |
|------|-------|-----|-----|
| `helm/chart-monitor/Chart.yaml` | `version` | `0.1.0` | `0.2.0` |
| `helm/chart-monitor/Chart.yaml` | `appVersion` | `"latest"` | `"3.2.0"` |
| `backend/pyproject.toml` | `version` | `0.1.0` | `0.2.0` |
| `backend/src/main.py` | FastAPI `version=` | `"0.1.0"` | `"0.2.0"` |
