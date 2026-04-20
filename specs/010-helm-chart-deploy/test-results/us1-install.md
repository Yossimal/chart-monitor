# Runtime Test: US1 — Install on Docker Desktop k8s

**Status**: PENDING — requires Docker Desktop with Kubernetes enabled

## Commands to Run

```bash
# Ensure local-path-provisioner is installed for PVC support
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Install the chart
helm install chart-monitor helm/chart-monitor \
  -n chart-monitor \
  --create-namespace \
  --set backend.image.repository=<your-backend-image> \
  --set frontend.image.repository=<your-frontend-image>

# Wait for pods
kubectl rollout status deployment/chart-monitor-backend -n chart-monitor --timeout=3m
kubectl rollout status deployment/chart-monitor-frontend -n chart-monitor --timeout=3m
```

## Assertions

- [ ] `kubectl get pods -n chart-monitor` shows backend pod in `Running` state
- [ ] `kubectl get pods -n chart-monitor` shows frontend pod in `Running` state
- [ ] `kubectl get pvc -n chart-monitor` shows PVC in `Bound` state
- [ ] `kubectl get ingress -n chart-monitor` shows Ingress created
- [ ] `kubectl get sa,role,rolebinding -n chart-monitor` shows ServiceAccount, Role, RoleBinding

## Results

| Assertion | Pass/Fail | Notes |
|-----------|-----------|-------|
| Backend pod Running | — | |
| Frontend pod Running | — | |
| PVC Bound | — | |
| Ingress created | — | |
| RBAC resources present | — | |
