# Phase 0: Research & Decisions

## Context

The UI Enhancements feature requires handling datasets of up to 10,000 rows in the browser, featuring bidirectional sorting, text filtering with autocomplete, and UI controls for dashboard settings. The strict constraint is to use Vanilla web technologies (HTML, CSS, JS) and avoid modern frameworks (React, Vue, etc.).

## Open Questions & Clarifications

### 1. Handling 10,000 Rows in Vanilla JS (Pagination vs Virtualization)
**Decision**: Implement **Client-Side Pagination** from scratch using Vanilla JS, supplemented by a `<datalist>` or custom DOM list for the autocomplete filter.  
**Rationale**: Paginating 10,000 items in memory using `Array.prototype.slice()` and rendering only 50-100 rows at a time is computationally trivial (well under 10ms for modern browsers) and keeps the DOM extremely light. This easily meets the `< 1s` performance goal for sorting and avoids the need to download or integrate third-party virtualization libraries like Clusterize.js, keeping the dependency tree totally flat and adhering perfectly to the constitution's "Vanilla" and "Clean Code" principles.
**Alternatives considered**:
- *Virtual DOM/Scrolling library (e.g., Clusterize.js)*: Requires managing scroll events, calculating row heights, and integrating an external script. It's more complex than pagination and violates the desire to minimize dependencies when a simpler approach works.
- *Render all 10k rows*: This would bloat the DOM, causing severe jank and failing the performance success criteria.

### 2. Autocomplete for Text Filters
**Decision**: Implement a custom debounced `keyup` event listener that renders a small absolutely positioned `<ul>` dropdown below the input, or utilizes the native HTML5 `<datalist>` tag.
**Rationale**: The native `<datalist>` requires zero JavaScript to display the dropdown, but to filter unique values dynamically from the 10,000 rows, a short JS function will extract unique values for the target column and populate the `<datalist>` or a custom `<ul>`. This is incredibly fast and dependency-free.
**Alternatives considered**:
- *jQuery UI Autocomplete*: Violates the Vanilla JS constraint.
- *Select2 / Choices.js*: Heavyweight libraries that require significant styling overrides and add unnecessary bloat.

### 3. Light/Dark Mode Toggling
**Decision**: Use a data attribute on the `<html>` or `<body>` tag (e.g., `data-theme="dark"`) and define CSS variable overrides in `styles.css`.
**Rationale**: This is the modern, standard way to implement theming in Vanilla CSS and allows instantaneous switching via a simple JS toggle button that updates the attribute and sets `localStorage` to persist the preference.

### 4. Chart/Visual Presentation Placeholder
**Decision**: For `FR-007` (basic data presentation within tables and human-readable time strings), time strings will be parsed using standard `Date` objects and formatted via `Intl.DateTimeFormat` for localization-aware, human-readable output. 
**Rationale**: `Intl.DateTimeFormat` is built into all modern browsers, requiring no external libraries (like `moment.js` or `date-fns`).
