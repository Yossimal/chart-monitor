# Feature Specification: Git HTTP Authentication Methods

**Feature Branch**: `012-git-http-auth`  
**Created**: 2026-04-27  
**Status**: Draft  
**Input**: User description: "the user will be able to set the connection to the git via http with http repository token, also he will be able to set the connection to the git with user and token. He will set those credentials in the helm and will set in the values the connection method. Each connection method will have its own values."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Connect to Git via Repository Token (Priority: P1)

An operator running the application in an environment where the Git server supports token-based HTTP authentication (e.g., GitLab deploy tokens, GitHub fine-grained tokens, Gitea tokens) can configure the deployment to connect to the Git repository over HTTPS using a single repository access token, without requiring an SSH key.

**Why this priority**: Token-based HTTP auth is the most common authentication method for on-premises Git servers and is simpler to set up than SSH keys. It is the primary alternative to SSH.

**Independent Test**: Configure the deployment with `gitops.connection: http-token` and a valid repository token; trigger a sync and confirm it clones/pulls successfully from an HTTPS Git URL.

**Acceptance Scenarios**:

1. **Given** `gitops.connection` is set to `http-token` and a valid token is provided, **When** a sync is triggered, **Then** the system connects to the Git repository over HTTPS using the token and sync completes successfully.
2. **Given** `gitops.connection` is set to `http-token` but the token is invalid or expired, **When** a sync is triggered, **Then** the sync fails with a clear authentication error message.
3. **Given** `gitops.connection` is set to `http-token` and no token is provided, **When** the application starts, **Then** the system reports a configuration error indicating the token is missing.

---

### User Story 2 — Connect to Git via Username and Password/Token (Priority: P2)

An operator can configure the deployment to connect to the Git repository over HTTPS using a username and password or personal access token combination, as required by Git servers that use Basic HTTP authentication (e.g., Bitbucket Server, some self-hosted GitLab/Gitea instances).

**Why this priority**: Username + token/password covers Git servers that require a username to disambiguate the credential scope, which is a common on-premises pattern.

**Independent Test**: Configure the deployment with `gitops.connection: http-user-token` and valid username + token; trigger a sync and confirm it pulls successfully.

**Acceptance Scenarios**:

1. **Given** `gitops.connection` is set to `http-user-token` with a valid username and token, **When** a sync is triggered, **Then** the system connects over HTTPS using the credentials and sync completes successfully.
2. **Given** `gitops.connection` is set to `http-user-token` but either the username or token is missing, **When** the application starts, **Then** the system reports a configuration error identifying which credential is absent.
3. **Given** `gitops.connection` is set to `http-user-token` with an invalid username or token, **When** a sync is triggered, **Then** the sync fails with a clear authentication error.

---

### User Story 3 — Select Connection Method via Helm Values (Priority: P3)

An operator can declare the connection method (`ssh`, `http-token`, or `http-user-token`) in the Helm `values.yaml` file, and each method exposes only the configuration fields relevant to that method. Fields for other methods are not required and do not appear in the active configuration.

**Why this priority**: The clean values separation ensures operators are not confused by irrelevant fields and that credentials for unused methods are never provisioned unnecessarily.

**Independent Test**: Render the Helm chart with each of the three `gitops.connection` values and confirm only the relevant configuration section is applied to the deployment.

**Acceptance Scenarios**:

1. **Given** `gitops.connection: ssh`, **When** the chart is rendered, **Then** only SSH-related configuration (SSH URL, key path) is applied; HTTP credential fields are absent.
2. **Given** `gitops.connection: http-token`, **When** the chart is rendered, **Then** only the HTTPS URL and token fields are applied; SSH and username fields are absent.
3. **Given** `gitops.connection: http-user-token`, **When** the chart is rendered, **Then** only the HTTPS URL, username, and token fields are applied; SSH fields are absent.
4. **Given** an invalid or missing `gitops.connection` value, **When** the chart is rendered, **Then** Helm returns a validation error identifying the invalid value.

---

### Edge Cases

- What if the HTTPS URL uses a self-signed certificate? The existing `gitops.skipVerify` flag should apply to HTTP connections as well as SSH, disabling TLS certificate verification for HTTPS git operations.
- What if the operator sets `gitops.connection: http-token` but also provides SSH fields? The SSH fields are ignored; only the selected method's fields are used.
- What if the token contains special characters (e.g., `@`, `/`, `#`)? The system must handle these safely without breaking the Git URL or credential injection.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The deployment configuration MUST expose a `connection` selector with at least three valid values: `ssh`, `http-token`, and `http-user-token`.
- **FR-002**: When `connection` is `http-token`, the system MUST authenticate Git operations using an HTTPS URL and a single repository access token stored as a Kubernetes Secret.
- **FR-003**: When `connection` is `http-user-token`, the system MUST authenticate Git operations using an HTTPS URL, a username, and a token/password, both stored as a Kubernetes Secret.
- **FR-004**: When `connection` is `ssh`, existing SSH-based behaviour MUST remain unchanged (backward compatible).
- **FR-005**: Missing required credentials for the selected connection method MUST cause the system to report a descriptive configuration error at startup, before any sync is attempted.
- **FR-006**: All credentials (tokens, passwords) MUST be stored in Kubernetes Secrets, not in the Helm ConfigMap.
- **FR-007**: The existing `gitops.skipVerify` flag MUST apply to HTTPS git operations (TLS certificate verification) when the connection method is `http-token` or `http-user-token`, in addition to its existing SSH behaviour.
- **FR-008**: Each connection method MUST have its own clearly named nested section in the deployment configuration (e.g., `gitops.ssh`, `gitops.httpToken`, `gitops.httpUserToken`) so operators only fill in fields for their chosen method. The existing flat `gitops.sshUrl` / `gitops.sshKeyMountPath` keys are replaced by the nested structure (`gitops.ssh.url`, `gitops.ssh.keyMountPath`).

### Key Entities

- **Connection Method**: The selected authentication strategy (`ssh`, `http-token`, `http-user-token`) that governs which credentials are used and how Git operations are performed.
- **Git Credential**: The set of secrets required for the selected connection method (SSH key, repository token, or username + token). Stored in Kubernetes Secrets.
- **Git Repository URL**: The remote URL used for Git operations. SSH method reads from `GIT_SSH_URL`; HTTP methods read from `GIT_REPO_URL`. Format is `git@host:org/repo.git` for SSH and `https://host/org/repo.git` for HTTP methods.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can switch from SSH to HTTP token authentication by changing two Helm values (`gitops.connection` and providing a token secret) — no source code changes required.
- **SC-002**: 100% of existing SSH-based deployments continue to function without any values changes after the feature is released (full backward compatibility).
- **SC-003**: When a required credential is missing for the selected connection method, the operator receives a descriptive error within the first sync attempt — not a generic failure.
- **SC-004**: All three connection methods successfully complete a sync against a compatible Git server within the same time bounds as the existing SSH implementation.

## Clarifications

### Session 2026-04-27

- Q: How should HTTP credentials be passed to git operations? → A: Write a temporary `.netrc` file at sync time; credentials are never embedded in the URL or exposed in process arguments.
- Q: Should Helm values use nested per-method sections or flat with prefixes? → A: Nested sections — `gitops.ssh.url`, `gitops.httpToken.url`, `gitops.httpUserToken.url`, etc. Existing `gitops.sshUrl` is renamed to `gitops.ssh.url` (breaking change, acceptable).
- Q: What env var name carries the repository URL for HTTP connection methods? → A: `GIT_REPO_URL` — a new generic env var used by HTTP methods. `GIT_SSH_URL` is retained as the SSH-specific env var for backward compatibility.

## Assumptions

- The Git repository URL format differs by connection method: SSH uses `git@host:org/repo.git` (read from `GIT_SSH_URL`); HTTP methods use `https://host/org/repo.git` (read from `GIT_REPO_URL`). Operators are expected to provide the correct URL format for their chosen method. `GIT_SSH_URL` is retained for SSH backward compatibility.
- Credentials for HTTP methods are passed to git via a temporary `.netrc` file written at sync time and deleted immediately after. Credentials are never embedded in the repository URL or exposed in process arguments, `ps` output, or git error messages.
- The `gitops.skipVerify` flag will extend to disable HTTPS TLS certificate verification (`git -c http.sslVerify=false`) when the connection method is HTTP-based, covering on-premises servers with self-signed certificates.
- The existing `existingSecret` Helm value mechanism is used to provide credentials; operators add token/password fields to the same Kubernetes Secret they already manage.
- No UI changes are required; this is a deployment configuration feature only.
