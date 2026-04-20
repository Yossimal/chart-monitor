# Runtime Test Results: Helm Chart Deployment

**Feature**: 010-helm-chart-deploy  
**Environment**: Docker Desktop Kubernetes (local)

## Test Summary

| Test | File | Status | Notes |
|------|------|--------|-------|
| US1 — Install | [us1-install.md](us1-install.md) | PENDING | Requires Docker Desktop k8s + images |
| US1 — Upgrade | [us1-upgrade.md](us1-upgrade.md) | PENDING | Run after install test passes |
| US1 — Uninstall | [us1-uninstall.md](us1-uninstall.md) | PENDING | Run after upgrade test passes |
| US3 — Value Overrides | [us3-values.md](us3-values.md) | PENDING | Requires Docker Desktop k8s + images |

## Static Validation Results (Completed)

These validations run without a live cluster and have all passed:

| Check | Command | Result |
|-------|---------|--------|
| `helm template` (default) | `helm template chart-monitor helm/chart-monitor` | ✅ PASS — 9 resources |
| `helm template` (OpenShift) | `helm template ... -f values-openshift.yaml` | ✅ PASS — Route present, Ingress absent |
| `helm lint` (default) | `helm lint helm/chart-monitor` | ✅ PASS — 0 errors |
| `helm lint` (OpenShift) | `helm lint ... -f values-openshift.yaml` | ✅ PASS — 0 errors |
| `helm install --dry-run` (default) | All expected kinds present | ✅ PASS |
| `helm install --dry-run` (OpenShift) | Route present, Ingress absent | ✅ PASS |
| Edge case: both flags true | Route wins, Ingress suppressed | ✅ PASS |
| Value overrides: 5 overrides | All reflected in `helm template` output | ✅ PASS |
| NOTES.txt (on-prem) | Shows Ingress URL | ✅ PASS |
| NOTES.txt (OpenShift) | Shows `oc get route` command | ✅ PASS |

## Prerequisites for Runtime Tests

1. Docker Desktop with Kubernetes enabled
2. Install [local-path-provisioner](https://github.com/rancher/local-path-provisioner) for PVC support
3. Build and push the backend and frontend container images to a registry accessible from Docker Desktop
