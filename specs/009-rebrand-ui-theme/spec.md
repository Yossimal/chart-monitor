# Feature Specification: Rebrand UI & Theme Refresh

**Feature Branch**: `009-rebrand-ui-theme`
**Created**: 2026-04-15
**Status**: Draft
**Input**: User description: "change the logo of the project (also the title icon) to the image in chart-monitor-logo.png; the theme of the webapp will integrate with that logo (in dark and light); change the modularity of the webapp so there will be no need for scroll if the screen is not super small; change the logo of the docs also to that image; change the theme of the docs to satisfy the project; change the sidebar to be from top to bottom; move the sync button to the top of the sidebar and put a git (not github) icon instead of the arrow icon; add refresh icon to the refresh button"

## Clarifications

### Session 2026-04-15

- Q: At what viewport width should the "no outer scroll" guarantee stop applying? → A: 1440px, with fully responsive collapse/scroll below it.
- Q: How far should the MkDocs docs theme be customized to match the rebrand? → A: Configure Material for MkDocs theme with light/dark palette, logo, favicon, and brand accents.
- Q: Which color from the logo should anchor the primary/brand color? → A: Sample the dominant non-neutral hue from `chart-monitor-logo.png`; derive primary + a complementary accent from it.
- Q: Which refresh control(s) should receive the new refresh icon? → A: All refresh controls in the app (global, per-chart, and any others).
- Q: How should the logo be prepared and delivered across surfaces? → A: Derive a small asset set from the source PNG — favicon.ico (16/32/48), 192/512 PNGs, and one header-sized PNG.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cohesive Brand Identity Across App & Docs (Priority: P1)

A user opens the chart-monitor web application and its in-app documentation and immediately sees a consistent, professional brand: the same new logo appears as the favicon/title icon, in the app header, and on every docs page. The color palette of both surfaces visibly harmonizes with the logo in both light and dark modes, making the product feel like a single, designed experience rather than two separate surfaces.

**Why this priority**: Brand identity is the first thing every user experiences. A mismatched or placeholder logo erodes trust on every page view, and the docs are where new users are sent — they must feel like part of the same product. This is the highest-leverage change.

**Independent Test**: Load the app and the docs in both light and dark modes on a fresh browser; verify the logo file appears in the browser tab, header, and docs header, and that primary/accent colors on both surfaces are visibly derived from the logo's palette.

**Acceptance Scenarios**:

1. **Given** the web app is open in a browser tab, **When** the user looks at the tab and the app header, **Then** both display the new chart-monitor logo image.
2. **Given** the user navigates to the in-app documentation, **When** the docs page renders, **Then** the same new logo appears in the docs header/branding area.
3. **Given** the user toggles between light and dark themes, **When** each theme is active, **Then** the primary colors, surfaces, and accents on both the app and the docs are visibly aligned with the logo's color palette and remain legible (sufficient contrast).

---

### User Story 2 - No-Scroll Layout on Normal Screens (Priority: P1)

A user on any typical laptop or desktop screen can see and interact with the main workspace (sidebar, charts area, and key controls) without needing to scroll the outer page. Only on unusually small viewports (narrow laptops, tablets in portrait, or smaller) does the layout fall back to scrolling behavior.

**Why this priority**: Unnecessary page-level scrolling on normal screens creates friction on every session and hides controls that should be one glance away. This is a daily quality-of-life win that affects every user.

**Independent Test**: Open the app at a 1440px-wide viewport (and common resolutions up to 1920×1080); confirm the full application chrome — header, sidebar, main content area, and footer controls — fits without a vertical page scrollbar, while internal regions (chart lists, data tables) scroll within their own containers as needed. Then reduce width below 1440px and confirm the layout remains fully responsive (regions collapse, stack, or scroll) without clipping controls.

**Acceptance Scenarios**:

1. **Given** the user has a viewport of at least 1440px width, **When** the app loads, **Then** no outer page vertical scrollbar appears and all primary UI regions are visible.
2. **Given** a long list of charts or a wide data set, **When** it exceeds its container, **Then** only the inner container scrolls, not the whole page.
3. **Given** the viewport is reduced below 1440px width, **When** the layout can no longer fit at the full desktop density, **Then** the app responsively collapses/stacks regions and/or allows scrolling rather than clipping content.

---

### User Story 3 - Vertical Sidebar with Sync at Top (Priority: P2)

A user sees a vertically-oriented sidebar that runs top-to-bottom along the side of the app. The GitOps sync button is the first, most prominent control at the top of the sidebar, labeled or iconified with a generic Git icon (not a GitHub-specific mark). The user can trigger a sync in one click from a predictable, always-visible location.

**Why this priority**: Sync is one of the most frequent operator actions. Placing it at the top of a persistent vertical sidebar makes it discoverable and reachable from any screen state. Using a neutral Git icon also removes an incorrect implication that the product is tied specifically to GitHub.

**Independent Test**: Open the app; verify the sidebar runs vertically from the top of the main area to the bottom, the sync button sits at its top, and the icon on that button is a generic Git icon rather than the GitHub octocat or an arrow.

**Acceptance Scenarios**:

1. **Given** the app is loaded, **When** the user looks at the sidebar, **Then** it is a vertical column running from the top of the content area to the bottom.
2. **Given** the sidebar is visible, **When** the user scans from the top, **Then** the first interactive element is the "Sync" action with a generic Git icon.
3. **Given** the user clicks the sync button, **When** the click is registered, **Then** the existing GitOps sync behavior is triggered unchanged.

---

### User Story 4 - Refresh Button Shows a Refresh Icon (Priority: P3)

A user looking for the refresh/reload action can recognize it at a glance by its standard circular-arrow refresh icon, rather than having to read a text label or guess from a non-iconic button.

**Why this priority**: Small affordance improvement — the button already exists and works; adding an icon simply makes it faster to locate. High value-to-effort ratio, but lower overall impact than branding and layout.

**Independent Test**: Locate the refresh button in the UI; confirm a recognizable refresh (circular-arrow) icon is displayed on it.

**Acceptance Scenarios**:

1. **Given** the app is loaded, **When** the user looks at the refresh control, **Then** a refresh icon is visibly rendered on it.
2. **Given** the user clicks the refresh button, **When** the click is registered, **Then** the existing refresh behavior is triggered unchanged.

---

### Edge Cases

- The logo image must render crisply on both standard and high-DPI (retina) displays without pixelation.
- Users who have chosen a specific theme (light or dark) must retain their choice after the rebrand; no forced reset.
- On very small viewports (below the "small screen" threshold), the layout must remain usable — scrolling is acceptable, but no control may become inaccessible.
- Derived theme colors must maintain accessible text contrast (at least WCAG AA) in both modes, even when the logo palette skews saturated.
- Docs theme changes must not break existing in-page navigation, search, or code-block readability.
- If the logo asset fails to load, a text fallback of the product name must render in its place rather than a broken-image placeholder.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The web application MUST use a derivative of `chart-monitor-logo.png` as its browser tab favicon/title icon, delivered via a multi-size `favicon.ico` (16/32/48) plus 192×192 and 512×512 PNGs for high-DPI and PWA contexts.
- **FR-002**: The web application MUST display a header-sized PNG derivative of `chart-monitor-logo.png` in its main header/branding area, sized to render crisply at standard and high-DPI resolutions without pixelation.
- **FR-003**: The in-app documentation (served via MkDocs) MUST use the Material for MkDocs theme configured to display the header-sized logo derivative as its header logo and the favicon derivative(s) as its favicon.
- **FR-004**: Both the web application and the documentation MUST offer a light theme and a dark theme whose primary and accent colors are derived from and visibly harmonize with the logo's color palette; for the docs, this is expressed via the Material theme's `palette` configuration (scheme + primary + accent) rather than hand-written CSS overrides.
- **FR-005**: Theme colors MUST meet WCAG AA contrast standards for body text and primary interactive elements in both modes.
- **FR-006**: The web application's main layout MUST fit within a viewport of 1440px width (and above) without producing an outer page vertical scrollbar.
- **FR-007**: On viewports narrower than 1440px, the layout MUST be fully responsive — regions may collapse, stack, or scroll — with no controls clipped or made inaccessible at any width down to a standard mobile portrait (~360px).
- **FR-008**: Internal scrollable regions (chart lists, tables, etc.) MUST scroll within their own containers rather than causing the outer page to scroll.
- **FR-009**: The application's sidebar MUST be laid out vertically, running from the top of the main content area to the bottom.
- **FR-010**: The GitOps sync control MUST be positioned at the top of the sidebar as its first interactive element.
- **FR-011**: The sync control's icon MUST be a generic Git icon (not a GitHub-specific mark and not the prior arrow icon).
- **FR-012**: Every refresh control in the application — global dashboard refresh, per-chart refresh, and any other refresh action — MUST display a recognizable refresh (circular-arrow) icon, consistently styled across all instances.
- **FR-013**: Rebranding and layout changes MUST NOT alter the underlying behavior of sync, refresh, or other existing controls.
- **FR-014**: Users' previously selected theme preference (light/dark) MUST be preserved across the rebrand.

### Key Entities

- **Brand Asset**: The `chart-monitor-logo.png` source image plus the derived asset set — `favicon.ico` (16/32/48), 192×192 PNG, 512×512 PNG, and a header-sized PNG — used wherever product branding is shown (app favicon, app header, docs favicon, docs header).
- **Theme**: A named color palette (light or dark variant) derived from the logo, applied consistently across the app and the docs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of user-facing product surfaces that currently show a logo (app tab icon, app header, docs tab icon, docs header) display the new `chart-monitor-logo.png`.
- **SC-002**: On viewports 1440px wide and larger, 0 outer page vertical scrollbars appear on the primary application view at initial load; on viewports narrower than 1440px, the layout remains usable with no clipped or inaccessible controls down to ~360px.
- **SC-003**: Both light and dark themes pass WCAG AA contrast checks for body text and primary interactive elements across the app and docs.
- **SC-004**: A first-time user can locate and trigger the sync action within 5 seconds of seeing the app for the first time (measured in usability review).
- **SC-005**: The refresh control is correctly identified by icon alone (no label needed) by at least 9 out of 10 reviewers in a quick recognition test.
- **SC-006**: Zero regressions are reported in sync, refresh, or theme-toggle behavior after the rebrand lands.

## Assumptions

- The no-scroll guarantee applies at 1440px viewport width and above; below 1440px the layout is fully responsive (collapse/stack/scroll) down to standard mobile widths (~360px).
- The primary design target is 1920×1080; 1440px is the minimum width at which the desktop no-scroll layout must hold.
- The logo file `chart-monitor-logo.png` committed at the repository root is the authoritative source-of-truth brand asset; all delivered assets (favicon.ico, 192/512 PNGs, header PNG) are derived from it and kept in sync via a documented regeneration step.
- Theme colors will be derived from the logo palette using standard color-system practices (primary, surface, accent, text-on-primary, etc.); exact hex values are a design-time decision, not a spec-time one.
- The brand primary color is sampled from the dominant non-neutral hue in `chart-monitor-logo.png`; a complementary accent is derived from it. The same anchor is applied in the app's CSS variables and in MkDocs Material's `palette.primary`/`palette.accent`.
- The existing theme toggle UX (user-selectable light/dark) is retained; this feature updates the palettes, not the toggling mechanism.
- The "git (not github)" icon refers to a vendor-neutral Git mark (e.g., a generic branching/commit glyph), not the GitHub octocat.
