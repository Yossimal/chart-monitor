# Feature Specification: Per-Column Filter Menu

**Feature Branch**: `007-column-filter-menu`  
**Created**: 2026-04-12  
**Status**: Draft  
**Input**: User description: "the filter will be per row filter - instead of large filter input on the top, the user will be able to click on a row name and then a little menu will be open. In the menu, the user will be able to sort by that row when clicking on the sort button (second click will revert the order). Also, a textbox will be under the button and under that textbox there will be a list of all the available values and checkbox near each value. When typing to that textbox, the values will be filtered, when marking one of the checkbox, the data will be filtered so only the data with the marked checkbox value in that row will appear. The sql will move to the bottom and there will be SQL button that will execute the sql INSTEAD OF the sort or the checkbox filter. The applied filter will be the last one that the user set up."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sort a Column via Header Menu (Priority: P1)

A user viewing a data table wants to sort the data by a specific column. They click the column header to open a small menu, then click the sort button. The data reorders accordingly. Clicking the sort button again reverses the order.

**Why this priority**: Sorting is the most commonly needed interaction. It delivers immediate, visible value with a single action and forms the foundation for all other column-level interactions.

**Independent Test**: Can be fully tested by clicking a column header, pressing the sort button, and verifying the data rows reorder — then clicking again to verify reversal.

**Acceptance Scenarios**:

1. **Given** a data table is displayed, **When** the user clicks a column header, **Then** a menu opens anchored to that column header.
2. **Given** the column menu is open, **When** the user clicks the Sort button, **Then** the table rows are sorted ascending by that column's values.
3. **Given** the table is sorted ascending by a column, **When** the user clicks the Sort button again (same column menu), **Then** the sort order reverses to descending.
4. **Given** the table is sorted by column A, **When** the user opens column B's menu and sorts by column B, **Then** the sort is applied to column B and column A's sort is cleared.

---

### User Story 2 - Filter by Column Values via Checkboxes (Priority: P2)

A user wants to narrow down the displayed rows to only those matching specific values in a column. They click the column header, see a list of all distinct values for that column with checkboxes, check one or more values, and the table instantly updates to show only matching rows.

**Why this priority**: Value-based filtering is the primary data exploration action. It provides targeted results without requiring knowledge of SQL.

**Independent Test**: Can be fully tested by opening a column menu, checking one value, and verifying only rows with that value in that column remain visible.

**Acceptance Scenarios**:

1. **Given** the column menu is open, **Then** a list of all distinct values for that column is displayed, each with an unchecked checkbox.
2. **Given** the column menu is open with values listed, **When** the user checks one or more checkboxes, **Then** the table updates to show only rows where the column value matches any checked value.
3. **Given** one or more checkboxes are checked, **When** the user unchecks all checkboxes, **Then** the table returns to showing all rows (no filter active).
4. **Given** filters are applied via checkboxes, **When** the user opens a different column's menu and applies checkbox filters there too, **Then** both column filters are combined (rows must match all active column filters).

---

### User Story 3 - Search Within Column Value List (Priority: P2)

When a column has many distinct values, the user can type into a search box within the column menu to narrow the displayed value list, making it easier to find and select specific values.

**Why this priority**: Enhances usability for columns with large cardinality (e.g., hundreds of unique values). Without it, the checkbox list becomes unwieldy.

**Independent Test**: Can be fully tested by opening a column menu with many distinct values, typing in the search box, and verifying the checkbox list filters to only show matching values.

**Acceptance Scenarios**:

1. **Given** the column menu is open, **Then** a text input (search box) is displayed above the value list.
2. **Given** the search box is focused, **When** the user types text, **Then** the value list below updates in real-time to show only values containing the typed text (case-insensitive).
3. **Given** a search term is entered and some values are hidden, **When** the user clears the search box, **Then** all distinct values reappear in the list.
4. **Given** a search term is active, **When** the user checks a visible value, **Then** that value's filter is applied regardless of whether the search box is then cleared.

---

### User Story 4 - Execute SQL as an Alternative Filter (Priority: P3)

A power user wants to apply a custom SQL query to filter or transform the data, bypassing the checkbox/sort UI. The SQL editor is now located at the bottom of the page, and there is a dedicated "Run SQL" button that applies the SQL query as the active filter — replacing any sort or checkbox filters.

**Why this priority**: Provides advanced flexibility for users who know SQL, without cluttering the primary UI. The SQL mode is an escape hatch, not the default path.

**Independent Test**: Can be fully tested by typing a valid SQL query in the bottom editor, clicking the SQL button, and verifying the table reflects the query results instead of any previously applied checkbox/sort filters.

**Acceptance Scenarios**:

1. **Given** the page is loaded, **Then** the SQL editor is displayed at the bottom of the page (not at the top).
2. **Given** a SQL query is entered in the editor, **When** the user clicks the "Run SQL" button, **Then** the table updates to show the results of the SQL query.
3. **Given** the user has applied checkbox filters, **When** they click "Run SQL", **Then** the SQL results replace the checkbox filter output (SQL takes precedence as the last applied filter).
4. **Given** the user has run a SQL query, **When** they apply a checkbox filter or sort on a column, **Then** the table switches back to the checkbox/sort result (the last action applied wins).

---

### Edge Cases

- What happens when a column has no data (all null/empty values)? The value list should show an "(empty)" entry that can be checked.
- What happens when the user searches for a term with no matching values? The list shows an empty state message (e.g., "No values match").
- What happens when sorting is applied and then a checkbox filter is applied — which takes precedence? Sort and checkbox filters are independent: sort controls row order, checkboxes control which rows are visible. Both can be active simultaneously.
- What happens when the SQL query is invalid? The table shows an error message and retains the previous display state.
- What happens when the user clicks outside the open column menu? The menu closes without applying any uncommitted changes.
- What happens when there are many distinct values (e.g., 1000+)? The value list should be scrollable with a fixed max height.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The existing global filter input at the top of the page MUST be removed and replaced by per-column header menus.
- **FR-002**: Each column header MUST be clickable to open a contextual menu anchored to that column.
- **FR-003**: The column menu MUST contain a Sort button that sorts the table by that column ascending on first click and descending on second click.
- **FR-004**: Only one sort column MUST be active at a time; opening a new column's sort clears the previous sort.
- **FR-005**: The column menu MUST display a search/filter text input above the distinct-value list.
- **FR-006**: The column menu MUST display a scrollable list of all distinct values for that column, each with a checkbox.
- **FR-007**: Typing in the search box MUST filter the visible value list in real-time (case-insensitive substring match).
- **FR-008**: Checking one or more value checkboxes MUST filter table rows to only those whose column value matches any checked value (OR logic within a column).
- **FR-009**: Multiple column filters MUST be combinable; rows must satisfy all active column filters simultaneously (AND logic across columns).
- **FR-010**: The SQL editor MUST be relocated to the bottom of the page.
- **FR-011**: A "Run SQL" button MUST execute the SQL query and display its results in the table.
- **FR-012**: The last-applied filter mode MUST take precedence: if the user runs SQL after setting checkboxes, SQL results are shown; if the user applies checkboxes/sort after running SQL, those results are shown instead.
- **FR-013**: Clicking outside an open column menu MUST close it without applying changes.
- **FR-014**: Column menus MUST only be open one at a time; opening a new column's menu closes any other open menu.
- **FR-015**: The full filter state (active sort column and direction, checked values per column, active SQL query, and current filter mode) MUST be encoded in the page URL so that the view is shareable and survives a page refresh.
- **FR-016**: A visible banner or badge MUST be displayed indicating the currently active filter mode — either "Column filters active" or "SQL filter active" — updating whenever the mode changes.
- **FR-017**: A "Clear all filters" button MUST be available that resets all column filters, the active sort, the SQL query, and the filter mode, returning the table to its fully unfiltered state.

### Key Entities

- **Column Menu**: A contextual popup attached to a specific column header, containing the Sort button, search input, and value checklist.
- **Active Sort**: The current sort state — which column and direction (ascending/descending) is applied.
- **Column Filter**: A per-column filter state consisting of zero or more selected values for that column.
- **Filter Mode**: The currently active filter strategy — either "column-filters" (checkboxes + sort) or "sql" (SQL query result). Determined by which was applied last.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can apply a column filter (checkbox selection) in 3 clicks or fewer from any table state.
- **SC-002**: The column menu opens and renders all distinct values within 300ms of clicking the column header for columns with up to 1,000 distinct values.
- **SC-003**: Typing in the search box filters the visible value list within 100ms (no perceptible lag).
- **SC-004**: The table re-renders with filtered/sorted results within 500ms of any checkbox, sort, or SQL action.
- **SC-005**: 90% of users can apply a value filter without consulting documentation (discoverable UI).
- **SC-006**: The SQL editor relocation to the bottom does not break any existing SQL execution functionality.

## Clarifications

### Session 2026-04-12

- Q: Should filter state (active sort, checked values, SQL query, filter mode) persist across page refreshes? → A: URL params — filter state is encoded in the URL (shareable, survives refresh).
- Q: Should the column menu value lists reflect the current visible data or the full original dataset? → A: Always from the full original dataset, regardless of active filter mode or SQL results.
- Q: Should the UI visually indicate which filter mode is currently active (column-filters vs SQL)? → A: Yes — display a banner or badge showing the active mode (e.g., "SQL filter active" / "Column filters active").
- Q: Is a global "clear all filters" action needed? → A: Yes — a "Clear all filters" button resets all column filters, sort, and SQL back to the unfiltered view.
- Q: Should the column menu support keyboard navigation? → A: No — mouse-only interaction is acceptable; keyboard accessibility is out of scope for this feature.

## Assumptions

- The existing data table already has a concept of "columns" and "rows" that can be sorted and filtered client-side or via query.
- Distinct values for a column are always computed from the full original dataset, regardless of what filter mode is active or what a SQL query returned. This ensures the value list is stable and predictable.
- The checkbox filters use OR logic within a column and AND logic across columns (most common and intuitive behavior for this pattern).
- The SQL editor already exists; this feature relocates it and adds a dedicated trigger button — no SQL engine changes are needed.
- The "last applied wins" filter mode behavior means no persistent combination of SQL + checkbox filters; they are mutually exclusive in terms of what the table shows.
- Column menus close when clicking outside (standard dropdown behavior).
- Keyboard accessibility (Tab, Arrow keys, Escape) is explicitly out of scope — mouse-only interaction is sufficient for this feature.
