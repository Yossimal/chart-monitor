# Quickstart: Deploying chart-monitor with Helm

**Feature**: 010-helm-chart-deploy | **Date**: 2026-04-19

---

## Prerequisites

| Requirement | On-prem Kubernetes | OpenShift |
|------------|-------------------|-----------|
| Helm 3.x | ✅ Required | ✅ Required |
| Kubernetes / OCP version | 1.24+ | 4.10+ |
| Ingress controller | ✅ Required (e.g., nginx-ingress) | ❌ Not needed |
| Route controller | ❌ Not needed | ✅ Built-in |
| Storage provisioner | ✅ Required | ✅ Required |
| Image registry access | ✅ Required | ✅ Required |

---

## On-Prem Kubernetes (Default)

```bash
# 1. Clone or download the chart
cd helm/chart-monitor

# 2. Customise values
cp values.yaml my-values.yaml
# Edit my-values.yaml: set backend.image.repository, frontend.image.repository, ingress.host

# 3. Install
helm install chart-monitor ./helm/chart-monitor -f my-values.yaml -n chart-monitor --create-namespace

# 4. Verify
kubectl get pods -n chart-monitor
kubectl get ingress -n chart-monitor
```

---

## OpenShift

```bash
# 1. Install with OpenShift values overlay
helm install chart-monitor ./helm/chart-monitor \
  -f helm/chart-monitor/values-openshift.yaml \
  -n chart-monitor --create-namespace

# 2. (Optional) Bind ServiceAccount to restricted-v2 SCC if required
oc adm policy add-scc-to-user restricted-v2 \
  -z chart-monitor -n chart-monitor

# 3. Verify
oc get pods -n chart-monitor
oc get route -n chart-monitor
```

---

## Upgrade

```bash
helm upgrade chart-monitor ./helm/chart-monitor -f my-values.yaml -n chart-monitor
```

---

## Uninstall

```bash
helm uninstall chart-monitor -n chart-monitor
# Note: PVC is NOT deleted automatically. To remove data:
kubectl delete pvc -l app.kubernetes.io/instance=chart-monitor -n chart-monitor
```

---

## Common Value Overrides

```bash
# Override image tags
helm upgrade chart-monitor ./helm/chart-monitor \
  --set backend.image.tag=1.2.3 \
  --set frontend.image.tag=1.2.3

# Use a specific StorageClass
helm upgrade chart-monitor ./helm/chart-monitor \
  --set persistence.storageClass=my-storage-class

# Scale backend
helm upgrade chart-monitor ./helm/chart-monitor \
  --set backend.replicaCount=3
```

---

## Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| Pod stuck in `Pending` | No storage provisioner | Set `persistence.storageClass` or install a provisioner |
| Pod stuck in `ImagePullBackOff` | Registry unreachable / missing pull secret | Set `imagePullSecrets` in values |
| Pod in `CrashLoopBackOff` on OpenShift | UID outside namespace range | Set `podSecurityContext.runAsUser: null` in values |
| No Route created on OpenShift | `openshift.enabled` not set | Add `--set openshift.enabled=true` |
| `helm lint` fails | Template syntax error | Run `helm lint --debug` for details |
