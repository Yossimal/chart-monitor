# Column Filter & Sort

Each column in a Dashboard table has its own filter and sort controls, accessible through a per-column menu.

---

## Opening the column menu

Click the **▾** arrow that appears in any column header to open its filter menu.

```
┌──────────────┬──────────────┬──────────────┐
│ Pod Name ▾   │ Status ▾ •   │ Restarts ▾   │
└──────────────┴──────────────┴──────────────┘
```

The `•` dot next to "Status" indicates an active filter on that column.

---

## The column menu

```
┌─────────────────────────┐
│  ↕ Sort                 │
│  ─────────────────────  │
│  [Search values...]     │
│  ─────────────────────  │
│  ☑ Running              │
│  ☑ Pending              │
│  ☐ CrashLoopBackOff     │
│  ☐ (empty)              │
└─────────────────────────┘
```

### Sort button

Click **↕ Sort** to cycle the sort direction for this column:

| State | Icon | Behaviour |
|-------|------|-----------|
| No sort | ↕ | No sort applied |
| Sort ascending | ↑ | Smallest / A–Z first |
| Sort descending | ↓ | Largest / Z–A first |

Only one column can be sorted at a time. Sorting a new column removes the sort from the previous column.

### Search within the menu

Type in the search box to filter the list of distinct values shown in the menu. This is useful for columns with many distinct values.

### Multi-value checkbox filter

Each distinct value in the column appears as a checkbox. Values are checked (included) by default. **Uncheck** a value to hide all rows where that column contains that value.

- `(empty)` represents rows where the column is `null` or an empty string
- Unchecking all values results in an empty table (no rows match)

---

## Active filter indicator

When a column has at least one value unchecked (filtered), a small coloured **dot** appears in the column header. This lets you see at a glance which columns have active filters.

---

## Clearing filters

### Clear a single column

Re-open the column menu and check all values, or re-check the values you previously unchecked.

### Clear all filters

A **Clear all filters** button appears in the table toolbar whenever any filter (column or SQL) is active. Clicking it removes all column filters and any active SQL filter in one action.

---

## Interaction with SQL filter

Column filters and the SQL filter are **mutually exclusive** — only one mode is active at a time:

- Applying column filters **deactivates** any active SQL filter
- Running a SQL query **deactivates** all column filters

The currently active mode is shown by a badge in the table toolbar.

See [SQL Filter](sql-filter.md) for details on the SQL mode.

---

## Keyboard access

- The column menu can be opened by focusing a column header and pressing **Enter**
- Inside the menu, **Tab** moves between the sort button, search box, and checkboxes
- **Space** toggles a focused checkbox
- **Escape** closes the menu
