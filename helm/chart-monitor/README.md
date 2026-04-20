# chart-monitor Helm Chart

Deploys the chart-monitor backend and frontend to standard Kubernetes clusters and OpenShift.

## Prerequisites

| Requirement | On-prem Kubernetes | OpenShift |
|------------|-------------------|-----------|
| Helm 3.x | ✅ Required | ✅ Required |
| Kubernetes version | 1.24+ | 4.10+ |
| Ingress controller | ✅ Required (e.g., nginx-ingress) | ❌ Not needed |
| Storage provisioner | ✅ Required | ✅ Built-in |

> **Note**: A storage provisioner is a **hard prerequisite**. The chart always creates a PersistentVolumeClaim for the backend. On Docker Desktop, install [local-path-provisioner](https://github.com/rancher/local-path-provisioner).

## Quick Install

### On-prem Kubernetes

```bash
helm install chart-monitor helm/chart-monitor \
  --set backend.image.repository=<your-registry>/chart-monitor-backend \
  --set backend.image.tag=<version> \
  --set frontend.image.repository=<your-registry>/chart-monitor-frontend \
  --set frontend.image.tag=<version> \
  --set ingress.host=chart-monitor.example.com \
  -n chart-monitor --create-namespace
```

### OpenShift

```bash
helm install chart-monitor helm/chart-monitor \
  -f helm/chart-monitor/values-openshift.yaml \
  --set backend.image.repository=<your-registry>/chart-monitor-backend \
  --set backend.image.tag=<version> \
  --set frontend.image.repository=<your-registry>/chart-monitor-frontend \
  --set frontend.image.tag=<version> \
  -n chart-monitor --create-namespace
```

## Upgrade

```bash
helm upgrade chart-monitor helm/chart-monitor -f my-values.yaml -n chart-monitor
```

## Uninstall

```bash
helm uninstall chart-monitor -n chart-monitor
```

> **⚠️ PVC Retention**: The backend PersistentVolumeClaim is **not deleted** by `helm uninstall`. This is intentional to prevent data loss. To remove it:
> ```bash
> kubectl delete pvc -l app.kubernetes.io/instance=chart-monitor -n chart-monitor
> ```

## Minimum Recommended Resource Limits

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|------------|----------------|-----------|--------------|
| Backend   | 100m       | 128Mi          | 500m      | 512Mi        |
| Frontend  | 50m        | 64Mi           | 200m      | 256Mi        |

## Image Pull Secrets

If your registry requires authentication:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<user> \
  --docker-password=<password> \
  -n chart-monitor

helm install chart-monitor helm/chart-monitor \
  --set imagePullSecrets[0].name=regcred \
  ...
```

## StorageClass

By default, `persistence.storageClass` is empty, which uses the cluster's default StorageClass. To use a specific one:

```bash
helm install chart-monitor helm/chart-monitor \
  --set persistence.storageClass=my-storage-class \
  ...
```

## OpenShift Notes

- When `openshift.enabled=true`, an OpenShift Route (Edge TLS) is created instead of an Ingress.
- HTTP traffic is automatically redirected to HTTPS by the router.
- If UID 1000 is outside your namespace's allowed UID range, set `podSecurityContext.runAsUser: null` in values to let OpenShift assign the UID (this is already the default in `values-openshift.yaml`).
- To bind the ServiceAccount to an SCC:
  ```bash
  oc adm policy add-scc-to-user restricted-v2 -z chart-monitor -n chart-monitor
  ```

## Configuration Reference

See [`values.yaml`](values.yaml) for the full list of configurable parameters with inline documentation.
