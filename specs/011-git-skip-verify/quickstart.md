# Quickstart: Testing Git Skip-Verify

**Feature**: 011-git-skip-verify

---

## Local development (docker-compose / bare process)

Set `GIT_SKIP_VERIFY=true` in your environment before starting the backend:

```bash
export GIT_SSH_URL=git@your-onprem-git.internal:org/repo.git
export GIT_SSH_KEY_PATH=/path/to/id_rsa
export GIT_TARGET_PATH=/tmp/store
export SYNC_SECRET=dev-secret
export GIT_SKIP_VERIFY=true

cd backend
uvicorn src.main:app --reload
```

Trigger a sync and confirm it succeeds against a server with a self-signed host key:

```bash
curl -X POST http://localhost:8000/api/v1/git/sync \
  -H "Authorization: Bearer dev-secret"
```

---

## Helm deployment (on-prem)

Add to your `values.yaml` override:

```yaml
gitops:
  sshUrl: "git@your-onprem-git.internal:org/repo.git"
  skipVerify: true
```

Then install/upgrade:

```bash
helm upgrade --install chart-monitor ./helm/chart-monitor \
  -f my-values.yaml \
  -n chart-monitor
```

The `GIT_SKIP_VERIFY=true` environment variable will be injected into the pod via the ConfigMap.

---

## Verifying the SSH command

After startup, the effective `GIT_SSH_COMMAND` will appear in the pod logs on the first sync:

```
Running git command: git clone git@... (cwd=/data/store)
```

The SSH flags used are logged at DEBUG level. To confirm which mode is active, check the value of `GIT_SKIP_VERIFY` in the ConfigMap:

```bash
kubectl get configmap chart-monitor -n chart-monitor -o yaml | grep GIT_SKIP_VERIFY
```

---

## Running tests

```bash
cd backend
pytest tests/ -k "git" -v
```
