# Feature Specification: Helm Chart Deployment

**Feature Branch**: `010-helm-chart-deploy`  
**Created**: 2026-04-19  
**Status**: Draft  
**Input**: User description: "helm chart for deploying the project; works with on-prem environment and OpenShift; provides route"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy to On-Prem Kubernetes (Priority: P1)

An operator deploys chart-monitor to a standard on-premises Kubernetes cluster using the Helm chart. They configure values (image, replicas, storage, etc.) via a `values.yaml` override and run a single `helm install` or `helm upgrade` command. The application becomes accessible through a Kubernetes Ingress.

**Why this priority**: The most common deployment target; validates that the chart's default behaviour works without any platform-specific extensions.

**Independent Test**: Deploy chart to a local/test Kubernetes cluster (e.g., kind or minikube), verify all pods reach Ready state, and confirm the UI is reachable via the configured Ingress host.

**Acceptance Scenarios**:

1. **Given** a Kubernetes cluster and a `values.yaml` with image references, **When** `helm install chart-monitor ./helm/chart-monitor` is run, **Then** backend and frontend Deployments, Services, and an Ingress are created and all pods reach Running status within 3 minutes.
2. **Given** a running installation, **When** `helm upgrade chart-monitor ./helm/chart-monitor --set replicaCount=2` is run, **Then** the rollout completes without downtime and the new replica count is active.
3. **Given** a running installation, **When** `helm uninstall chart-monitor` is run, **Then** all chart-owned resources are removed from the cluster.

---

### User Story 2 - Deploy to OpenShift (Priority: P1)

An operator deploys chart-monitor to an OpenShift cluster. The chart detects (or is told via a value) that the target is OpenShift and automatically creates an OpenShift Route instead of a Kubernetes Ingress, while also respecting OpenShift's security constraints (no root, appropriate Security Context Constraints).

**Why this priority**: OpenShift is an explicit requirement; the chart must be usable without manual post-install patching.

**Independent Test**: Deploy chart on an OpenShift cluster (or CRC), verify a Route object is created and the application is reachable via the Route URL.

**Acceptance Scenarios**:

1. **Given** an OpenShift cluster and `openshift.enabled=true` in values, **When** `helm install` is run, **Then** an OpenShift Route is created (no Ingress), pods start successfully under the cluster's default SCC.
2. **Given** the Route is created, **When** the Route hostname is opened in a browser, **Then** the chart-monitor UI loads correctly.
3. **Given** `openshift.enabled=false` on an OpenShift cluster, **Then** a standard Ingress is created instead of a Route (operator opt-out scenario).

---

### User Story 3 - Customise Deployment via Values (Priority: P2)

An operator customises the deployment — changing image tags, resource limits, environment variables, persistence settings, and replica counts — entirely through Helm values without modifying chart templates.

**Why this priority**: Enables GitOps-style configuration management and makes the chart reusable across environments (dev, staging, prod).

**Independent Test**: Override at least five distinct values and verify each change is reflected in the rendered manifests (`helm template`) and in the live deployment.

**Acceptance Scenarios**:

1. **Given** a `values.yaml` specifying a custom image tag, **When** the chart is rendered, **Then** the Deployment manifests reference the correct image.
2. **Given** resource limit values, **When** the chart is deployed, **Then** pods have the specified CPU/memory limits and requests.
3. **Given** extra environment variables in values, **When** pods start, **Then** those environment variables are present in the container environment.

---

### User Story 4 - Helm Lint and Dry-Run Pass (Priority: P2)

A developer runs `helm lint` and `helm install --dry-run` against the chart with both default values and an OpenShift-specific values override. Both commands exit without errors.

**Why this priority**: Gates CI pipelines; prevents broken charts from reaching clusters.

**Independent Test**: Run `helm lint ./helm/chart-monitor` and `helm install --dry-run chart-monitor ./helm/chart-monitor -f values-openshift.yaml` — both must exit 0 with no errors.

**Acceptance Scenarios**:

1. **Given** the default `values.yaml`, **When** `helm lint` is run, **Then** it exits with 0 warnings or errors.
2. **Given** an OpenShift values override file, **When** `helm lint -f values-openshift.yaml` is run, **Then** it exits cleanly.
3. **Given** `helm install --dry-run`, **Then** all expected resource kinds appear in the output.

---

### Edge Cases

- What happens when both `ingress.enabled=true` and `openshift.enabled=true` are set simultaneously? (Chart should prefer Route and warn/ignore Ingress flag.)
- What happens if the target namespace does not exist before install? (Chart should either create it or fail with a clear error message.)
- What happens when the image pull secret is missing? (Pod should fail with ImagePullBackOff; chart should document the required secret name.)
- What happens when resource limits are set lower than the application's actual requirements? (Pod OOMKilled; chart README should document minimum recommended limits.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chart MUST deploy the chart-monitor backend and frontend as separate workloads.
- **FR-002**: The chart MUST create a Kubernetes Service for each workload.
- **FR-003**: The chart MUST create a Kubernetes Ingress by default for external access.
- **FR-004**: When `openshift.enabled=true`, the chart MUST create an OpenShift Route instead of an Ingress.
- **FR-005**: The chart MUST allow the Route hostname to be set via a value; if unset, OpenShift assigns it automatically.
- **FR-005a**: The OpenShift Route MUST use Edge TLS termination by default; TLS terminates at the OpenShift router and cluster-internal traffic is plain HTTP.
- **FR-006**: The chart MUST NOT run any container as root by default.
- **FR-006a**: The chart MUST create a dedicated ServiceAccount for the workloads.
- **FR-006b**: The chart MUST create a namespace-scoped Role and RoleBinding granting the ServiceAccount only the permissions required to operate; no ClusterRole or ClusterRoleBinding shall be created.
- **FR-007**: All configurable parameters (image repository, tag, pull policy, replicas, resources, environment variables, labels, annotations) MUST be exposed as Helm values.
- **FR-008**: The chart MUST include a `values.yaml` with safe, working defaults suitable for a standard Kubernetes cluster.
- **FR-009**: The chart MUST include an example `values-openshift.yaml` override file demonstrating the OpenShift-specific configuration.
- **FR-010**: The chart MUST always create a PersistentVolumeClaim for the backend data directory; a storage provisioner is a hard prerequisite for installation.
- **FR-011**: The chart MUST expose liveness and readiness probe configuration through values.
- **FR-012**: `helm lint` MUST pass with zero errors against the chart's default values.
- **FR-013**: The chart MUST include a `NOTES.txt` that prints the URL (Ingress hostname or Route URL) after installation.

### Key Entities

- **Helm Chart**: The deployable package (`Chart.yaml`, `values.yaml`, templates directory) that describes the full chart-monitor deployment.
- **Backend Workload**: The Python/FastAPI service — Deployment + Service + optional PVC.
- **Frontend Workload**: The static JS/HTML frontend — Deployment + Service.
- **Ingress**: Standard Kubernetes resource for HTTP routing on non-OpenShift clusters.
- **OpenShift Route**: OpenShift-native resource providing external HTTP/HTTPS access, created in place of Ingress when targeting OpenShift.
- **Values**: User-supplied configuration overrides that customise the chart without modifying templates.
- **ServiceAccount**: A dedicated Kubernetes ServiceAccount created by the chart, used by all workload pods; scoped RBAC Role and RoleBinding are bound to it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A fresh deployment on a standard Kubernetes cluster completes successfully (all pods Running) within 5 minutes of `helm install`.
- **SC-002**: A fresh deployment on an OpenShift cluster creates an accessible Route and all pods reach Running within 5 minutes.
- **SC-003**: `helm lint` passes with zero errors on both default and OpenShift value sets.
- **SC-004**: An operator can customise image, replicas, and resource limits entirely via values with no template edits required.
- **SC-005**: The chart-monitor UI and API are reachable via the provisioned Ingress or Route URL after a default install.
- **SC-006**: `helm uninstall` removes all chart-managed resources without leaving orphaned objects.

## Clarifications

### Session 2026-04-19

- Q: What TLS termination mode should the OpenShift Route use? → A: Edge (TLS terminates at the OpenShift router; cluster-internal traffic is plain HTTP)
- Q: Should the backend PersistentVolumeClaim be created by default or opt-in? → A: Always on — PVC is always created; a storage provisioner is required
- Q: Should the chart create a ServiceAccount and RBAC resources? → A: ServiceAccount + namespace-scoped Role and RoleBinding (no cluster-level RBAC)
- Q: Should the chart include Prometheus metrics or monitoring resources? → A: No — chart includes no metrics endpoints or monitoring resources

## Assumptions

- The project consists of a backend service and a frontend service that are deployed as independent containers.
- A storage provisioner (e.g., local-path, NFS, OpenShift dynamic provisioner) MUST be available in the cluster; the chart always creates a PVC for the backend.
- Container images are pre-built and stored in an accessible registry; the chart does not build images.
- On-prem Kubernetes clusters have an Ingress controller installed (e.g., nginx-ingress); OpenShift clusters have their Route controller active.
- TLS/HTTPS termination is handled at the Ingress/Route level via cluster-managed certificates; the chart exposes the option but does not manage certificate issuance.
- The chart targets Helm 3 (no Tiller required).
- Minimum Kubernetes version: 1.24+; minimum OpenShift version: 4.10+.
