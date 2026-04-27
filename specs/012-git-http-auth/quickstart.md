# Quickstart: Testing Git HTTP Authentication

**Feature**: 012-git-http-auth

---

## Local development — http-token

```bash
export GIT_CONNECTION_METHOD=http-token
export GIT_REPO_URL=https://github.com/your-org/your-repo.git
export GIT_HTTP_TOKEN=ghp_yourPersonalAccessToken
export GIT_TARGET_PATH=/tmp/store
export SYNC_SECRET=dev-secret

cd backend && uvicorn src.main:app --reload
```

Trigger sync:
```bash
curl -X POST http://localhost:8000/api/v1/git/sync \
  -H "Authorization: Bearer dev-secret"
```

---

## Local development — http-user-token

```bash
export GIT_CONNECTION_METHOD=http-user-token
export GIT_REPO_URL=https://gitlab.company.internal/org/repo.git
export GIT_HTTP_TOKEN=glpat-yourGitLabToken
export GIT_HTTP_USERNAME=your.username
export GIT_TARGET_PATH=/tmp/store
export SYNC_SECRET=dev-secret
export GIT_SKIP_VERIFY=true   # for self-signed TLS cert on on-prem server

cd backend && uvicorn src.main:app --reload
```

---

## Helm deployment — http-token

```yaml
gitops:
  connection: http-token
  httpToken:
    url: "https://github.com/your-org/your-repo.git"
  skipVerify: false
```

Secret:
```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<sync-token> \
  --from-literal=GIT_HTTP_TOKEN=<repo-token> \
  -n chart-monitor
```

---

## Helm deployment — http-user-token (on-prem with self-signed cert)

```yaml
gitops:
  connection: http-user-token
  httpUserToken:
    url: "https://git.company.internal/org/repo.git"
    username: "svc-account"
  skipVerify: true
```

Secret:
```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<sync-token> \
  --from-literal=GIT_HTTP_TOKEN=<password-or-pat> \
  -n chart-monitor
```

---

## Verifying `.netrc` is cleaned up

The `.netrc` file is written to a temp directory and deleted after each sync. To confirm no credentials persist:

```bash
kubectl exec -n chart-monitor deploy/chart-monitor -- find /tmp -name ".netrc" 2>/dev/null
# Should return nothing after a sync completes
```

---

## Confirming TLS skip works for HTTP

```bash
kubectl exec -n chart-monitor deploy/chart-monitor -- \
  git -c http.sslVerify=false ls-remote https://your-git-server/repo.git
```

---

## Backward compat — existing SSH deployments

Existing values using `gitops.sshUrl` must be migrated:

```yaml
# Old (0.1.x):
gitops:
  sshUrl: "git@github.com:org/repo.git"

# New (0.2.0+):
gitops:
  connection: ssh
  ssh:
    url: "git@github.com:org/repo.git"
```
