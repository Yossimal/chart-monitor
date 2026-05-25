# chart-monitor Helm Chart

Deploys the chart-monitor backend and frontend to standard Kubernetes clusters and OpenShift.

**Chart version**: 0.2.0 | **App version**: 3.3.0

## Prerequisites

| Requirement | On-prem Kubernetes | OpenShift |
|------------|-------------------|-----------|
| Helm 3.x | ✅ Required | ✅ Required |
| Kubernetes version | 1.24+ | 4.10+ |
| Ingress controller | ✅ Required (e.g., nginx-ingress) | ❌ Not needed (Route used) |
| Storage provisioner | ✅ Required | ✅ Built-in |

> **Note**: A storage provisioner is a **hard prerequisite**. The chart always creates a PersistentVolumeClaim for the backend data directory.

---

## Quick Install

### Step 1 — Create the Secret

The chart reads all sensitive values from a Kubernetes Secret. The required keys depend on your chosen Git connection method:

**SSH:**
```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<sync-token> \
  --from-file=ssh-key=/path/to/id_rsa \
  -n chart-monitor
```

**HTTP token:**
```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<sync-token> \
  --from-literal=GIT_HTTP_TOKEN=<repo-token> \
  -n chart-monitor
```

**HTTP username + token:**
```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<sync-token> \
  --from-literal=GIT_HTTP_TOKEN=<password-or-pat> \
  -n chart-monitor
```

### Step 2 — Install

**On-prem Kubernetes (SSH):**
```bash
helm install chart-monitor helm/chart-monitor \
  --set image.repository=<your-registry>/chart-monitor \
  --set image.tag=3.3.0 \
  --set gitops.connection=ssh \
  --set gitops.ssh.url=git@github.com:your-org/repo.git \
  --set ingress.host=chart-monitor.example.com \
  --set existingSecret=chart-monitor \
  -n chart-monitor --create-namespace
```

**On-prem Kubernetes (HTTP token):**
```bash
helm install chart-monitor helm/chart-monitor \
  --set image.repository=<your-registry>/chart-monitor \
  --set image.tag=3.3.0 \
  --set gitops.connection=http-token \
  --set gitops.httpToken.url=https://github.com/your-org/repo.git \
  --set ingress.host=chart-monitor.example.com \
  --set existingSecret=chart-monitor \
  -n chart-monitor --create-namespace
```

**OpenShift:**
```bash
helm install chart-monitor helm/chart-monitor \
  -f helm/chart-monitor/values-openshift.yaml \
  --set image.repository=<your-registry>/chart-monitor \
  --set image.tag=3.3.0 \
  --set gitops.connection=ssh \
  --set gitops.ssh.url=git@github.com:your-org/repo.git \
  --set existingSecret=chart-monitor \
  -n chart-monitor --create-namespace
```

---

## Git Connection Methods

Set `gitops.connection` to select the authentication method. Each method has its own values section:

### `ssh` (default)

```yaml
gitops:
  connection: ssh
  ssh:
    url: "git@github.com:your-org/repo.git"
    keyMountPath: "/app/secrets"   # where the ssh-key Secret file is mounted
```

Secret must contain: `SYNC_SECRET`, `ssh-key` (PEM private key)

### `http-token`

```yaml
gitops:
  connection: http-token
  httpToken:
    url: "https://github.com/your-org/repo.git"
```

Secret must contain: `SYNC_SECRET`, `GIT_HTTP_TOKEN`

### `http-user-token`

```yaml
gitops:
  connection: http-user-token
  httpUserToken:
    url: "https://gitlab.company.internal/org/repo.git"
    username: "svc-account"   # non-sensitive, set in values not Secret
```

Secret must contain: `SYNC_SECRET`, `GIT_HTTP_TOKEN`

### Skip certificate / host-key verification

Add `skipVerify: true` under `gitops:` for on-premises servers with self-signed certificates. Applies to both SSH (host key) and HTTPS (TLS) connections:

```yaml
gitops:
  connection: http-user-token
  httpUserToken:
    url: "https://git.company.internal/org/repo.git"
    username: "svc-account"
  skipVerify: true
```

Only use on trusted internal networks.

---

## Upgrade

```bash
helm upgrade chart-monitor helm/chart-monitor -f my-values.yaml -n chart-monitor
```

## Uninstall

```bash
helm uninstall chart-monitor -n chart-monitor
```

> **⚠️ PVC Retention**: The PersistentVolumeClaim is **not deleted** by `helm uninstall`. To remove it:
> ```bash
> kubectl delete pvc -l app.kubernetes.io/instance=chart-monitor -n chart-monitor
> ```

---

## Migrating from chart 0.1.x to 0.2.0

The `gitops:` block has been restructured. Update your values:

```yaml
# Before (0.1.x):
gitops:
  sshUrl: "git@..."
  sshKeyMountPath: "/app/secrets"

# After (0.2.0):
gitops:
  connection: ssh
  ssh:
    url: "git@..."
    keyMountPath: "/app/secrets"
```

---

## Resource Limits

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|------------|----------------|-----------|--------------|
| Backend + Frontend | 100m | 128Mi | 500m | 512Mi |

## Image Pull Secrets

If your registry requires authentication:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<user> \
  --docker-password=<password> \
  -n chart-monitor

# Then set in values:
# imagePullSecrets:
#   - name: regcred
```

## StorageClass

By default, `persistence.storageClass` is empty (cluster default). Override:

```yaml
persistence:
  storageClass: my-storage-class
```

## OpenShift Notes

- When `openshift.enabled=true`, an OpenShift Route (Edge TLS) is created instead of an Ingress.
- HTTP traffic is automatically redirected to HTTPS.
- Set `podSecurityContext.runAsUser: null` if UID 1000 is outside the namespace's allowed range (already default in `values-openshift.yaml`).

## Configuration Reference

See [`values.yaml`](values.yaml) for the full list of configurable parameters with inline documentation.
