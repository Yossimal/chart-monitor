<!--
Sync Impact Report:
- Version change: 1.0.0 -> 1.1.0
- List of modified principles:
  - IV. Secure Execution Sandbox -> IV. Secure Execution Sandbox (allow controlled network access)
  - V. Modern Responsive UI -> V. Vanilla Desktop-First UI
- Added sections: N/A
- Removed sections: N/A
- Templates requiring updates:
  - .specify/templates/plan-template.md (✅ verified no changes needed)
  - .specify/templates/spec-template.md (✅ verified no changes needed)
  - .specify/templates/tasks-template.md (✅ verified no changes needed)
- Follow-up TODOs: None
-->
# Chart-Monitor Constitution

## Core Principles

### I. Dynamic Data Engine
Chart-Monitor MUST act as a dynamic data extraction, transformation, and visualization engine. It MUST provide a generalized way to execute small, safe Python scripts against external systems (like Kubernetes APIs, databases, or Git providers), extract specified data fields, apply styling rules, and present the results in customizable dashboards.
*Rationale: To provide maximum flexibility for monitoring diverse data sources without hardcoding integrations.*

### II. Storage Agnostic & GitOps First
System specifications (Sources and Dashboards) MUST be decoupled from the Kubernetes API. The application MUST support multiple storage backends, starting with a "Pure GitOps" file-system/Git approach. Kubernetes CRDs may be supported as an optional implementation choice.
*Rationale: Ensures the system can run outside of Kubernetes and integrates naturally with GitOps workflows.*

### III. Strict Typing & Clean Code
The backend MUST be written in Python 3.11+ with strict typing enforced. The frontend MUST be written in TypeScript. Clean code practices MUST be followed across the entire codebase.
*Rationale: Prevents runtime type errors, improves developer experience, and ensures long-term maintainability.*

### IV. Secure Execution Sandbox
Core execution logic MUST run within a secure sandbox using `RestrictedPython`. Dynamically executed scripts MUST have controlled network access to collect data from providers, but MUST NOT have unrestricted access to the host system or environment variables.
*Rationale: Allows users to write custom extraction and transformation scripts dynamically that can securely interact with external APIs without compromising the host system.*

### V. Vanilla Desktop-First UI
The user interface MUST be built with Vanilla web technologies (HTML, CSS, JS) to ensure maximum future flexibility without framework lock-in. It MUST prioritize comfortable desktop monitoring functionality over broad responsive behavior.
*Rationale: Vanilla technologies ensure longevity and reduced maintenance overhead. Desktop-first optimization acknowledges the primary context in which monitoring dashboards are consumed.*

## Governance

Amendments to this constitution require documentation, approval, and a migration plan if applicable. All PRs/reviews MUST verify compliance with these core principles. Any deviation or complexity MUST be explicitly justified.

**Version**: 1.1.0 | **Ratified**: 2026-03-09 | **Last Amended**: 2026-03-09
