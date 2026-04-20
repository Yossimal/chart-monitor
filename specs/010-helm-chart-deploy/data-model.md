# Data Model: Helm Chart Values Schema

**Feature**: 010-helm-chart-deploy | **Date**: 2026-04-19

The "data model" for a Helm chart is its values schema — the structured configuration surface exposed to operators.

---

## Top-Level Structure

```
values
├── nameOverride          string     Override chart name component in resource names
├── fullnameOverride      string     Override full resource name prefix
├── imagePullSecrets      []object   List of image pull secret references
│
├── backend               object     Backend workload configuration
├── frontend              object     Frontend workload configuration
│
├── ingress               object     Kubernetes Ingress (on-prem)
├── openshift             object     OpenShift Route configuration
│
├── persistence           object     PVC configuration (always created)
├── serviceAccount        object     ServiceAccount + RBAC
│
├── podSecurityContext    object     Pod-level security context
├── containerSecurityContext object  Container-level security context
│
├── nodeSelector          object     Node scheduling constraints
├── tolerations           []object   Tolerations
├── affinity              object     Affinity rules
├── podAnnotations        object     Extra pod annotations
└── podLabels             object     Extra pod labels
```

---

## Backend Workload (`backend.*`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backend.image.repository` | string | `"chart-monitor-backend"` | Container image repository |
| `backend.image.tag` | string | `"latest"` | Image tag |
| `backend.image.pullPolicy` | string | `"IfNotPresent"` | Image pull policy |
| `backend.replicaCount` | int | `1` | Number of pod replicas |
| `backend.resources.requests.cpu` | string | `"100m"` | CPU request |
| `backend.resources.requests.memory` | string | `"128Mi"` | Memory request |
| `backend.resources.limits.cpu` | string | `"500m"` | CPU limit |
| `backend.resources.limits.memory` | string | `"512Mi"` | Memory limit |
| `backend.env` | []object | `[]` | Extra environment variables (`name`/`value` pairs) |
| `backend.extraEnvFrom` | []object | `[]` | EnvFrom sources (ConfigMap/Secret refs) |
| `backend.service.type` | string | `"ClusterIP"` | Service type |
| `backend.service.port` | int | `8000` | Service port |
| `backend.probes.liveness` | object | See below | Liveness probe spec |
| `backend.probes.readiness` | object | See below | Readiness probe spec |

**Default probes**:
```yaml
backend:
  probes:
    liveness:
      httpGet:
        path: /health
        port: http
      initialDelaySeconds: 15
      periodSeconds: 20
    readiness:
      httpGet:
        path: /health
        port: http
      initialDelaySeconds: 5
      periodSeconds: 10
```

---

## Frontend Workload (`frontend.*`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `frontend.image.repository` | string | `"chart-monitor-frontend"` | Container image repository |
| `frontend.image.tag` | string | `"latest"` | Image tag |
| `frontend.image.pullPolicy` | string | `"IfNotPresent"` | Image pull policy |
| `frontend.replicaCount` | int | `1` | Number of pod replicas |
| `frontend.resources.requests.cpu` | string | `"50m"` | CPU request |
| `frontend.resources.requests.memory` | string | `"64Mi"` | Memory request |
| `frontend.resources.limits.cpu` | string | `"200m"` | CPU limit |
| `frontend.resources.limits.memory` | string | `"256Mi"` | Memory limit |
| `frontend.service.type` | string | `"ClusterIP"` | Service type |
| `frontend.service.port` | int | `80` | Service port |
| `frontend.probes.liveness` | object | `httpGet / path: /` | Liveness probe spec |
| `frontend.probes.readiness` | object | `httpGet / path: /` | Readiness probe spec |

---

## Ingress (`ingress.*`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ingress.enabled` | bool | `true` | Create Ingress (suppressed when `openshift.enabled=true`) |
| `ingress.className` | string | `""` | IngressClass name |
| `ingress.annotations` | object | `{}` | Extra annotations |
| `ingress.host` | string | `"chart-monitor.local"` | Ingress hostname |
| `ingress.tls` | []object | `[]` | TLS secret references |

**Constraint**: When `openshift.enabled=true`, this block is ignored regardless of `ingress.enabled`.

---

## OpenShift (`openshift.*`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `openshift.enabled` | bool | `false` | Create Route instead of Ingress |
| `openshift.route.host` | string | `""` | Route hostname; empty = auto-assigned by OpenShift |
| `openshift.route.tls.termination` | string | `"edge"` | TLS termination mode |
| `openshift.route.tls.insecureEdgeTerminationPolicy` | string | `"Redirect"` | HTTP→HTTPS redirect policy |

---

## Persistence (`persistence.*`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `persistence.storageClass` | string | `""` | StorageClass name; empty = cluster default |
| `persistence.accessMode` | string | `"ReadWriteOnce"` | PVC access mode |
| `persistence.size` | string | `"1Gi"` | Storage request size |
| `persistence.mountPath` | string | `"/data"` | Mount path inside backend container |

**Invariant**: PVC is always created. No conditional guard. Cluster must have a storage provisioner.

---

## ServiceAccount & RBAC (`serviceAccount.*`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `serviceAccount.name` | string | `""` | SA name; empty = `{{ fullname }}` |
| `serviceAccount.annotations` | object | `{}` | Annotations on the SA (e.g., IAM role ARN) |

**Created resources**:
- `ServiceAccount` — named SA used by all pods
- `Role` — namespace-scoped; `rules: []` (app doesn't call K8s API)
- `RoleBinding` — binds Role to SA

---

## Security Contexts

### Pod Security Context (`podSecurityContext.*`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `podSecurityContext.runAsNonRoot` | bool | `true` | Reject root UID |
| `podSecurityContext.runAsUser` | int | `1000` | UID for all containers (set to `null` on OpenShift to use namespace range) |
| `podSecurityContext.fsGroup` | int | `2000` | GID for volume mounts |

### Container Security Context (`containerSecurityContext.*`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `containerSecurityContext.allowPrivilegeEscalation` | bool | `false` | Block privilege escalation |
| `containerSecurityContext.capabilities.drop` | []string | `["ALL"]` | Drop all Linux capabilities |

---

## State Transitions

| Event | Resources Created | Resources Removed |
|-------|-------------------|-------------------|
| `helm install` | All 12–14 resources | — |
| `helm upgrade` | Updated in-place | Resources removed from chart |
| `helm uninstall` | — | All chart-owned resources (PVC retained by default K8s behavior unless `--cascade=background`) |

**Note**: PVC is not deleted by `helm uninstall` by default (Kubernetes retains PVCs for data safety). Operators must delete the PVC manually if data should be purged.
