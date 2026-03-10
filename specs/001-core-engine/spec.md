# Feature Specification: Core Chart-Monitor Application

**Feature Branch**: `001-core-engine`  
**Created**: 2026-03-09  
**Status**: Draft  
**Input**: User description: "Build the core Chart-Monitor application. The core mechanic of Chart-Monitor works by defining two conceptual entities: 1. Source... 2. Dashboard..."

## Clarifications

### Session 2026-03-10
- Q: Specification Models → A: Added `Collector` base class with `@secret` annotation and `TableDashboard` base class with `@dashboardColumn` annotation. SQLite in-memory support planned for the future.

### Session 2026-03-09
- Q: Secrets & Credentials Management → A: Backend resolves secrets via Host Environment variables. (HashiCorp Vault parsing is a future planned feature).
- Q: Configuration Reload Mechanism → A: Local Auto-Polling (periodic directory checks).
- Q: Frontend Polling Frequency → A: Overridable scrape interval defined in the Source script configuration.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Backend Data Execution (Priority: P1)

As an operator, I want the system to load my Source configurations and execute them securely in a sandbox so that I can extract raw data from external systems.

**Why this priority**: Without the ability to securely fetch raw data, the monitoring dashboards cannot function.

**Independent Test**: Can be fully tested by defining a Source configuration that returns static data and verifying the backend successfully executes it inside the secure execution sandbox.

**Acceptance Scenarios**:

1. **Given** a valid Source configuration defining an extraction script, **When** the backend loads it, **Then** it must securely execute the script and return the raw output.
2. **Given** a Source configuration with unauthorized system access (e.g., trying to read local files outside sandbox), **When** executed, **Then** the execution must fail due to security restrictions.

---

### User Story 2 - Dashboard Data Processing (Priority: P1)

As an operator, I want the system to load Dashboard configurations to process Source data using extraction rules (dot-notation, regex) and apply styling rules so that the data is ready for UI consumption.

**Why this priority**: Extracted data needs to be styled and filtered for users to monitor effectively.

**Independent Test**: Can be tested by passing mock Source data through a Dashboard configuration and verifying the output applies the correct extraction and styling mapping.

**Acceptance Scenarios**:

1. **Given** a Dashboard configuration and raw Source data, **When** processed, **Then** the system extracts specific fields using the defined methods.
2. **Given** styling rules based on specific data values, **When** processed, **Then** the result objects include the corresponding CSS styling indicators.

---

### User Story 3 - Frontend Display & Polling (Priority: P2)

As a user, I want the UI to poll the backend server at a customizable frequency defined by the Source configuration (scrape interval) and render the processed data in dynamic tables so that I can see the latest monitoring information without overwhelming the backend.

**Why this priority**: The frontend allows users to visualize the monitoring data collected by the backend efficiently.

**Independent Test**: Can be tested using mock backend responses to ensure the frontend successfully polls at intervals and renders dynamic tables with proper styling.

**Acceptance Scenarios**:

1. **Given** the frontend application is running, **When** it polls the backend server, **Then** it correctly renders a table representing the parsed dashboard data and applies the correct styling.

---

### Edge Cases & Failure Handling

- **Script Exceptions & Secret Failures**: If a `Collector`, `TableDashboard`, or secret resolution throws an error, the backend MUST NOT crash. It must log the exception as an error. The UI must display the error reason in the dashboard area. If the error is specific to a column, that column must be marked in red instead of failing the entire dashboard.
- **Malformed Configurations**: If the store encounters malformed files, the backend logs a warning/error and ignores the file entirely, continuing to serve valid configurations.
- **Frontend Disconnect**: If the static frontend loses connection to the backend, it stops updating data and displays a "Disconnected" banner at the top. When attempting to reconnect, it displays a "Connecting..." banner.
- **Infinite Yields & Data Limits**: To prevent memory exhaustion, data collection is bounded by a `max_data` parameter. 
  - If a `Collector` yields infinitely, reading stops once `max_data` items are yielded.
  - If a `Collector` returns a list larger than `max_data`, the list is truncated.
  - The `max_data` limit is configured *per collector* within the dashboard (e.g., via a `getCollector` method) to support future SQLite multi-source joins.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a generalized Store interface to load configurations via periodic auto-polling of a file-system or version-controlled store.
- **FR-002**: System MUST parse "Source" entities, defined as Python classes extending a base `Collector` class. The `Collector` must implement a `collect` method that returns or yields a collection of data. Sub-collectors MUST be supported for inheritance.
- **FR-003**: System MUST resolve credentials securely via an `@secret("secret_name")` annotation in the `Collector` class. Secrets are resolved using Host Environment variables before executing Source scripts. (HashiCorp Vault or k8s secrets are future planned features).
- **FR-004**: System MUST parse "Dashboard" entities, defined as Python classes extending a base `TableDashboard`. Properties/methods with a `@dashboardColumn(<column-name>)` annotation MUST map to table columns.
- **FR-005**: System MUST apply CSS styling rules defined in Dashboards to the extracted data.
- **FR-006**: System MUST serve the processed and styled data via an API endpoint.
- **FR-007**: System MUST enforce a configurable `max_data` limit per Collector during execution to truncate oversized lists or stop reading infinite yields.
- **FR-008**: System MUST provide a frontend interface that polls the backend at an interval dynamically defined by the specific Source configuration (e.g., scrape interval) and renders the data in dynamic tables.

### Key Entities

- **Source (`Collector`)**: Configuration defining how to fetch data. Must extend `Collector`, implement `collect()` (returning/yielding data), and supports `@secret` annotations. The `Collector` base has default values for `max_data` and `scrape_interval` (which defaults from an environment variable). Dashboards can override these defaults. Executes in a secure sandbox.
- **Dashboard (`TableDashboard`)**: Configuration referencing a Source. Must extend `TableDashboard` and use `@dashboardColumn` annotations to define table schema and styling logic. (Future: Support SQLite in-memory for multi-source joins).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully executes well-formed Source scripts and returns data.
- **SC-002**: Malicious or unauthorized code inside a Source is consistently blocked by the sandbox without compromising the host.
- **SC-003**: Frontend table renders correctly applying mapped CSS styling based on the dashboard configuration values.
- **SC-004**: The system loads configurations from the persistent GitOps store without validation errors.
