# Sidebar & Navigation

The sidebar lists all available dashboards and lets you search and switch between them.

---

## Dashboard list

Every Dashboard registered in your Git repository appears in the sidebar as a clickable item. The list is sorted alphabetically by Dashboard ID.

Click any Dashboard name to load it in the main content area. The URL updates to `?dashboard=<id>` so you can bookmark or share a specific dashboard.

---

## Search

Type in the **Search...** box at the top of the sidebar to filter the dashboard list. The filter is case-insensitive and matches anywhere in the dashboard name.

```
Search: pod
────────────────────────
• pod_dashboard
• pod_by_region
```

Clear the search field to see all dashboards again.

---

## Loading state

When a dashboard is first selected, a loading indicator appears in the main content area while the backend fetches data. Subsequent refreshes happen silently (the previous data remains visible until new data arrives).

---

## Empty sidebar

If no dashboards appear:

1. Your Git repository may not be connected — check the [Git setup guide](../getting-started/connect-git.md)
2. No valid Dashboard classes may exist in the repository — check for Python errors with a manual sync
3. The backend may be starting up — wait a few seconds and refresh

---

## Keyboard navigation

- **Tab** — move focus between sidebar items
- **Enter / Space** — activate the focused dashboard
- The search box is reachable via **Tab** and responds to standard text input
