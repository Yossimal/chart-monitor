# Research: Git Skip-Verify for SSH Connection

**Feature**: 011-git-skip-verify  
**Phase**: 0 — Research & Unknowns Resolution

---

## Finding 1: Current SSH command is already permissive (hardcoded)

**Decision**: The existing `_build_git_env()` in `backend/src/storage/git_sync.py:94-96` already hardcodes `StrictHostKeyChecking=no` and `UserKnownHostsFile=/dev/null`, meaning host key verification is already bypassed for every deployment regardless of environment.

**Implication**: The feature is not about adding the capability — it already exists. The goal is to:
1. Make the behavior explicit and opt-in via `GIT_SKIP_VERIFY` env var.
2. Introduce a stricter default (`StrictHostKeyChecking=accept-new`) when skip-verify is off, documenting the intent clearly.
3. Harden the SSH command with additional safety flags that are currently missing.

**Rationale**: Hardcoding permissive SSH options is a security smell. Making it configurable restores secure-by-default intent while giving on-prem operators an explicit escape hatch.

**Alternatives considered**:
- Keep `StrictHostKeyChecking=no` hardcoded: Rejected — no operator visibility, silently insecure.
- Use a persistent `known_hosts` volume: Deferred — out of scope; adds PVC complexity for a minor gain in stateless containers.

---

## Finding 2: SSH command missing safety flags

**Decision**: Add `BatchMode=yes` and `ConnectTimeout=30` to `GIT_SSH_COMMAND` unconditionally in both skip-verify and verify modes.

**Rationale**:
- `BatchMode=yes` prevents SSH from hanging waiting for interactive password or passphrase prompts, which would cause the 60-second subprocess timeout to fire instead of a clear SSH error.
- `ConnectTimeout=30` sets an explicit SSH-level connection timeout (separate from the subprocess timeout), so TCP-level hangs surface faster with a clearer error.

**Alternatives considered**:
- `ConnectTimeout=60` to match subprocess timeout: Rejected — gives SSH the full window, subprocess timeout fires first with a generic message.

---

## Finding 3: SSH StrictHostKeyChecking semantics in a stateless container

**Decision**: When `GIT_SKIP_VERIFY=false` (default), use `StrictHostKeyChecking=accept-new`. When `GIT_SKIP_VERIFY=true`, use `StrictHostKeyChecking=no`.

**Rationale**: In a stateless container with `UserKnownHostsFile=/dev/null`, both options effectively always succeed on first connect (nothing in known_hosts to reject). However:
- `accept-new` is the semantically correct "safer" value and signals intent clearly.
- `no` is the explicit "bypass everything" opt-in for on-prem environments.
- The `UserKnownHostsFile=/dev/null` remains in both modes since containers have no persistent known_hosts store.

---

## Finding 4: Helm configmap has a required GitOps SSH URL

**Decision**: `configmap.yaml:12` uses `{{ required ... .Values.gitops.sshUrl }}` which forces every Helm install to provide a Git SSH URL. This is a pre-existing issue outside scope of this feature.

**Implication**: The new `GIT_SKIP_VERIFY` field in the ConfigMap will use `{{ .Values.gitops.skipVerify | default "false" | quote }}` (not required) so it does not break non-GitOps deployments.

---

## Finding 5: Files requiring changes

| File | Change |
|------|--------|
| `backend/src/storage/git_sync.py` | Add `git_skip_verify: bool` to `GitOpsConfig`; read `GIT_SKIP_VERIFY` env var; update `_build_git_env()` signature and logic; add `BatchMode=yes`, `ConnectTimeout=30` |
| `helm/chart-monitor/values.yaml` | Add `gitops.skipVerify: false` |
| `helm/chart-monitor/templates/configmap.yaml` | Add `GIT_SKIP_VERIFY` entry |
| `DEPLOY.md` | Document `GIT_SKIP_VERIFY` env var |
| `docs/docs/getting-started/connect-git.md` | Document the new option and when to use it |

---

## Finding 6: No TLS/HTTPS path exists in current code

**Decision**: The existing Git operations use SSH URLs exclusively (`git@...`). There is no HTTPS Git path in the codebase, so `GIT_SSL_NO_VERIFY` / `http.sslVerify=false` are not needed at this time.

**Alternatives considered**: Adding HTTPS support with `GIT_SSL_NO_VERIFY`: Deferred — SSH is the only transport currently used; HTTPS support is a separate future feature.

---

## Resolution Summary

All unknowns resolved. No NEEDS CLARIFICATION items remain. Implementation is straightforward: one Python file, one Helm values file, one Helm template, and two documentation files.
