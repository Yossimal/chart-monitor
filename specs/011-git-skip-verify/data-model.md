# Data Model: Git Skip-Verify

**Feature**: 011-git-skip-verify

---

## Entity: GitOpsConfig (extended)

**Location**: `backend/src/storage/git_sync.py` — `GitOpsConfig` dataclass

**Current fields** (unchanged):

| Field | Type | Source env var | Required |
|-------|------|----------------|----------|
| `git_ssh_url` | `str` | `GIT_SSH_URL` | Yes |
| `git_ssh_key_path` | `str` | `GIT_SSH_KEY_PATH` | Yes |
| `git_target_path` | `str` | `GIT_TARGET_PATH` | Yes |
| `sync_secret` | `str` | `SYNC_SECRET` | Yes |

**New field**:

| Field | Type | Source env var | Default | Required |
|-------|------|----------------|---------|----------|
| `git_skip_verify` | `bool` | `GIT_SKIP_VERIFY` | `False` | No |

**Validation rule**: `GIT_SKIP_VERIFY` is parsed as a boolean. Values `"true"`, `"1"`, `"yes"` (case-insensitive) evaluate to `True`. Everything else (including missing/empty) evaluates to `False`.

---

## Entity: Helm Values (extended)

**Location**: `helm/chart-monitor/values.yaml` — `gitops` block

**Current fields** (unchanged):

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `gitops.sshUrl` | string | `""` | SSH URL of remote Git repo |
| `gitops.sshKeyMountPath` | string | `"/app/secrets"` | Mount path for SSH key |

**New field**:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `gitops.skipVerify` | bool | `false` | When `true`, bypasses SSH host key verification (`GIT_SKIP_VERIFY=true`) |

---

## Runtime Behaviour: SSH Command

The `_build_git_env()` function builds the `GIT_SSH_COMMAND` environment variable passed to all git subprocess calls.

**When `git_skip_verify=False` (default)**:
```
ssh -i "<key_path>" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=30
```

**When `git_skip_verify=True`**:
```
ssh -i "<key_path>" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=30
```

**Flags added unconditionally** (not present in current code):
- `BatchMode=yes`: Prevents interactive SSH prompts from hanging the subprocess.
- `ConnectTimeout=30`: Surfaces TCP-level hangs faster with a clearer SSH error.

---

## State Transitions

`GIT_SKIP_VERIFY` is read once at module load (via `load_gitops_config()`). Changes require a process restart or pod restart (Helm rollout).

No persistent state is introduced; the flag is purely runtime configuration.
