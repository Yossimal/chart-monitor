# Feature Specification: Git Skip TLS Verification for Deployment

**Feature Branch**: `011-git-skip-verify`  
**Created**: 2026-04-26  
**Status**: Draft  
**Input**: User description: "the user will be able to deploy the project with skip-verify on the git (needed for the on prem env)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enable Skip-Verify During Deployment (Priority: P1)

An operator deploying the project in an on-premises environment where the Git server uses a self-signed or internal CA certificate can configure the deployment to skip Git TLS/SSL certificate verification, allowing the deployment to succeed without requiring changes to the system's certificate store.

**Why this priority**: This is the core requirement. Without this, the deployment process fails entirely in environments with non-public certificates, blocking all other work.

**Independent Test**: Can be fully tested by running a deployment with the skip-verify option enabled against a Git server with a self-signed certificate, and verifying the deployment completes successfully.

**Acceptance Scenarios**:

1. **Given** a deployment configuration without skip-verify set, **When** the user deploys against a Git server with a trusted public certificate, **Then** the deployment succeeds normally with no change in behavior.
2. **Given** a deployment configuration with skip-verify enabled, **When** the user deploys against a Git server with a self-signed certificate, **Then** the deployment completes successfully without certificate errors.
3. **Given** a deployment configuration with skip-verify disabled (explicit), **When** the user deploys against a Git server with a self-signed certificate, **Then** the deployment fails with a clear error indicating a certificate verification failure.

---

### User Story 2 - Configure Skip-Verify via Deployment Parameters (Priority: P2)

An operator can set the skip-verify option through the standard deployment configuration mechanism (e.g., a configuration file, environment variable, or deployment flag) without modifying source code or internal system files.

**Why this priority**: The option must be accessible and reversible through normal operational means, not require code changes.

**Independent Test**: Can be tested by setting the skip-verify option via the deployment interface and confirming the setting is respected on the next deployment run.

**Acceptance Scenarios**:

1. **Given** the deployment tool exposes a skip-verify option, **When** the operator sets it to true, **Then** subsequent deployments skip Git certificate verification.
2. **Given** the skip-verify option is set, **When** the operator sets it back to false, **Then** subsequent deployments enforce Git certificate verification again.

---

### Edge Cases

- What happens when skip-verify is enabled but the Git server is unreachable for reasons unrelated to TLS (e.g., network timeout)? The deployment should still fail with an appropriate network error.
- What happens if the skip-verify flag is set in a public/cloud environment by mistake? The deployment proceeds but the operator accepts the reduced security posture; no system-level guard is needed.
- What if the configuration file has skip-verify set to an invalid value (e.g., a non-boolean string)? The system should reject the configuration with a clear validation error before attempting deployment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both the GitOps sync flow and the Helm chart deployment flow MUST expose a skip-verify option for their respective Git operations.
- **FR-002**: When skip-verify is enabled, the system MUST bypass Git TLS/SSL certificate verification for all Git operations performed during deployment.
- **FR-003**: When skip-verify is disabled or not set, the system MUST enforce standard Git TLS/SSL certificate verification (default behavior unchanged).
- **FR-004**: The skip-verify option MUST default to `false` (verification enabled) to preserve secure-by-default behavior.
- **FR-005**: The deployment process MUST surface a clear, human-readable error when Git certificate verification fails and skip-verify is not enabled.
- **FR-006**: The skip-verify setting MUST be configurable via an environment variable, without modifying application source code. Both the GitOps sync flow and the Helm chart deployment flow MUST read this environment variable at runtime.

### Key Entities

- **Deployment Configuration**: The set of parameters controlling a deployment run, including the new skip-verify flag and its value.
- **Git Operation**: Any interaction with a remote Git repository during deployment (clone, fetch, pull), subject to the skip-verify setting.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can complete a full deployment against a Git server with a self-signed certificate in the same time as a standard deployment (no significant overhead introduced by the skip-verify path).
- **SC-002**: 100% of deployments with skip-verify disabled continue to behave identically to pre-feature deployments (no regression).
- **SC-003**: The skip-verify option can be toggled and takes effect within a single deployment cycle — no restart or reinstallation required.
- **SC-004**: When certificate verification fails and skip-verify is off, operators receive an actionable error message that identifies the root cause within the deployment output.

## Clarifications

### Session 2026-04-26

- Q: Which deployment path(s) should skip-verify apply to? → A: Both GitOps sync (002-gitops-sync) and Helm chart deployment (010-helm-chart-deploy).
- Q: What is the primary configuration surface for the skip-verify option? → A: Environment variable, read by both the GitOps sync flow and the Helm chart deployment flow.
- Q: Should deployment output display a visible warning when skip-verify is active? → A: No — no warning required; the operator is responsible for knowing the environment variable is set.

## Assumptions

- Both the GitOps sync flow (002-gitops-sync) and the Helm chart deployment flow (010-helm-chart-deploy) already perform Git operations as part of their flows; this feature adds a configuration knob to each.
- "On-premises environment" refers to internal networks where Git servers may use self-signed or private CA certificates not trusted by the OS certificate store.
- The skip-verify option applies to Git operations only, not to other HTTPS calls (e.g., registry pulls, API calls) made during deployment.
- No audit logging or visible warning is required when skip-verify is active; the operator is responsible for knowing the environment variable state.
