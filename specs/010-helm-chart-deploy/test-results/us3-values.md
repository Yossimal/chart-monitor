# Runtime Test: US3 — Value Overrides on Docker Desktop k8s

**Status**: PENDING — requires Docker Desktop with Kubernetes enabled  
**Prerequisite**: Docker Desktop k8s running, local-path-provisioner installed

## Commands to Run

```bash
helm install chart-monitor helm/chart-monitor \
  -n chart-monitor --create-namespace \
  --set backend.image.repository=<your-backend-image> \
  --set backend.image.tag=0.9.0 \
  --set frontend.image.repository=<your-frontend-image> \
  --set backend.replicaCount=2 \
  --set backend.resources.limits.memory=256Mi \
  --set persistence.size=2Gi \
  --set "backend.env[0].name=MY_VAR" \
  --set "backend.env[0].value=hello"

kubectl rollout status deployment/chart-monitor-backend -n chart-monitor --timeout=3m
```

## Assertions

- [ ] `kubectl get deploy chart-monitor-backend -n chart-monitor -o jsonpath='{.spec.replicas}'` returns `2`
- [ ] `kubectl get pods -n chart-monitor -l app.kubernetes.io/component=backend -o jsonpath='{.items[0].spec.containers[0].image}'` contains `0.9.0`
- [ ] `kubectl get pods -n chart-monitor -l app.kubernetes.io/component=backend -o jsonpath='{.items[0].spec.containers[0].resources.limits.memory}'` returns `256Mi`
- [ ] `kubectl get pvc -n chart-monitor -o jsonpath='{.items[0].spec.resources.requests.storage}'` returns `2Gi`
- [ ] `kubectl exec -n chart-monitor deploy/chart-monitor-backend -- env | grep MY_VAR` returns `MY_VAR=hello`

## Results

| Override | Assertion | Pass/Fail | Notes |
|----------|-----------|-----------|-------|
| `backend.image.tag=0.9.0` | Image tag in pod spec | — | |
| `backend.replicaCount=2` | 2 pods running | — | |
| `backend.resources.limits.memory=256Mi` | Memory limit on container | — | |
| `persistence.size=2Gi` | PVC storage request | — | |
| `backend.env MY_VAR=hello` | Env var in container | — | |
