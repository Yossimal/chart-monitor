# Runtime Test: US1 — Uninstall on Docker Desktop k8s

**Status**: PENDING — run after us1-upgrade.md passes  
**Prerequisite**: chart-monitor release running in `chart-monitor` namespace

## Commands to Run

```bash
helm uninstall chart-monitor -n chart-monitor

# Wait briefly for resources to terminate
sleep 10
```

## Assertions

- [ ] `kubectl get deploy -n chart-monitor` returns no chart-monitor resources
- [ ] `kubectl get svc -n chart-monitor` returns no chart-monitor resources
- [ ] `kubectl get ingress -n chart-monitor` returns no chart-monitor resources
- [ ] `kubectl get sa,role,rolebinding -n chart-monitor` returns no chart-monitor resources
- [ ] `kubectl get pvc -n chart-monitor` still shows the PVC (retained by design)

## Results

| Assertion | Pass/Fail | Notes |
|-----------|-----------|-------|
| Deployments removed | — | |
| Services removed | — | |
| Ingress removed | — | |
| RBAC resources removed | — | |
| PVC retained (expected) | — | |
