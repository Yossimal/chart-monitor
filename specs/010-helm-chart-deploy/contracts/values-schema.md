# Contract: Helm Values Schema

**Feature**: 010-helm-chart-deploy | **Date**: 2026-04-19

This document defines the operator-facing contract for the `helm/chart-monitor` chart. Any change to a field name, type, or default is a breaking change requiring a chart version bump.

---

## Canonical `values.yaml`

```yaml
nameOverride: ""
fullnameOverride: ""
imagePullSecrets: []

backend:
  image:
    repository: "chart-monitor-backend"
    tag: "latest"
    pullPolicy: IfNotPresent
  replicaCount: 1
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"
  env: []
  extraEnvFrom: []
  service:
    type: ClusterIP
    port: 8000
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

frontend:
  image:
    repository: "chart-monitor-frontend"
    tag: "latest"
    pullPolicy: IfNotPresent
  replicaCount: 1
  resources:
    requests:
      cpu: "50m"
      memory: "64Mi"
    limits:
      cpu: "200m"
      memory: "256Mi"
  service:
    type: ClusterIP
    port: 80
  probes:
    liveness:
      httpGet:
        path: /
        port: http
      initialDelaySeconds: 10
      periodSeconds: 20
    readiness:
      httpGet:
        path: /
        port: http
      initialDelaySeconds: 5
      periodSeconds: 10

ingress:
  enabled: true
  className: ""
  annotations: {}
  host: "chart-monitor.local"
  tls: []

openshift:
  enabled: false
  route:
    host: ""
    tls:
      termination: edge
      insecureEdgeTerminationPolicy: Redirect

persistence:
  storageClass: ""
  accessMode: ReadWriteOnce
  size: 1Gi
  mountPath: /data

serviceAccount:
  name: ""
  annotations: {}

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000

containerSecurityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL

nodeSelector: {}
tolerations: []
affinity: {}
podAnnotations: {}
podLabels: {}
```

---

## OpenShift Override Example (`values-openshift.yaml`)

```yaml
openshift:
  enabled: true
  route:
    host: ""          # leave empty; OpenShift auto-assigns from cluster wildcard domain
    tls:
      termination: edge
      insecureEdgeTerminationPolicy: Redirect

ingress:
  enabled: false      # redundant when openshift.enabled=true, but explicit for clarity

podSecurityContext:
  runAsNonRoot: true
  runAsUser: null     # null = OpenShift assigns UID from namespace range
  fsGroup: null       # null = OpenShift assigns GID from namespace range
```

---

## Exposed Service Ports

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| `chart-monitor-backend` | `8000` | TCP/HTTP | FastAPI REST API |
| `chart-monitor-frontend` | `80` | TCP/HTTP | Static frontend |

Both Services are `ClusterIP`; external access is exclusively through Ingress or Route.

---

## Volume Mounts

| Resource | Mount Path | Source | Purpose |
|----------|-----------|--------|---------|
| Backend container | `/data` (configurable) | PVC `chart-monitor-backend-data` | Persistent application data |

---

## NOTES.txt Output Contract

After `helm install`, operators see:

```
chart-monitor has been deployed.

Access the UI at:
  http(s)://<host>

  On-prem (Ingress): http://{{ .Values.ingress.host }}
  OpenShift (Route): https://<auto-assigned or .Values.openshift.route.host>
```

---

## Breaking Change Policy

| Change Type | Version Bump |
|------------|--------------|
| Rename or remove a value key | MAJOR |
| Change a value's type or default in a behaviour-affecting way | MINOR |
| Add a new optional value with a safe default | PATCH |
| Template-only fix (no values changes) | PATCH |
