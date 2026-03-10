# Phase 1: Data Model

This document outlines the core entities and state structures required for the UI Enhancements feature.

## 1. Dashboard Configuration (Client State)
Represents the runtime configuration and active user-selected permutations applied to a dashboard view.

**Fields**:
- `activeTheme`: String (`'light'` | `'dark'`)
- `refreshIntervalSeconds`: Number (Overrides default backend interval)
- `maxDataValueLimit`: Number (Clamps numeric charts/tables, `< 0` resets to `0` and clears data)
- `searchQuery`: String (Current input in dashboard list search)
- `tableState`: Object
  - `sortColumn`: String | Null
  - `sortDirection`: String (`'asc'` | `'desc'`)
  - `filterText`: String
  - `currentPage`: Number (0-indexed)

**State Transitions**:
- `ThemeToggle`: `activeTheme` -> `'light'` <-> `'dark'`
- `MaxDataChange`: If user inputs `< 0`, set to `0` and `rows = []`.

## 2. API Response Enhancements (Backend Models)

### CellResult Enhancement
To support exact sorting on formatted strings (e.g. `"85%"` or `"10m 30s"`), the backend `CellResult` model is extended to include a `display` field.

**Fields**:
- `value`: Any (Number, String, Date-string) - The actual raw value used strictly for logical operations like sorting in the UI.
- `display`: String - The human-readable formatted display string presented to the user. Falls back to `value` if omitted.
- `style`: String (CSS classes)

### DashboardMeta Enhancement
The `DashboardMeta` or `DashboardDataResponse` needs to accommodate the `set_name` config property.

**Fields**:
- `set_name`: String (Overrides the Python class name. Max 150 chars. Throws error/renders error field if >150 chars).
