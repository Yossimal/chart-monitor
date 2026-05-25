# Implementation Plan: Git Skip-Verify for SSH Connection

**Branch**: `011-git-skip-verify` | **Date**: 2026-04-26 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/011-git-skip-verify/spec.md`

## Summary

Allow operators to opt in to bypassing SSH host key verification via a `GIT_SKIP_VERIFY` environment variable, needed for on-premises Git servers with self-signed or internally signed SSH host certificates. The existing `GIT_SSH_COMMAND` in `_build_git_env()` already hardcodes `StrictHostKeyChecking=no`; this plan makes that behaviour explicit, configurable, and secure-by-default. Two additional SSH flags (`BatchMode=yes`, `ConnectTimeout=30`) are added unconditionally to harden the command.

## Technical Context

**Language/Version**: Python 3.11+ (backend), YAML (Helm chart)  
**Primary Dependencies**: FastAPI, subprocess (stdlib), Helm 3  
**Storage**: N/A (no storage changes)  
**Testing**: pytest  
**Target Platform**: Linux container (Kubernetes / on-prem)  
**Project Type**: Web service + Helm chart  
**Performance Goals**: No overhead introduced; SSH connection timeout capped at 30s  
**Constraints**: Backward compatible — existing deployments without `GIT_SKIP_VERIFY` must continue to work  
**Scale/Scope**: Single env var, 5 files touched

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Dynamic Data Engine | ✅ Pass | No change to data extraction pipeline |
| II. Storage Agnostic & GitOps First | ✅ Pass | Extends GitOps SSH handling; no storage backend change |
| III. Strict Typing & Clean Code | ✅ Pass | New `bool` field on `GitOpsConfig` dataclass; type-safe |
| IV. Secure Execution Sandbox | ✅ Pass | Skip-verify is off by default; explicit opt-in only |
| V. Vanilla Desktop-First UI | ✅ Pass | No UI changes |

**Gate**: All principles pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/011-git-skip-verify/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── environment-variables.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (files to change)

```text
backend/
└── src/
    └── storage/
        └── git_sync.py          # GitOpsConfig dataclass + _build_git_env()

helm/chart-monitor/
├── values.yaml                  # gitops.skipVerify: false
└── templates/
    └── configmap.yaml           # GIT_SKIP_VERIFY env var entry

DEPLOY.md                        # Document GIT_SKIP_VERIFY
docs/docs/getting-started/
└── connect-git.md               # Document the option and on-prem usage
```

**Structure Decision**: Web application (Option 2). Backend-only changes plus Helm chart config. No frontend changes.

---

## Implementation Detail

### Change 1 — `backend/src/storage/git_sync.py`

**a) Module docstring** — add `GIT_SKIP_VERIFY` to the environment variable table:
```
GIT_SKIP_VERIFY  : Set to "true" to bypass SSH host key verification (on-prem use).
                   Defaults to false (secure-by-default).
```

**b) `GitOpsConfig` dataclass** — add field:
```python
git_skip_verify: bool = False
```

**c) `load_gitops_config()`** — read and parse env var:
```python
git_skip_verify = os.environ.get("GIT_SKIP_VERIFY", "").lower() in ("true", "1", "yes")
```
Include in the returned `GitOpsConfig(...)` constructor call.

**d) `_build_git_env(key_path, skip_verify=False)`** — accept `skip_verify` parameter:
```python
def _build_git_env(key_path: str, skip_verify: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    safe_key_path = key_path.replace('\\', '/')
    host_check = "no" if skip_verify else "accept-new"
    env["GIT_SSH_COMMAND"] = (
        f'ssh -i "{safe_key_path}"'
        f' -o StrictHostKeyChecking={host_check}'
        f' -o UserKnownHostsFile=/dev/null'
        f' -o BatchMode=yes'
        f' -o ConnectTimeout=30'
    )
    return env
```

**e) `perform_sync()`** — pass `cfg.git_skip_verify` to `_build_git_env()`:
```python
git_env = _build_git_env(cfg.git_ssh_key_path, skip_verify=cfg.git_skip_verify)
```

---

### Change 2 — `helm/chart-monitor/values.yaml`

Add under `gitops:` block (after `sshKeyMountPath`):
```yaml
  # Set to true to bypass SSH host key verification (needed for on-prem Git servers
  # with self-signed or internal CA SSH host certificates).
  skipVerify: false
```

---

### Change 3 — `helm/chart-monitor/templates/configmap.yaml`

Add after the existing `GIT_SSH_KEY_PATH` line:
```yaml
  GIT_SKIP_VERIFY: {{ .Values.gitops.skipVerify | default "false" | quote }}
```

---

### Change 4 — `DEPLOY.md`

Document `GIT_SKIP_VERIFY` in the environment variables reference table. Add an "On-premises Git servers" note explaining when to set it.

---

### Change 5 — `docs/docs/getting-started/connect-git.md`

Add a section: "Using a self-signed or on-prem Git server" that explains:
- What `GIT_SKIP_VERIFY=true` does
- When to use it (on-prem / internal CA)
- Security implication (host key not validated — only use on trusted networks)
- How to set it via Helm (`gitops.skipVerify: true`)

---

## Complexity Tracking

No constitution violations. No complexity justification table needed.
