# Runtime Test: US1 — Upgrade on Docker Desktop k8s

**Status**: PENDING — run after us1-install.md passes  
**Prerequisite**: chart-monitor release installed in `chart-monitor` namespace

## Commands to Run

```bash
helm upgrade chart-monitor helm/chart-monitor \
  --set backend.replicaCount=2 \
  -n chart-monitor

kubectl rollout status deployment/chart-monitor-backend -n chart-monitor --timeout=3m
```

## Assertions

- [ ] `kubectl get pods -n chart-monitor -l app.kubernetes.io/component=backend` shows 2 Running pods
- [ ] Upgrade completes without pod restarts on frontend (no downtime)
- [ ] `helm history chart-monitor -n chart-monitor` shows revision 2

## Results

| Assertion | Pass/Fail | Notes |
|-----------|-----------|-------|
| 2 backend pods Running | — | |
| Frontend not restarted | — | |
| History shows revision 2 | — | |
