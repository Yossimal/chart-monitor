# Feature Specification: GitOps Support

**Feature Branch**: `002-gitops-sync`  
**Created**: 2026-03-10  
**Status**: Draft  
**Input**: User description: "the next feature is GitOps support. In that feature we will receive from the environment variables the git repo ssh url and key path. then it will monitor the git repo and for each python update it will rerender its scripts so the next fetch will use them."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Git Repository (Priority: P1)

The system administrator can configure a Git repository using environment variables (SSH URL and SSH key path) so that the system knows where to fetch the Python scripts from.

**Why this priority**: Without credentials and repository location, the GitOps feature cannot function. This is the foundational configuration step.

**Independent Test**: Can be fully tested by providing valid and invalid SSH credentials via environment variables and verifying if the system successfully connects or correctly logs an authentication failure.

**Acceptance Scenarios**:

1. **Given** the system is starting, **When** the `GIT_SSH_URL` and `GIT_SSH_KEY_PATH` environment variables are provided with valid credentials, **Then** the system successfully initializes the GitOps monitor.
2. **Given** the system is starting, **When** invalid Git credentials are provided, **Then** the system logs an initialization error and either falls back to local scripts or halts, depending on configured behavior.

---

### User Story 2 - Manual Sync / Rerender (Priority: P1)

The system provides a manual "Sync" button at the bottom of the dashboards sidebar in the UI. When the user asserts a sync, a prompt asks for the `SYNC_SECRET`. If provided correctly (with an optional "Remember me" to save to local storage), the system executes a shell Git command directly in the target directory to fetch updates. When new Python scripts are fetched, the system rerenders the scripts so they are ready for the next fetch cycle.

**Why this priority**: This is the core functionality of the feature, giving the user control over when to update operations with the latest scripts defined in the Git repository, while securing the action with a secret token.

**Independent Test**: Can be fully tested by pushing a new commit that alters a Python script to the remote repository, clicking the "Sync" button in the sidebar, entering the correct `SYNC_SECRET`, and observing the system fetching and rerendering the scripts.

**Acceptance Scenarios**:

1. **Given** the GitOps monitor is running and tracking a repository, **When** the user clicks the "Sync" button in the sidebar and enters a valid `SYNC_SECRET`, **Then** the system fetches the latest updates using shell Git commands in the target directory and rerenders the scripts.
2. **Given** the user checks "Remember me" during sync, **When** they trigger a sync in the future, **Then** they are not prompted again as the secret is loaded from local storage.
3. **Given** the user provides an invalid `SYNC_SECRET`, **When** they assert a sync, **Then** the API rejects the request as unauthorized.

---

### Edge Cases

- **Invalid Credentials**: If the SSH key path or URL is invalid, missing, or lacks permissions, the system will log a visible error to the console and display an alert containing the reason for the failure in the UI.
- **Temporary Unreachability**: If the Git repository is temporarily unreachable during a manual sync, the system will abort the sync, log the connection error to the console, and display an alert containing the failure reason in the UI.
- **Syntax Errors**: If a newly fetched Python script has a syntax error, the system will abort the sync, fall back to the previous working version, log detailed errors to the console, and display an alert containing the script parsing error reason in the UI.
- **Missing Environment Variables**: If the required environment variables are not provided, the GitOps feature is considered disabled. The core monitoring app will be completely disabled. The frontend root route (`/`) will redirect to a mandatory "How to connect your repo" tutorial page instead of the main dashboard UI.
- **Malicious Files**: If the remote repository contains any files that do not have a `.txt` or `.py` extension, the system will instantly abort the pull process to avoid malicious payloads, log the security error, and surface the alert in the UI.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept the Git repository SSH URL, SSH key path, target local directory path, and a sync secret via environment variables (e.g., `GIT_SSH_URL`, `GIT_SSH_KEY_PATH`, `GIT_TARGET_PATH`, and `SYNC_SECRET`).
- **FR-002**: System MUST provide a manual "Sync" button located at the bottom of the dashboards sidebar in the UI.
- **FR-003**: System MUST prompt the user for the `SYNC_SECRET` when clicking the Sync button, offering a "Remember me" checkbox to persist the token in browser local storage.
- **FR-004**: System MUST authenticate the `/api/git/sync` endpoint using the provided secret as a Bearer token.
- **FR-005**: System MUST execute Git commands directly using the system shell within `GIT_TARGET_PATH` when fetching updates.
- **FR-006**: System MUST inspect the repository contents and abort the pull process if any file lacks a `.py` or `.txt` extension.
- **FR-007**: System MUST rerender the updated Python scripts upon successfully fetching them.
- **FR-008**: System MUST use the latest rerendered scripts for all subsequent fetching/processing operations.
- **FR-009**: System MUST gracefully handle authentication, validation, and repository connection errors and display an alert in the UI detailing the reason for the failure.
- **FR-010**: System MUST handle script parsing/rendering errors gracefully by falling back to the previous working version of the script, logging the specific errors to the console, and displaying an alert in the UI detailing the specific script error.
- **FR-011**: System MUST provide a built-in UI page directly on the root route (`/`) if GitOps environment variables are missing. This page MUST disable access to the rest of the application and display instructions on how to configure SSH keys. This page MUST include premade guides for Bitbucket, GitHub, and GitLab.

### Key Entities *(include if feature involves data)*

- **GitOpsConfiguration**: Contains the repository SSH URL and key path.
- **ScriptVersionTracker**: Tracks the currently loaded commit hash to identity when a new fetch and rerender is necessary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully authenticates and connects to a remote Git repository using provided SSH credentials.
- **SC-002**: When a user clicks "Sync", updates to Python scripts in the remote repository are fetched and rerendered successfully.
- **SC-003**: Successive data fetch cycles use the updated scripts immediately after a manual rerendering is complete.
- **SC-004**: System handles invalid manual sync attempts (e.g., offline repository, syntax errors) without impacting core monitoring uptime.
- **SC-005**: The UI provides clear, actionable instructions for configuring Git credentials across the 3 major Git providers (GitHub, GitLab, Bitbucket).
