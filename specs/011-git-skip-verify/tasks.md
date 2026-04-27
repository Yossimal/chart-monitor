# Tasks: Git Skip-Verify for SSH Connection

**Input**: Design documents from `/specs/011-git-skip-verify/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by user story. US1 (backend behaviour) and US2 (Helm configuration surface) are independently testable and can be implemented sequentially. All changes are modifications to existing files; no new files are created except in docs.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[US1]**: Enable Skip-Verify During Deployment (P1)
- **[US2]**: Configure Skip-Verify via Deployment Parameters (P2)

---

## Phase 1: Setup

> No project initialization required — this feature modifies existing files only.

---

## Phase 2: Foundational (Blocking Prerequisites)

> No shared foundational layer required. US1 changes are self-contained in `git_sync.py`; US2 changes are self-contained in the Helm chart. No phase 2 tasks.

---

## Phase 3: User Story 1 — Enable Skip-Verify During Deployment (Priority: P1) 🎯 MVP

**Goal**: The backend reads `GIT_SKIP_VERIFY` from the environment and adjusts the SSH command accordingly, with `BatchMode=yes` and `ConnectTimeout=30` added unconditionally.

**Independent Test**: Start the backend with `GIT_SKIP_VERIFY=true` and all other GitOps env vars set; call `POST /api/v1/git/sync` and confirm it succeeds against a server with a non-trusted host key. Without `GIT_SKIP_VERIFY` (or set to `false`), the SSH command uses `StrictHostKeyChecking=accept-new`.

### Implementation for User Story 1

- [x] T001 [US1] Add `git_skip_verify: bool = False` field to `GitOpsConfig` dataclass in `backend/src/storage/git_sync.py` (after the `sync_secret` field)
- [x] T002 [US1] In `load_gitops_config()` in `backend/src/storage/git_sync.py`, read `GIT_SKIP_VERIFY` env var and parse it: `git_skip_verify = os.environ.get("GIT_SKIP_VERIFY", "").lower() in ("true", "1", "yes")`; pass it to the `GitOpsConfig(...)` constructor
- [x] T003 [US1] Update `_build_git_env(key_path, skip_verify=False)` in `backend/src/storage/git_sync.py` to accept a `skip_verify: bool` parameter; set `host_check = "no" if skip_verify else "accept-new"`; build the SSH command as: `ssh -i "{safe_key_path}" -o StrictHostKeyChecking={host_check} -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=30`
- [x] T004 [US1] Update the `_build_git_env(cfg.git_ssh_key_path)` call inside `perform_sync()` in `backend/src/storage/git_sync.py` to pass `skip_verify=cfg.git_skip_verify`
- [x] T005 [US1] Update the module docstring in `backend/src/storage/git_sync.py` to add `GIT_SKIP_VERIFY` to the environment variable table: `GIT_SKIP_VERIFY : Set to "true" to bypass SSH host key verification (on-prem use). Defaults to false.`

**Checkpoint**: US1 is complete. Verify by running `backend/src/storage/git_sync.py` in isolation with `GIT_SKIP_VERIFY=true` and checking the constructed `GIT_SSH_COMMAND` value contains `StrictHostKeyChecking=no BatchMode=yes ConnectTimeout=30`. Without the flag, confirm `StrictHostKeyChecking=accept-new`.

---

## Phase 4: User Story 2 — Configure Skip-Verify via Deployment Parameters (Priority: P2)

**Goal**: Operators can set `gitops.skipVerify: true` in Helm values (or pass `GIT_SKIP_VERIFY=true` directly as an env var) to enable skip-verify without modifying source code. Toggling the value and running `helm upgrade` takes effect on the next pod restart.

**Independent Test**: Run `helm template ./helm/chart-monitor --set gitops.sshUrl=git@example.com:org/repo.git --set gitops.skipVerify=true | grep GIT_SKIP_VERIFY` and confirm the ConfigMap renders `GIT_SKIP_VERIFY: "true"`. Run again with `skipVerify=false` and confirm `GIT_SKIP_VERIFY: "false"`.

### Implementation for User Story 2

- [x] T006 [P] [US2] Add `skipVerify: false` under the `gitops:` block in `helm/chart-monitor/values.yaml` (after `sshKeyMountPath`), with a comment: `# Set to true to bypass SSH host key verification for on-prem Git servers`
- [x] T007 [P] [US2] Add `GIT_SKIP_VERIFY: {{ .Values.gitops.skipVerify | default "false" | quote }}` to the `data:` block of `helm/chart-monitor/templates/configmap.yaml` (after the `GIT_SSH_KEY_PATH` line)

**Checkpoint**: US2 is complete. `helm template` output confirms the ConfigMap carries the correct `GIT_SKIP_VERIFY` value from `values.yaml`. Both `true` and `false` render correctly.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation so operators know the option exists and when to use it.

- [x] T008 [P] Update `DEPLOY.md` to document `GIT_SKIP_VERIFY` in the environment variables section: describe the accepted values (`true`/`false`), the default (`false`), and add an "On-premises Git servers" callout explaining when to set it to `true` and the security implication
- [x] T009 [P] Update `docs/docs/getting-started/connect-git.md` to add a section "Using a self-signed or on-prem Git server" explaining `GIT_SKIP_VERIFY=true`, when to use it, how to set it via Helm (`gitops.skipVerify: true`), and a security note (only use on trusted networks)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 3 (US1)**: No dependencies — start immediately (T001 → T002 → T003 → T004 → T005 in sequence, same file)
- **Phase 4 (US2)**: No hard dependency on US1 (Helm chart changes are independent of backend); can be done in parallel with Phase 3 if desired. T006 and T007 are parallel to each other.
- **Phase 5 (Polish)**: Should follow Phase 3 and 4 completion; T008 and T009 are parallel to each other.

### Within User Story 1

T001 → T002 → T003 → T004 (sequential, all in the same file)  
T005 can be done at any point alongside the others (docstring only, no code dependency)

### Within User Story 2

T006 and T007 are fully parallel (different files, no shared state).

### Parallel Opportunities

```bash
# Phase 4 and Phase 5 documentation can run in parallel:
T006 (values.yaml) || T007 (configmap.yaml)

# Polish tasks are fully parallel:
T008 (DEPLOY.md) || T009 (connect-git.md)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 3 (T001–T005) — backend reads and applies `GIT_SKIP_VERIFY`
2. **Validate**: Set `GIT_SKIP_VERIFY=true` locally and confirm sync succeeds against on-prem Git server
3. Stop here if Helm deployment is not yet needed

### Full Delivery

1. Phase 3: US1 backend changes (T001–T005)
2. Phase 4: US2 Helm chart changes (T006–T007, parallel)
3. Phase 5: Documentation (T008–T009, parallel)
4. Total: 9 tasks, ~1–2 hours

---

## Notes

- [P] tasks = different files, no shared state — safe to execute in parallel
- T001–T004 all modify `backend/src/storage/git_sync.py` — execute sequentially; do not split across parallel agents
- T006 and T007 modify different Helm chart files — safe to parallelize
- T008 and T009 modify different documentation files — safe to parallelize
- No new files are created (except potentially an added section in existing docs)
- Commit after Phase 3 checkpoint and after Phase 4 checkpoint for clean bisect history
