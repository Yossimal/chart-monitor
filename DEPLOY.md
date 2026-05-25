# chart-monitor — On-Prem Deployment Guide

## What's in this package

```
chart-monitor-deploy/
├── Dockerfile                   # Build the application image
├── DEPLOY.md                    # This file
├── backend/                     # Python/FastAPI source
├── frontend/src/                # Vanilla JS frontend
├── docs/                        # MkDocs source (built inside Docker)
└── helm/chart-monitor/          # Helm 3 chart
```

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Docker | For building the image |
| Helm 3 | `helm version` |
| Kubernetes 1.24+ | With a storage provisioner (default StorageClass) |
| Ingress controller | e.g. nginx-ingress |
| Image registry | Accessible from the cluster |

---

## Step 1 — Build and push the image

```bash
# Build
docker build -t <your-registry>/chart-monitor:3.3.0 .

# Push
docker push <your-registry>/chart-monitor:3.3.0
```

---

## Step 2 — Create the namespace

```bash
kubectl create namespace chart-monitor
```

---

## Step 3 — Create the Secret

The chart references an existing Secret named `chart-monitor` (configurable via `existingSecret`).
The required keys depend on your chosen connection method:

| Connection method | Required Secret keys |
|-------------------|---------------------|
| `ssh` | `SYNC_SECRET`, `ssh-key` (PEM private key) |
| `http-token` | `SYNC_SECRET`, `GIT_HTTP_TOKEN` |
| `http-user-token` | `SYNC_SECRET`, `GIT_HTTP_TOKEN` |

### SSH

```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<your-sync-token> \
  --from-file=ssh-key=/path/to/id_rsa \
  -n chart-monitor
```

### HTTP token

```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<your-sync-token> \
  --from-literal=GIT_HTTP_TOKEN=<repository-access-token> \
  -n chart-monitor
```

### HTTP username + token

```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<your-sync-token> \
  --from-literal=GIT_HTTP_TOKEN=<password-or-pat> \
  -n chart-monitor
```

Add extra collector tokens as needed to any of the above:
```bash
  --from-literal=GITHUB_TOKEN=<github-pat>
```

---

## Step 4 — Configure values

Copy and edit the values file:

```bash
cp helm/chart-monitor/values.yaml my-values.yaml
```

### SSH (default)

```yaml
image:
  repository: <your-registry>/chart-monitor
  tag: "3.3.0"

gitops:
  connection: ssh
  ssh:
    url: "git@github.com:your-org/your-dashboards-repo.git"

ingress:
  host: "chart-monitor.your-domain.com"

persistence:
  storageClass: ""   # leave empty for cluster default, or set explicitly
```

### HTTP token

```yaml
gitops:
  connection: http-token
  httpToken:
    url: "https://github.com/your-org/your-dashboards-repo.git"
```

### HTTP username + token

```yaml
gitops:
  connection: http-user-token
  httpUserToken:
    url: "https://gitlab.company.internal/org/repo.git"
    username: "svc-account"
```

### On-premises Git servers (self-signed / internal CA certificate)

Add `skipVerify: true` to bypass certificate verification. Works for both SSH (host key) and HTTP (TLS) connections:

```yaml
gitops:
  connection: http-user-token
  httpUserToken:
    url: "https://git.company.internal/org/repo.git"
    username: "svc-account"
  skipVerify: true
```

Only enable on trusted internal networks.

---

## Step 5 — Deploy

```bash
helm install chart-monitor helm/chart-monitor \
  -f my-values.yaml \
  -n chart-monitor
```

### Verify

```bash
kubectl get pods,svc,pvc,ingress -n chart-monitor
kubectl logs -n chart-monitor -l app.kubernetes.io/instance=chart-monitor -f
```

---

## Upgrade

```bash
helm upgrade chart-monitor helm/chart-monitor -f my-values.yaml -n chart-monitor
```

## Uninstall

```bash
helm uninstall chart-monitor -n chart-monitor
# PVC is retained — delete manually if needed:
kubectl delete pvc -l app.kubernetes.io/instance=chart-monitor -n chart-monitor
```

---

## Migrating from chart 0.1.x to 0.2.0

The `gitops:` values block has been restructured. Update your values file:

| Old (0.1.x) | New (0.2.0) |
|-------------|-------------|
| `gitops.sshUrl` | `gitops.ssh.url` |
| `gitops.sshKeyMountPath` | `gitops.ssh.keyMountPath` |

Add the new required field:

```yaml
gitops:
  connection: ssh        # add this line
  ssh:
    url: "git@..."       # was gitops.sshUrl
```

---

## OpenShift

Use the provided overlay instead of `values.yaml`:

```bash
helm install chart-monitor helm/chart-monitor \
  -f helm/chart-monitor/values-openshift.yaml \
  -f my-values.yaml \
  -n chart-monitor
```

The OpenShift overlay enables an Edge TLS Route and clears the UID/GID constraints so OpenShift assigns them from the namespace range.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Pod `Pending` | PVC unbound | Check storage provisioner; set `persistence.storageClass` |
| `FailedMount` for `ssh-key` | Secret missing or not using SSH method | Run Step 3 for SSH; for HTTP methods `ssh-key` is not needed |
| `ssh: not found` | Wrong image | Rebuild with provided Dockerfile |
| `dubious ownership` git error | PVC UID mismatch | Already fixed in Dockerfile (`safe.directory=*`) |
| `Collector is not defined` in logs | Dashboard script missing imports | Add `from chart_monitor import Collector` to your dashboard file |
| `Host key verification failed` (SSH) | Self-signed SSH host key not trusted | Set `gitops.skipVerify: true` (on trusted networks only) |
| HTTP 401 / auth failed | Wrong token or username | Check `GIT_HTTP_TOKEN` in Secret; for `http-user-token` check `gitops.httpUserToken.username` |
| TLS certificate error (HTTP) | Self-signed HTTPS cert on git server | Set `gitops.skipVerify: true` (on trusted networks only) |
