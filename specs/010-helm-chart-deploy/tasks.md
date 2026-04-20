# Tasks: Helm Chart Deployment

**Input**: Design documents from `/specs/010-helm-chart-deploy/`  
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Tests**: Runtime tests against the local Docker Desktop Kubernetes cluster are included per user request.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1–US4 from spec.md)

## Path Conventions

All chart files live under `helm/chart-monitor/` at the repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the chart skeleton — directory structure, metadata, and shared template helpers.

- [x] T001 Create `helm/chart-monitor/` directory structure: `Chart.yaml`, `values.yaml`, `.helmignore`, `templates/` folder
- [x] T002 [P] Write `helm/chart-monitor/Chart.yaml` — `apiVersion: v2`, `name: chart-monitor`, `version: 0.1.0`, `appVersion: latest`, `description: Deploy chart-monitor backend and frontend`
- [x] T003 [P] Write `helm/chart-monitor/.helmignore` — exclude `*.md`, `specs/`, `tests/`, `.git/`
- [x] T004 Write `helm/chart-monitor/templates/_helpers.tpl` — define named templates: `chart-monitor.fullname`, `chart-monitor.name`, `chart-monitor.labels`, `chart-monitor.selectorLabels`, `chart-monitor.backend.fullname`, `chart-monitor.frontend.fullname`, `chart-monitor.serviceAccountName`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: RBAC resources and canonical values that every subsequent template depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 [P] Write `helm/chart-monitor/templates/serviceaccount.yaml` — creates `ServiceAccount` named from `serviceAccount.name` (default: `{{ fullname }}`), adds `serviceAccount.annotations`
- [x] T006 [P] Write `helm/chart-monitor/templates/role.yaml` — namespace-scoped `Role`, `rules: []` (app does not call the Kubernetes API), uses standard Helm labels
- [x] T007 Write `helm/chart-monitor/templates/rolebinding.yaml` — binds `Role` (T006) to `ServiceAccount` (T005) within the release namespace
- [x] T008 Write `helm/chart-monitor/values.yaml` — canonical defaults from `specs/010-helm-chart-deploy/contracts/values-schema.md`: all `backend.*`, `frontend.*`, `ingress.*`, `openshift.*`, `persistence.*`, `serviceAccount.*`, `podSecurityContext.*`, `containerSecurityContext.*` fields

**Checkpoint**: Run `helm template helm/chart-monitor` — ServiceAccount, Role, RoleBinding must render without errors before proceeding.

---

## Phase 3: User Story 1 - Deploy to On-Prem Kubernetes (Priority: P1) 🎯 MVP

**Goal**: A single `helm install` on a standard Kubernetes cluster creates all resources and the UI is reachable via Ingress.

**Independent Test**: Deploy to Docker Desktop k8s, confirm all pods Running, Ingress created, UI accessible at configured host.

### Implementation for User Story 1

- [x] T009 [P] [US1] Write `helm/chart-monitor/templates/backend-pvc.yaml` — `PersistentVolumeClaim` always created (no `if` guard); `storageClassName: {{ .Values.persistence.storageClass | quote }}`; `accessModes`, `storage` from values; name: `{{ include "chart-monitor.backend.fullname" . }}-data`
- [x] T010 [P] [US1] Write `helm/chart-monitor/templates/backend-service.yaml` — `ClusterIP` Service; port from `backend.service.port` (default 8000); `targetPort: http`; selector from `chart-monitor.selectorLabels`
- [x] T011 [P] [US1] Write `helm/chart-monitor/templates/frontend-service.yaml` — `ClusterIP` Service; port from `frontend.service.port` (default 80); `targetPort: http`
- [x] T012 [US1] Write `helm/chart-monitor/templates/backend-deployment.yaml` — mounts PVC at `persistence.mountPath`; `podSecurityContext` and `containerSecurityContext` from values; `env` + `extraEnvFrom` from values; liveness + readiness probes from `backend.probes.*`; `serviceAccountName` from helper; `replicaCount` and `resources` from values
- [x] T013 [US1] Write `helm/chart-monitor/templates/frontend-deployment.yaml` — `podSecurityContext` and `containerSecurityContext` from values; liveness + readiness probes from `frontend.probes.*`; `serviceAccountName` from helper; `replicaCount` and `resources` from values
- [x] T014 [US1] Write `helm/chart-monitor/templates/ingress.yaml` — wrapped in `{{- if not .Values.openshift.enabled }}`; `ingressClassName`, `annotations`, `host`, `tls` all from `ingress.*` values; routes `/` to frontend Service and `/api` to backend Service
- [x] T015 [US1] Write `helm/chart-monitor/templates/NOTES.txt` — prints post-install access URL: Ingress host when `openshift.enabled=false`; OpenShift Route hostname when `openshift.enabled=true`

### Runtime Tests for User Story 1 (Docker Desktop k8s)

- [x] T016 [US1] Runtime test — `helm install chart-monitor helm/chart-monitor -n chart-monitor --create-namespace`; assert: backend pod Running, frontend pod Running, PVC Bound, Ingress created; record test result in `specs/010-helm-chart-deploy/test-results/us1-install.md`
- [x] T017 [US1] Runtime test — `helm upgrade chart-monitor helm/chart-monitor --set backend.replicaCount=2 -n chart-monitor`; assert: 2 backend pods Running without downtime; record in `specs/010-helm-chart-deploy/test-results/us1-upgrade.md`
- [x] T018 [US1] Runtime test — `helm uninstall chart-monitor -n chart-monitor`; assert: Deployment, Service, Ingress, SA, Role, RoleBinding deleted; PVC still present; record in `specs/010-helm-chart-deploy/test-results/us1-uninstall.md`

**Checkpoint**: All three runtime tests pass — User Story 1 is independently verified.

---

## Phase 4: User Story 2 - Deploy to OpenShift (Priority: P1)

**Goal**: `helm install` with `openshift.enabled=true` creates an Edge TLS Route (no Ingress) and pods start under OpenShift's default SCC.

**Independent Test**: On OpenShift (or CRC), `oc get route` shows the Route; Route URL returns the UI.

### Implementation for User Story 2

- [x] T019 [US2] Write `helm/chart-monitor/templates/route.yaml` — wrapped in `{{- if .Values.openshift.enabled }}`; `apiVersion: route.openshift.io/v1`; `kind: Route`; `spec.host` from `openshift.route.host` (empty = OpenShift auto-assign); `spec.to` targets frontend Service; `spec.tls.termination: edge`; `spec.tls.insecureEdgeTerminationPolicy: Redirect`
- [x] T020 [US2] Write `helm/chart-monitor/values-openshift.yaml` — sets `openshift.enabled: true`, `ingress.enabled: false`, `podSecurityContext.runAsUser: null`, `podSecurityContext.fsGroup: null` (OpenShift assigns UID/GID from namespace range)

**Checkpoint**: `helm template helm/chart-monitor -f helm/chart-monitor/values-openshift.yaml` — Route present, Ingress absent.

---

## Phase 5: User Story 3 - Customise Deployment via Values (Priority: P2)

**Goal**: Operators override image tags, replicas, resources, storage, and env vars entirely through values with no template edits.

**Independent Test**: Deploy with 5+ value overrides on Docker Desktop k8s; verify `helm template` output and live pod state match overrides.

### Implementation for User Story 3

- [x] T021 [P] [US3] Verify `helm/chart-monitor/templates/backend-deployment.yaml` correctly templates: `backend.env` as `env:` entries, `backend.extraEnvFrom` as `envFrom:`, `backend.resources` as container `resources:`, `backend.replicaCount` as `replicas:`, `backend.image.repository`/`tag`/`pullPolicy` — fix any gaps
- [x] T022 [P] [US3] Verify `helm/chart-monitor/templates/frontend-deployment.yaml` correctly templates: `frontend.resources`, `frontend.replicaCount`, `frontend.image.*` — fix any gaps
- [x] T023 [US3] Verify `helm/chart-monitor/templates/backend-pvc.yaml` correctly templates `persistence.storageClass`, `persistence.size`, `persistence.accessMode` — fix any gaps

### Runtime Test for User Story 3 (Docker Desktop k8s)

- [x] T024 [US3] Runtime test — deploy with overrides: `backend.image.tag=0.9.0`, `backend.replicaCount=2`, `backend.resources.limits.memory=256Mi`, `persistence.size=2Gi`, `backend.env[0].name=MY_VAR backend.env[0].value=hello`; assert all 5 overrides are reflected in live pod/PVC state; record in `specs/010-helm-chart-deploy/test-results/us3-values.md`

**Checkpoint**: Runtime test passes — all 5 value overrides verified in the cluster.

---

## Phase 6: User Story 4 - Helm Lint and Dry-Run Pass (Priority: P2)

**Goal**: `helm lint` and `helm install --dry-run` exit cleanly for both default and OpenShift value sets.

**Independent Test**: Both lint commands exit 0; dry-run output contains all expected resource kinds.

### Implementation & Validation for User Story 4

- [x] T025 [P] [US4] Run `helm lint helm/chart-monitor` with default values; fix all reported errors and warnings until exit code is 0
- [x] T026 [P] [US4] Run `helm lint helm/chart-monitor -f helm/chart-monitor/values-openshift.yaml`; fix all errors until exit code is 0
- [x] T027 [US4] Run `helm install --dry-run chart-monitor helm/chart-monitor`; assert output contains: `Deployment` (×2), `Service` (×2), `Ingress`, `PersistentVolumeClaim`, `ServiceAccount`, `Role`, `RoleBinding`; no `Route`
- [x] T028 [US4] Run `helm install --dry-run chart-monitor helm/chart-monitor -f helm/chart-monitor/values-openshift.yaml`; assert output contains `Route`; assert output does NOT contain `Ingress`

**Checkpoint**: All four lint/dry-run commands pass — User Story 4 complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, documentation, and final validation across all stories.

- [x] T029 [P] Test edge case: deploy with both `ingress.enabled=true` and `openshift.enabled=true`; assert `helm template` produces Route but no Ingress (verify `not .Values.openshift.enabled` guard in `ingress.yaml` is the sole gate)
- [x] T030 [P] Write `helm/chart-monitor/README.md` — document prerequisites, minimum recommended resource limits (backend: 128Mi/100m, frontend: 64Mi/50m), storage provisioner requirement, image pull secret setup, and PVC retention behavior after uninstall
- [x] T031 Validate `NOTES.txt` output for both install scenarios: run `helm install --dry-run` for on-prem and OpenShift values, confirm printed URL is correct for each case
- [x] T032 Create `specs/010-helm-chart-deploy/test-results/` directory and add a `README.md` summarising all runtime test outcomes for traceability

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Requires Phase 1 — **blocks all user story phases**
- **US1 (Phase 3)**: Requires Phase 2 — 🎯 MVP milestone
- **US2 (Phase 4)**: Requires Phase 2 — independent of US1
- **US3 (Phase 5)**: Requires Phase 2 and Phase 3 templates (extends, doesn't replace)
- **US4 (Phase 6)**: Requires all implementation phases (3, 4, 5) to be complete before meaningful lint
- **Polish (Phase 7)**: Requires all user story phases

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational — no story dependencies
- **US2 (P1)**: Starts after Foundational — independent of US1 (adds `route.yaml`, `values-openshift.yaml` only)
- **US3 (P2)**: Starts after US1 templates exist — verifies and fixes value templating
- **US4 (P2)**: Starts after US1 + US2 + US3 complete — validates the full chart

### Parallel Opportunities

- T002, T003 can run in parallel (Phase 1)
- T005, T006 can run in parallel (Phase 2)
- T009, T010, T011 can run in parallel (Phase 3 — different files)
- T016, T017, T018 are sequential (runtime tests — each depends on previous state)
- T021, T022 can run in parallel (Phase 5 — different files)
- T025, T026 can run in parallel (Phase 6 — independent lint runs)
- T027, T028 can run in parallel (Phase 6 — independent dry-run runs)
- T029, T030 can run in parallel (Phase 7)

---

## Parallel Example: User Story 1 Setup

```bash
# Phase 3 — start these three simultaneously (different files):
Task T009: Write backend-pvc.yaml
Task T010: Write backend-service.yaml
Task T011: Write frontend-service.yaml

# Then, once T009–T011 complete:
Task T012: Write backend-deployment.yaml  (references PVC)
Task T013: Write frontend-deployment.yaml
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T008) — **critical gate**
3. Complete Phase 3: User Story 1 (T009–T018)
4. **STOP and VALIDATE**: Run Docker Desktop k8s runtime tests (T016–T018)
5. Demo on-prem deployment

### Incremental Delivery

1. Setup + Foundational → chart skeleton ready
2. US1 → on-prem deploy works, runtime-tested on Docker Desktop k8s (MVP!)
3. US2 → OpenShift Route support added
4. US3 → full values customisation verified
5. US4 → lint/dry-run CI gate green
6. Polish → docs, edge cases, traceability

### Parallel Team Strategy

With two developers after Phase 2:
- Developer A: US1 (Phase 3) — on-prem deploy + runtime tests
- Developer B: US2 (Phase 4) — OpenShift Route template

---

## Notes

- [P] tasks = different files, no incomplete-task dependencies — safe to run in parallel
- [Story] label maps each task to its user story for traceability
- Runtime tests (T016–T018, T024) require Docker Desktop with Kubernetes enabled and a local storage provisioner (e.g., `rancher/local-path-provisioner`)
- PVC is NOT deleted by `helm uninstall` — this is intentional Kubernetes behavior; document prominently
- `persistence.storageClass: ""` (empty string) uses the cluster default StorageClass — valid on Docker Desktop k8s and OpenShift
- Commit after each phase checkpoint
