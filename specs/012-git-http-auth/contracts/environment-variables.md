# Contract: Environment Variables

**Feature**: 012-git-http-auth

---

## GIT_CONNECTION_METHOD

| Property | Value |
|----------|-------|
| **Name** | `GIT_CONNECTION_METHOD` |
| **Type** | String enum |
| **Default** | `ssh` |
| **Required** | No |
| **Source** | ConfigMap (`gitops.connection`) |

**Accepted values**: `ssh`, `http-token`, `http-user-token`  
**Invalid values**: startup error listing valid options.

---

## GIT_REPO_URL

| Property | Value |
|----------|-------|
| **Name** | `GIT_REPO_URL` |
| **Type** | String (HTTPS URL) |
| **Default** | `""` |
| **Required** | When `GIT_CONNECTION_METHOD` is `http-token` or `http-user-token` |
| **Source** | ConfigMap (`gitops.httpToken.url` or `gitops.httpUserToken.url`) |

**Format**: `https://host/org/repo.git`

---

## GIT_HTTP_TOKEN

| Property | Value |
|----------|-------|
| **Name** | `GIT_HTTP_TOKEN` |
| **Type** | String (secret) |
| **Default** | (none) |
| **Required** | When `GIT_CONNECTION_METHOD` is `http-token` or `http-user-token` |
| **Source** | Kubernetes Secret key `GIT_HTTP_TOKEN` |

---

## GIT_HTTP_USERNAME

| Property | Value |
|----------|-------|
| **Name** | `GIT_HTTP_USERNAME` |
| **Type** | String |
| **Default** | `""` |
| **Required** | When `GIT_CONNECTION_METHOD` is `http-user-token` |
| **Source** | ConfigMap (`gitops.httpUserToken.username`) |

---

## GIT_SSH_URL (unchanged)

| Property | Value |
|----------|-------|
| **Name** | `GIT_SSH_URL` |
| **Type** | String (SSH URL) |
| **Required** | When `GIT_CONNECTION_METHOD` is `ssh` |
| **Source** | ConfigMap (`gitops.ssh.url`) |

---

## Helm values contract

```yaml
gitops:
  connection: ssh           # Required — selects auth method

  ssh:
    url: ""                 # Required when connection: ssh
    keyMountPath: "/app/secrets"

  httpToken:
    url: ""                 # Required when connection: http-token

  httpUserToken:
    url: ""                 # Required when connection: http-user-token
    username: ""            # Required when connection: http-user-token

  skipVerify: false         # Optional — disables TLS/SSH verification
```

## Secret contract (operator-managed)

```bash
# For SSH (existing):
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<token> \
  --from-file=ssh-key=/path/to/id_rsa

# For http-token:
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<token> \
  --from-literal=GIT_HTTP_TOKEN=<repo-access-token>

# For http-user-token:
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<token> \
  --from-literal=GIT_HTTP_TOKEN=<password-or-token>
```
