# Tasks: Git HTTP Authentication Methods

**Input**: Design documents from `/specs/012-git-http-auth/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not explicitly requested — no test tasks included.

**Organization**: Tasks grouped by user story. Foundational phase covers all shared backend changes; US1 and US2 build on top of the foundation; US3 is the Helm chart restructure. Versioning is a Polish phase concern.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Different files, no blocking dependencies — safe to run in parallel
- **[US1]**: Connect via repository token (P1)
- **[US2]**: Connect via username + token (P2)
- **[US3]**: Select connection method via Helm values (P3)

---

## Phase 1: Setup

> No new project initialization required — all changes are to existing files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend changes shared by US1 and US2. Must complete before either HTTP story can be implemented or tested.

**⚠️ CRITICAL**: US1 and US2 cannot be implemented until this phase is complete.

- [x] T001 Update module docstring in `backend/src/storage/git_sync.py` to document `GIT_CONNECTION_METHOD`, `GIT_REPO_URL`, `GIT_HTTP_TOKEN`, and `GIT_HTTP_USERNAME` environment variables alongside the existing entries
- [x] T002 Add four new fields to `GitOpsConfig` dataclass in `backend/src/storage/git_sync.py`: `connection_method: str = "ssh"`, `git_repo_url: str = ""`, `git_http_token: str = ""`, `git_http_username: str = ""`
- [x] T003 Rewrite `load_gitops_config()` in `backend/src/storage/git_sync.py` to: (1) read `GIT_CONNECTION_METHOD` env var (default `"ssh"`), reject unknown values with a descriptive error; (2) for `ssh` require `GIT_SSH_URL` + `GIT_SSH_KEY_PATH`; (3) for `http-token`/`http-user-token` require `GIT_REPO_URL` + `GIT_HTTP_TOKEN`; (4) for `http-user-token` additionally require `GIT_HTTP_USERNAME`; (5) `GIT_TARGET_PATH` and `SYNC_SECRET` always required; (6) populate all new fields in the returned `GitOpsConfig`
- [x] T004 Add `_build_http_env(repo_url, token, username, skip_verify)` function to `backend/src/storage/git_sync.py`: parse hostname from `repo_url` with `urllib.parse.urlparse`; determine login (`username` if provided else `"oauth2"`); create temp dir with `tempfile.mkdtemp(prefix="chart-monitor-git-")`; write `$TMPDIR/.netrc` with content `machine <hostname> login <login> password <token>\n` and set permissions `0o600`; set `env["HOME"] = tmp_dir`; if `skip_verify` set `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=http.sslVerify`, `GIT_CONFIG_VALUE_0=false`; return `(env, tmp_dir)`
- [x] T005 Update `perform_sync()` in `backend/src/storage/git_sync.py` to branch on `cfg.connection_method`: for `ssh` call `_build_git_env(cfg.git_ssh_key_path, skip_verify=cfg.git_skip_verify)` and use `cfg.git_ssh_url` as clone/fetch URL (unchanged); for `http-token`/`http-user-token` call `_build_http_env(cfg.git_repo_url, cfg.git_http_token, cfg.git_http_username, cfg.git_skip_verify)` and use `cfg.git_repo_url` as URL; wrap HTTP git operations in `try/finally` that calls `shutil.rmtree(tmp_dir, ignore_errors=True)` to delete temp dir

**Checkpoint**: Foundational complete. Test with `GIT_CONNECTION_METHOD=ssh` (existing behaviour unchanged). Run backend with SSH env vars and confirm sync still works.

---

## Phase 3: User Story 1 — Connect via Repository Token (Priority: P1) 🎯 MVP

**Goal**: Operator sets `GIT_CONNECTION_METHOD=http-token`, `GIT_REPO_URL`, and `GIT_HTTP_TOKEN`; sync authenticates via temporary `.netrc` with `oauth2` as login.

**Independent Test**: Start backend with `GIT_CONNECTION_METHOD=http-token`, `GIT_REPO_URL=https://github.com/org/repo.git`, `GIT_HTTP_TOKEN=<valid-token>`, `GIT_TARGET_PATH=/tmp/store`, `SYNC_SECRET=test`; call `POST /api/v1/git/sync` and confirm sync completes. Verify no `.netrc` file remains in `/tmp` after sync.

### Implementation for User Story 1

> US1 is fully implemented by the Foundational phase (T001–T005) — the `http-token` branch in `perform_sync()` uses `git_http_username=""` which causes `_build_http_env()` to use `oauth2` as login automatically. No additional implementation tasks are needed for US1 beyond the foundation.

**Checkpoint**: US1 is complete after Foundational phase. Test independently per the Independent Test above.

---

## Phase 4: User Story 2 — Connect via Username + Token (Priority: P2)

**Goal**: Operator sets `GIT_CONNECTION_METHOD=http-user-token`, `GIT_REPO_URL`, `GIT_HTTP_TOKEN`, and `GIT_HTTP_USERNAME`; sync authenticates via temporary `.netrc` using the provided username.

**Independent Test**: Start backend with `GIT_CONNECTION_METHOD=http-user-token`, `GIT_REPO_URL=https://gitlab.internal/org/repo.git`, `GIT_HTTP_TOKEN=<token>`, `GIT_HTTP_USERNAME=svc-account`, `GIT_TARGET_PATH=/tmp/store`, `SYNC_SECRET=test`; call `POST /api/v1/git/sync`; confirm success and that `.netrc` used `login svc-account`.

> US2 is also fully implemented by the Foundational phase. The `http-user-token` branch passes `cfg.git_http_username` to `_build_http_env()`, which uses it as the `.netrc` login directly.

**Checkpoint**: US2 is complete after Foundational phase. Test with a Git server that requires a username.

---

## Phase 5: User Story 3 — Select Connection Method via Helm Values (Priority: P3)

**Goal**: `gitops.connection` selector in `values.yaml` drives which method is active; each method has its own nested section; SSH volume mount is conditional; versioning is bumped throughout.

**Independent Test**: Run `helm template ./helm/chart-monitor --set gitops.connection=http-token --set gitops.httpToken.url=https://example.com/repo.git` and confirm: (1) ConfigMap contains `GIT_CONNECTION_METHOD: "http-token"` and `GIT_REPO_URL: "https://example.com/repo.git"`; (2) no `ssh-key` volume mount appears. Repeat for `ssh` and `http-user-token`.

### Implementation for User Story 3

- [x] T006 Restructure `gitops:` block in `helm/chart-monitor/values.yaml`: replace flat `sshUrl`/`sshKeyMountPath`/`skipVerify` with nested structure containing `connection: ssh`, `ssh.url: ""`, `ssh.keyMountPath: "/app/secrets"`, `httpToken.url: ""`, `httpUserToken.url: ""`, `httpUserToken.username: ""`, `skipVerify: false`; preserve all existing comments and other values sections untouched
- [x] T007 Rewrite `data:` block in `helm/chart-monitor/templates/configmap.yaml`: remove `required` from `GIT_SSH_URL` entry; update path to `{{ .Values.gitops.ssh.url | default "" | quote }}`; update `GIT_SSH_KEY_PATH` to `{{ printf "%s/ssh-key" (.Values.gitops.ssh.keyMountPath | default "/app/secrets") | quote }}`; add `GIT_CONNECTION_METHOD: {{ .Values.gitops.connection | default "ssh" | quote }}`; add `GIT_REPO_URL: {{ coalesce .Values.gitops.httpToken.url .Values.gitops.httpUserToken.url "" | quote }}`; add `GIT_HTTP_USERNAME: {{ .Values.gitops.httpUserToken.username | default "" | quote }}`; update `GIT_SKIP_VERIFY` path to `{{ .Values.gitops.skipVerify | default "false" | quote }}`
- [x] T008 Wrap the `ssh-key` volumeMount in `helm/chart-monitor/templates/deployment.yaml` with `{{- if eq .Values.gitops.connection "ssh" }}` / `{{- end }}`; wrap the `ssh-key` volume definition the same way; update `mountPath` reference to `{{ .Values.gitops.ssh.keyMountPath | default "/app/secrets" }}`
- [x] T009 [P] Update `helm/chart-monitor/values-local.yaml` to use new nested structure: replace `gitops.sshUrl` with `gitops.connection: ssh` and `gitops.ssh.url: "git@github.com:Yossimal/chart-monitor-dashboards.git"`

**Checkpoint**: US3 complete. `helm template` renders correct ConfigMap and conditional volume for all three connection methods.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Version bumps, documentation, and migration guide.

- [x] T010 [P] Bump `version` from `0.1.0` to `0.2.0` and `appVersion` from `"latest"` to `"3.2.0"` in `helm/chart-monitor/Chart.yaml`
- [x] T011 [P] Bump `version` from `0.1.0` to `0.2.0` in `backend/pyproject.toml`
- [x] T012 [P] Bump FastAPI `version=` from `"0.1.0"` to `"0.2.0"` in `backend/src/main.py`
- [x] T013 [P] Update `DEPLOY.md`: add migration table (`gitops.sshUrl` → `gitops.ssh.url`, `gitops.sshKeyMountPath` → `gitops.ssh.keyMountPath`); add HTTP token secret creation example (`--from-literal=GIT_HTTP_TOKEN=<token>`); add HTTP user+token secret example; add per-method values snippets for `http-token` and `http-user-token`; add troubleshooting row for HTTP auth failures
- [x] T014 [P] Update `docs/docs/getting-started/connect-git.md`: add `GIT_CONNECTION_METHOD`, `GIT_REPO_URL`, `GIT_HTTP_TOKEN`, `GIT_HTTP_USERNAME` to env var table; add "Using HTTP token authentication" section; add "Using HTTP username + token" section; add 0.1.x → 0.2.0 migration note for SSH users

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 2 (Foundational)**: No dependencies — start immediately
- **Phase 3 (US1)**: Depends on Phase 2 completion — but adds no new tasks
- **Phase 4 (US2)**: Depends on Phase 2 completion — but adds no new tasks
- **Phase 5 (US3)**: Independent of Phases 3/4 — Helm chart changes can run in parallel with Phase 2
- **Phase 6 (Polish)**: Can start after Phase 5 (T006–T009 complete); version bumps (T010–T012) are fully independent

### Within Phase 2 (Foundational)

T001 → T002 → T003 → T004 → T005 (sequential, all in `git_sync.py`)

### Within Phase 5 (US3)

T006 → T007 (values before configmap, for consistency)  
T008 can run after T006 (deployment.yaml references values paths)  
T009 [P] can run any time (separate file, no dependencies)

### Within Phase 6 (Polish)

T010, T011, T012, T013, T014 are all fully parallel (different files).

### Parallel Opportunities

```bash
# Phase 5 can run in parallel with Phase 2:
Phase 2 (T001–T005, git_sync.py) || Phase 5 (T006–T009, Helm chart)

# Phase 6 all parallel:
T010 (Chart.yaml) || T011 (pyproject.toml) || T012 (main.py) || T013 (DEPLOY.md) || T014 (connect-git.md)
```

---

## Implementation Strategy

### MVP First (US1 — Repository Token Auth)

1. Complete Phase 2 (T001–T005) — backend reads `http-token` method and uses `.netrc`
2. **Validate**: `GIT_CONNECTION_METHOD=http-token` sync works locally
3. Stop here if Helm restructure is not yet needed

### Full Delivery

1. Phase 2: Foundational backend (T001–T005) **in parallel with** Phase 5: Helm chart (T006–T009)
2. Validate US1 and US2 independently
3. Validate US3 via `helm template`
4. Phase 6: Polish (T010–T014, all parallel)
5. Rebuild image, bump to 3.2.0, redeploy

### Parallel Team Strategy

- Developer A: Phase 2 (T001–T005, `git_sync.py`)
- Developer B: Phase 5 (T006–T009, Helm chart) + Phase 6 (T010–T014, docs/versions)

---

## Notes

- T001–T005 all modify `backend/src/storage/git_sync.py` — execute sequentially
- T006–T008 modify different Helm template files — T006 before T007/T008 for consistency but not a hard dependency
- T010–T014 are fully independent — parallelize freely
- US1 and US2 are implemented entirely by the Foundational phase; no additional code tasks needed
- After all tasks complete: rebuild Docker image tagged `3.2.0`, save tar, redeploy Helm with new chart version `0.2.0`
