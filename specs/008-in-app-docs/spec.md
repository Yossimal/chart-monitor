# Feature Specification: In-App Documentation (/docs)

**Feature Branch**: `008-in-app-docs`
**Created**: 2026-04-14
**Status**: Draft
**Input**: User description: "Add a rich, in-app documentation page reachable at /docs that comprehensively covers every user-facing aspect of Chart-Monitor: connecting a Git repository, what Collectors and Dashboards are, how to create a standard Collector, how to create a SQL Collector, how to load and use secrets, how to create Dashboards, how the project works under the hood, and how to use the UI. A persistent content tree on the right-hand side of the page must let users jump to any section instantly."

## Clarifications

### Session 2026-04-15

- Q: Where should the in-app entry point to `/docs` live? → A: A single persistent link labelled "Docs" in the app header, visible on every page.
- Q: Should the docs page provide in-page search? → A: Yes — a client-side text search box that filters the content tree and jumps to matches.
- Q: How does `/docs` fit into the app's routing model? → A: Separate standalone HTML page (`docs.html`) served at `/docs`, independent of the main SPA.
- Q: Should code blocks use syntax highlighting? → A: Full syntax highlighting for all detected languages, bundled with no CDN dependency.
- Q: Should the docs page share the app's light/dark theme preference? → A: Read the same browser-stored theme key set by the main app; fall back to OS `prefers-color-scheme` if unset. No separate toggle on the docs page.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and browse the full docs page (Priority: P1)

A new user opens the application and navigates to `/docs`. They are presented with a single, richly-formatted documentation page that covers every capability of Chart-Monitor. A content tree anchored on the right-hand side of the page lists every section and sub-section; clicking any entry scrolls smoothly to that section and highlights the active entry as the user reads.

**Why this priority**: Without a reachable docs page with navigable structure, none of the individual documentation topics can be consumed. This is the minimum viable delivery — a working `/docs` route with a table-of-contents tree and the full body of documentation rendered — and delivers immediate value even before any single topic is polished.

**Independent Test**: Open the app, navigate to the `/docs` URL directly, and verify (a) the page renders without errors, (b) the right-hand content tree is visible and lists all top-level sections, (c) clicking a tree entry scrolls to the matching heading, and (d) scrolling the body updates the highlighted entry in the tree.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** a user navigates to `/docs`, **Then** the docs page loads with a readable body and a visible right-side content tree.
2. **Given** the docs page is open, **When** the user clicks any entry in the content tree, **Then** the page scrolls to the corresponding section and that entry becomes the highlighted/active tree entry.
3. **Given** the docs page is open, **When** the user scrolls the body manually, **Then** the active entry in the content tree updates to reflect the section currently in view.
4. **Given** the user shares a link to a specific section (e.g. `/docs#creating-a-collector`), **When** another user opens that link, **Then** the page loads scrolled to that section and the matching tree entry is highlighted.
5. **Given** the docs page is open on a narrow screen, **When** the viewport is below the tablet breakpoint, **Then** the content tree collapses into an accessible on-demand menu so the body remains readable.

---

### User Story 2 - Learn how to connect a Git repository (Priority: P1)

A first-time operator needs to connect Chart-Monitor to their Git repository so monitoring scripts can be loaded. They open `/docs`, jump to the "Connecting a Git Repository" section, and follow the instructions end-to-end — including generating an SSH key, adding it as a deploy/access key on GitHub, GitLab, or Bitbucket, and setting the required environment variables.

**Why this priority**: Connecting a Git repository is a hard prerequisite for any productive use of the product. Without this documentation, new users are blocked at step zero. It shares P1 priority with Story 1 because the page is worthless if this topic is not on it from day one.

**Independent Test**: A user with no prior knowledge of Chart-Monitor can, using only the content of this section, successfully (a) generate an SSH key, (b) register it on a supported Git provider, (c) set the required environment variables, and (d) reach the main application without hitting the "GitOps not configured" screen.

**Acceptance Scenarios**:

1. **Given** a user is on `/docs`, **When** they open the "Connecting a Git Repository" section, **Then** they see step-by-step instructions for GitHub, GitLab, and Bitbucket with copyable commands and clearly labelled environment variables.
2. **Given** the section is open, **When** the user needs to switch between providers, **Then** they can toggle provider-specific guidance without leaving the page.
3. **Given** the instructions are followed, **When** the user restarts the backend, **Then** the guidance matches what the application actually requires (SSH URL, SSH key path, target path, sync secret).

---

### User Story 3 - Understand what Collectors and Dashboards are (Priority: P1)

A user who has just connected their repo opens `/docs` to understand the two core concepts of the product before writing any YAML. They read a conceptual overview that explains what a Collector is, what a Dashboard is, how they relate to each other, and where each lives in the repository.

**Why this priority**: Every other documentation topic assumes the reader knows what a Collector and a Dashboard are. Without this conceptual grounding, all subsequent how-to content is unusable. This belongs in P1 with the other foundational topics.

**Independent Test**: After reading only the "Concepts: Collectors and Dashboards" section, a reader can correctly answer: (a) what a Collector produces, (b) what a Dashboard consumes, (c) how many Collectors a Dashboard can reference, and (d) where in the repo each type of file is expected to live.

**Acceptance Scenarios**:

1. **Given** the docs page is open, **When** the user reads the Concepts section, **Then** they see a clear diagram or structured explanation describing the Collector → Dashboard data flow.
2. **Given** the Concepts section is being read, **When** the user hovers or clicks an inline link to "Creating a Collector" or "Creating a Dashboard", **Then** the page scrolls to the relevant how-to section.

---

### User Story 4 - Create a standard Collector (Priority: P1)

An operator wants to pull data from a REST endpoint and expose it as tabular data. They open `/docs`, jump to "Creating a Collector", and follow a complete walkthrough: file location, required and optional fields, the Python script body written under RestrictedPython, the expected return shape, how the output is typed, and a full, working example they can copy.

**Why this priority**: Collectors are the data source for every Dashboard. Without complete Collector documentation, users cannot produce any data to display. P1.

**Independent Test**: Using only this section, a reader creates a new Collector YAML file in the repo, writes a script that fetches a public JSON endpoint, syncs the repo, and sees the Collector appear and produce rows in a Dashboard that references it.

**Acceptance Scenarios**:

1. **Given** the docs page is open, **When** the user reads the Collector how-to, **Then** they see the full schema (required fields, optional fields, allowed types) with at least one complete worked example.
2. **Given** the example is followed, **When** the reader saves the file under the expected path and triggers a sync, **Then** the Collector is recognized by the backend and becomes available to Dashboards.
3. **Given** the script body uses RestrictedPython, **When** the user writes it, **Then** the documentation explicitly lists which standard-library functions, modules, and helpers are permitted inside the sandbox.

---

### User Story 5 - Create a SQL Collector (Priority: P1)

A user wants to combine multiple data sources or reshape existing data using SQL. They open `/docs`, jump to "Creating a SQL Collector", and learn how SQL Collectors differ from standard Collectors, how to reference upstream Collectors as tables, how to write the query, and how the result is materialized.

**Why this priority**: SQL Collectors are a distinct, first-class feature of the product. They are the primary mechanism for joining and aggregating across data sources and cannot be inferred from the standard-Collector docs. P1.

**Independent Test**: Using only this section, a reader creates a SQL Collector that joins two existing upstream Collectors, syncs, and sees the result appear as a queryable table in a Dashboard.

**Acceptance Scenarios**:

1. **Given** the section is open, **When** the user reads it, **Then** they see a complete worked example that declares upstream Collector inputs and a SQL query that produces a new result set.
2. **Given** the SQL dialect has caveats or limits, **When** the user reads the section, **Then** those limits (supported SQL features, row limits, performance notes) are clearly called out.

---

### User Story 6 - Load and use secrets (Priority: P1)

An operator needs to call an API that requires an authentication token. They open `/docs`, jump to "Loading Secrets", and learn where secrets come from, how to reference them inside a Collector script, and what happens if a referenced secret is missing.

**Why this priority**: Realistic data sources almost always require credentials. Without secret-loading documentation, Collectors cannot call authenticated endpoints, which rules out most real-world use cases. P1.

**Independent Test**: Using only this section, a reader configures one secret, references it from a Collector, and confirms the Collector can call an authenticated endpoint without the secret value ever appearing in the YAML file, logs, or rendered Dashboard.

**Acceptance Scenarios**:

1. **Given** the section is open, **When** the user reads it, **Then** they see a complete walkthrough of where secrets are defined, how they are referenced, and how missing-secret errors surface.
2. **Given** a secret is referenced in a script, **When** the Collector runs, **Then** the documented behaviour (value substitution, not leaked in logs, error on missing) matches what the product does.

---

### User Story 7 - Create a Dashboard (Priority: P1)

A user who has working Collectors wants to display the data. They open `/docs`, jump to "Creating a Dashboard", and follow a complete walkthrough covering the Dashboard file schema, how to reference one or more Collectors, how to declare columns and their types, how to configure any visualization options, and a full worked example.

**Why this priority**: Dashboards are the user-facing surface of the product. Without Dashboard documentation, Collector output cannot be consumed. P1.

**Independent Test**: Using only this section, a reader creates a Dashboard YAML that references an existing Collector, syncs, and sees the Dashboard appear in the sidebar with data rendered correctly.

**Acceptance Scenarios**:

1. **Given** the section is open, **When** the user reads it, **Then** they see the full Dashboard schema with every supported field documented and at least one complete working example.
2. **Given** a Dashboard references a non-existent Collector, **When** the user reads the section, **Then** the expected error behaviour is clearly described.

---

### User Story 8 - Learn how to use the UI (Priority: P2)

A user who has a working Dashboard wants to get the most out of the interface. They open `/docs`, jump to "Using the UI", and learn how to search dashboards, toggle dark mode, use the per-column filter menu, sort columns, write SQL filters, trigger a sync, and interpret the connection-status banners.

**Why this priority**: The UI is already mostly discoverable, so this is a P2 — valuable and expected in complete documentation, but a working user can usually figure out basic interaction without it.

**Independent Test**: Using only this section, a reader can: open a per-column filter menu, apply a multi-value filter, clear all filters, switch to SQL-filter mode, toggle the theme, and trigger a manual sync.

**Acceptance Scenarios**:

1. **Given** the section is open, **When** the user reads it, **Then** every interactive element of the main UI (sidebar, header, column menu, SQL panel, sync modal, connection banners) is explained with its purpose and keyboard/mouse behaviour.
2. **Given** the UI changes in a future release, **When** this section is read, **Then** the guidance still reflects observable UI behaviour (i.e. the section is maintained alongside UI changes, and out-of-date screenshots are avoided in favour of descriptive text).

---

### User Story 9 - Understand how the project works under the hood (Priority: P3)

A power user or reviewer wants to understand the architecture before extending or auditing the project. They open `/docs`, jump to "How It Works Under The Hood", and read a structured explanation of the data flow: GitOps sync → YAML parsing → sandboxed Collector execution → optional SQL layer → Dashboard rendering → UI interactions.

**Why this priority**: Architectural context is valuable but not required for day-to-day use. P3.

**Independent Test**: After reading this section, a reader can describe, in their own words, (a) how a change in the Git repo reaches the UI, (b) where sandboxing is applied, (c) where SQL is executed (backend vs browser), and (d) which data is persisted vs recomputed.

**Acceptance Scenarios**:

1. **Given** the section is open, **When** the user reads it, **Then** the end-to-end data flow is documented with each major component clearly named and its role explained.
2. **Given** the user wants deeper detail, **When** they reach the end of the section, **Then** references or links to the relevant source areas (conceptual, not line-numbers) are provided.

---

### Edge Cases

- The docs page is opened before any Git repository has been connected — the page must still render fully without depending on any Collector or Dashboard data.
- The docs page is opened on a narrow viewport — the right-side content tree must degrade gracefully (e.g. collapse behind a toggle) without losing navigability.
- A deep link like `/docs#creating-a-sql-collector` is opened in a new tab — the page must scroll to the target heading on first paint, not after a delayed content load.
- The user follows an internal link from one section to another — browser back/forward must return the user to the previous scroll position and restore the previously active tree entry.
- The content tree is long enough to overflow the viewport — it must be independently scrollable and must still keep the currently active entry visible as the user scrolls the body.
- A section contains a long code block — horizontal overflow must not break the page layout or the content tree.
- The user’s theme preference is dark mode — every documentation element (prose, code blocks, tree, active-entry highlight) must render with appropriate contrast.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST expose the documentation at the route `/docs` and it MUST be reachable directly by URL without requiring any prior navigation.
- **FR-002**: The docs page MUST render its full body content and the right-side content tree even when GitOps is not configured, so that new users can read setup instructions before completing setup.
- **FR-003**: The docs page MUST display a persistent content tree on the right-hand side of the viewport at desktop widths, listing every section and sub-section of the documentation.
- **FR-004**: Every section and sub-section MUST have a stable fragment anchor so deep links such as `/docs#creating-a-dashboard` scroll to that section on page load.
- **FR-005**: Clicking an entry in the content tree MUST scroll the page to the corresponding section and MUST update the browser URL fragment to that section’s anchor.
- **FR-006**: As the user scrolls the body, the content tree MUST highlight the entry corresponding to the section currently in view.
- **FR-007**: The content tree MUST remain navigable on narrow viewports by collapsing into an accessible on-demand menu (e.g. a toggle) rather than being hidden outright.
- **FR-008**: The documentation MUST include a top-level section covering connecting a Git repository, with complete, copyable step-by-step guidance for GitHub, GitLab, and Bitbucket, and a full listing of required environment variables.
- **FR-009**: The documentation MUST include a conceptual section explaining Collectors, Dashboards, and the relationship between them, including where each type of file lives in the repository.
- **FR-010**: The documentation MUST include a how-to section for creating a standard Collector, covering file location, the full schema, the script body and its RestrictedPython constraints, the expected return shape, and at least one complete worked example.
- **FR-011**: The documentation MUST include a how-to section for creating a SQL Collector, covering how SQL Collectors differ from standard Collectors, how upstream Collectors are referenced, and at least one complete worked example.
- **FR-012**: The documentation MUST include a section on loading secrets, covering where secrets are defined, how to reference them from a Collector script, and the behaviour when a referenced secret is missing.
- **FR-013**: The documentation MUST include a how-to section for creating a Dashboard, covering the full schema, how Collectors are referenced, how columns and types are declared, and at least one complete worked example.
- **FR-014**: The documentation MUST include a section on using the UI, covering the sidebar, header controls (including theme toggle), per-column filter menu, column sorting, SQL filter panel, the sync modal, and the connection-status banners.
- **FR-015**: The documentation MUST include a section explaining how the project works under the hood, covering the end-to-end data flow from Git sync through sandboxed Collector execution, optional SQL layer, Dashboard rendering, and UI interactions.
- **FR-016**: The documentation MUST render correctly in both light and dark themes, matching the rest of the application’s theming behaviour.
- **FR-017**: The documentation MUST render code blocks as visually distinct, monospaced, horizontally-scrollable blocks without breaking page layout.
- **FR-018**: The documentation content MUST be authored and maintained as part of the project repository so it is versioned alongside the code and can be updated in the same pull requests as behaviour changes.
- **FR-019**: The docs page MUST NOT require any backend calls that depend on user-configured data (Collectors, Dashboards, secrets) in order to render.
- **FR-020**: The docs page MUST be accessible via keyboard: tree entries MUST be focusable, activatable via the keyboard, and each section heading MUST expose a keyboard-reachable anchor link.
- **FR-021**: The main application header MUST display a single persistent link labelled "Docs" that navigates to `/docs`, visible on every page of the app (including the GitOps-unconfigured page) so users can reach the documentation in one click.
- **FR-022**: The docs page MUST provide a client-side text search box associated with the content tree. Typing in it MUST filter the tree to entries whose section or sub-section titles match the query, and selecting a filtered entry MUST jump to that section. Clearing the search MUST restore the full tree.
- **FR-023**: The documentation MUST be delivered as a separate standalone HTML page (`docs.html`) served at the `/docs` route. It MUST be fully independent of the main application's JavaScript, state, and WASM engine. The "Docs" header link in the main app and in the GitOps-unconfigured page MUST navigate to this page.
- **FR-024**: All code blocks in the documentation MUST use full syntax highlighting for all detected languages (YAML, Python, bash, SQL, and any others present). The highlighting library MUST be bundled with the page — no CDN dependency — consistent with the project's offline-capable posture.
- **FR-025**: The docs page MUST apply the user's theme by reading the same browser-storage key used by the main application, and MUST fall back to the OS `prefers-color-scheme` if no stored preference exists. The docs page does NOT include its own theme toggle.

### Key Entities *(include if feature involves data)*

- **Documentation Section**: A top-level unit of documentation (e.g. "Connecting a Git Repository", "Creating a Collector"). Has a human-readable title, a stable anchor identifier, an ordered set of sub-sections, and body content.
- **Documentation Sub-section**: A child unit of a section. Has a title and a stable anchor identifier; appears as a second-level entry in the content tree.
- **Content Tree Entry**: The navigable representation of a Section or Sub-section in the right-side tree. Knows its anchor target, its depth, and whether it is currently active.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user who has never used Chart-Monitor can, using only `/docs`, connect a Git repository, create a Collector, and create a Dashboard that displays its data in under 30 minutes.
- **SC-002**: 100% of the product’s user-facing capabilities — connecting a repo, standard Collectors, SQL Collectors, secrets, Dashboards, and the UI — are covered by at least one dedicated section in the docs.
- **SC-003**: From any section in the docs, a user can reach any other section in two interactions or fewer (one click on the tree, or scroll + click).
- **SC-004**: Deep-linked section URLs (e.g. `/docs#creating-a-dashboard`) land the user on the target section on first paint in 100% of test cases across desktop and narrow viewports.
- **SC-005**: As the user scrolls the body, the content-tree active-entry highlight reflects the section in view within one scroll frame (no perceptible lag).
- **SC-006**: Support requests that are answered verbatim by an existing docs section drop by at least 50% relative to the pre-launch baseline within the first release cycle after the docs ship.
- **SC-007**: The docs page renders successfully on first load in under 1 second on a typical broadband connection, including the content tree being interactive.
