# Research: Helm Chart Deployment

**Feature**: 010-helm-chart-deploy | **Date**: 2026-04-19

---

## 1. Multi-Environment Toggle (on-prem vs OpenShift)

**Decision**: Explicit `openshift.enabled` boolean value; no auto-detection.

**Rationale**: Auto-detecting OpenShift (e.g., checking for `route.openshift.io` CRD) requires a `lookup` function that fails during `helm template` and `--dry-run` without cluster access, breaking CI pipelines. Explicit toggle is the established Helm community pattern used by charts like Bitnami and Grafana.

**Alternatives considered**:
- Auto-detect via `lookup`: fails in `helm template`/dry-run; rejected.
- Separate chart per platform: doubles maintenance burden; rejected.

**Implications**:
- `ingress.yaml` wrapped in `{{- if not .Values.openshift.enabled }}`
- `route.yaml` wrapped in `{{- if .Values.openshift.enabled }}`
- When both flags could be set simultaneously, Route takes precedence (Ingress suppressed)

---

## 2. OpenShift Route — Edge TLS Configuration

**Decision**: `tls.termination: edge` with `insecureEdgeTerminationPolicy: Redirect`.

**Rationale**: Edge termination is the standard OpenShift pattern for web applications. `insecureEdgeTerminationPolicy: Redirect` ensures HTTP requests are automatically upgraded to HTTPS — a security best practice that requires no application-level redirect logic.

**Route template excerpt**:
```yaml
apiVersion: route.openshift.io/v1
kind: Route
spec:
  host: {{ .Values.openshift.route.host | quote }}
  to:
    kind: Service
    name: {{ include "chart-monitor.frontend.fullname" . }}
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```

**Alternatives considered**:
- Passthrough: requires app to handle TLS; adds complexity; rejected.
- Re-encrypt: highest security but requires internal TLS cert management; deferred as opt-in future enhancement.

---

## 3. PersistentVolumeClaim — StorageClass from Values

**Decision**: `persistence.storageClass` value, defaulting to `""` (empty string = cluster default provisioner).

**Rationale**: Empty string in `storageClassName` instructs Kubernetes to use the cluster's default StorageClass, which is always available on properly configured clusters. This allows on-prem operators to use local-path/NFS and OpenShift operators to use the OpenShift dynamic provisioner without any value override.

**PVC template excerpt**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
spec:
  storageClassName: {{ .Values.persistence.storageClass | quote }}
  accessModes:
    - {{ .Values.persistence.accessMode | quote }}
  resources:
    requests:
      storage: {{ .Values.persistence.size | quote }}
```

**Note**: PVC is always created (no `if` guard). Operators must ensure a storage provisioner exists.

---

## 4. RBAC Pattern — Minimal Namespace-Scoped

**Decision**: ServiceAccount + Role (empty rules) + RoleBinding. The backend doesn't call the Kubernetes API, so no rules are needed. The Role exists for SCC binding in OpenShift (bind SA to an SCC via `oc adm policy add-scc-to-user`).

**Rationale**: chart-monitor reads from filesystem/Git; it does not call the K8s API. The Role object is created with empty rules (`rules: []`) to satisfy the "dedicated SA + RBAC" requirement while following least-privilege. On OpenShift, cluster admins bind the SA to `restricted-v2` SCC separately.

**Alternatives considered**:
- No RBAC at all: prevents per-SA SCC binding in OpenShift; rejected.
- ClusterRole: excessive scope; rejected per spec FR-006b.

---

## 5. Pod Security — Non-Root Defaults

**Decision**: `runAsNonRoot: true`, `runAsUser: 1000`, `fsGroup: 2000`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`. `readOnlyRootFilesystem: false` because the backend writes to the PVC mount path.

**Rationale**: These settings are compatible with OpenShift's `restricted-v2` SCC (the default since OCP 4.11) as long as `runAsUser` is within the namespace's UID range. Operators may need to override `runAsUser` on OpenShift if UID 1000 falls outside their namespace range.

**OpenShift note added to `values-openshift.yaml`**: Set `podSecurityContext.runAsUser` to `null` to let OpenShift assign the UID from the namespace range.

---

## 6. Helm Chart Metadata & Versioning

**Decision**: `Chart.yaml` with `apiVersion: v2`, semantic versioning starting at `0.1.0`, `appVersion` tracking the application release.

**Conventions**:
- Chart version bumps independently from appVersion
- No external chart dependencies (all resources self-contained)
- `.helmignore` excludes `*.md`, `tests/`, `specs/`
