# Contract: Environment Variables

**Feature**: 011-git-skip-verify  
**Interface type**: Runtime configuration (environment variables)

---

## GIT_SKIP_VERIFY

| Property | Value |
|----------|-------|
| **Name** | `GIT_SKIP_VERIFY` |
| **Type** | Boolean string |
| **Default** | `false` (unset = verify enabled) |
| **Required** | No |
| **Scope** | Applies to all Git operations in both GitOps sync and Helm chart deployment flows |

**Accepted truthy values** (case-insensitive): `true`, `1`, `yes`  
**All other values** (including empty/unset): treated as `false`

**Effect when `true`**:
- SSH `StrictHostKeyChecking` set to `no` — host key verification bypassed entirely.
- `UserKnownHostsFile` set to `/dev/null` — no known_hosts file consulted.
- Intended for on-premises environments with self-signed or internally signed SSH host keys.

**Effect when `false` (default)**:
- SSH `StrictHostKeyChecking` set to `accept-new` — new hosts accepted, but mismatched keys are not silently bypassed.
- `UserKnownHostsFile` set to `/dev/null` — stateless container behavior; no persistent key store.

**Always applied** (regardless of skip-verify):
- `BatchMode=yes` — prevents interactive SSH prompts.
- `ConnectTimeout=30` — 30-second TCP connection timeout for SSH.

---

## Helm values contract

**Path**: `gitops.skipVerify` in `values.yaml`  
**Type**: boolean  
**Default**: `false`  
**Maps to**: `GIT_SKIP_VERIFY` environment variable in the ConfigMap

```yaml
gitops:
  skipVerify: true   # set to true for on-prem environments
```
