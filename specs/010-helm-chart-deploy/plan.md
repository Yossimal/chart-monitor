# Implementation Plan: Helm Chart Deployment

**Branch**: `010-helm-chart-deploy` | **Date**: 2026-04-19 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/010-helm-chart-deploy/spec.md`

## Summary

Package chart-monitor (Python/FastAPI backend + Vanilla JS frontend) as a production-ready Helm 3 chart that deploys to both standard on-prem Kubernetes (1.24+) and OpenShift (4.10+). The chart toggles between a Kubernetes Ingress and an OpenShift Route (Edge TLS) via `openshift.enabled`, always provisions a backend PersistentVolumeClaim (StorageClass from values), and creates a dedicated ServiceAccount with a namespace-scoped Role and RoleBinding.

## Technical Context

**Language/Version**: YAML / Helm Go templates, Helm 3.x  
**Primary Dependencies**: Helm 3, Kubernetes API 1.24+, `route.openshift.io/v1` (OpenShift 4.10+)  
**Storage**: PersistentVolumeClaim — StorageClass driven by `persistence.storageClass` value (empty = cluster default)  
**Testing**: `helm lint`, `helm template`, `helm install --dry-run`  
**Target Platform**: On-prem Kubernetes 1.24+ and OpenShift 4.10+  
**Project Type**: Helm chart (infrastructure packaging)  
**Performance Goals**: All pods Running within 5 minutes of `helm install`  
**Constraints**: No ClusterRole/ClusterRoleBinding; no root containers; PVC always created; no monitoring resources  
**Scale/Scope**: 2 workloads, ~14 Kubernetes resource templates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Dynamic Data Engine | N/A | Chart packages the app; doesn't change engine behavior |
| II. Storage Agnostic / GitOps First | **PASS** | Chart is the GitOps delivery artifact; values.yaml enables GitOps workflows |
| III. Strict Typing / Clean Code | N/A | Helm templates are YAML — Python/TS rules don't apply |
| IV. Secure Execution Sandbox | N/A | Chart doesn't change sandbox behavior |
| V. Vanilla Desktop-First UI | N/A | Chart doesn't change UI layer |

**Gate result: PASS** — no violations; no Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/010-helm-chart-deploy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (values schema)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── values-schema.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
helm/
└── chart-monitor/
    ├── Chart.yaml                  # Chart metadata, appVersion, dependencies
    ├── values.yaml                 # Default values (on-prem defaults)
    ├── values-openshift.yaml       # OpenShift override example
    ├── .helmignore
    └── templates/
        ├── _helpers.tpl            # Named template helpers (fullname, labels, etc.)
        ├── NOTES.txt               # Post-install URL output
        ├── serviceaccount.yaml     # Dedicated ServiceAccount
        ├── role.yaml               # Namespace-scoped Role
        ├── rolebinding.yaml        # RoleBinding → ServiceAccount
        ├── backend-deployment.yaml # Backend Deployment
        ├── backend-service.yaml    # Backend ClusterIP Service
        ├── backend-pvc.yaml        # Backend PersistentVolumeClaim (always created)
        ├── frontend-deployment.yaml# Frontend Deployment
        ├── frontend-service.yaml   # Frontend ClusterIP Service
        ├── ingress.yaml            # Ingress (when openshift.enabled=false)
        └── route.yaml              # OpenShift Route (when openshift.enabled=true)
```

**Structure Decision**: Single Helm chart at `helm/chart-monitor/` co-located with the existing `backend/` and `frontend/` directories. All templates are flat under `templates/` (no subdirectories) for Helm compatibility.
