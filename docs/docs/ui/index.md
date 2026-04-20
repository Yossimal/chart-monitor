# Using the UI — Overview

The Chart-Monitor UI is a single-page application that runs in your browser. It connects to the backend via a REST API and auto-refreshes data on a configurable interval.

---

## Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER: [CM] Chart-Monitor   [Docs] [🌙 Dark]  ● last updated  │
├──────────────────┬──────────────────────────────────────────────┤
│                  │                                              │
│   SIDEBAR        │   MAIN CONTENT                               │
│                  │                                              │
│   Dashboards     │   Dashboard table                            │
│   ──────────     │   (columns with filter/sort menus)           │
│   [Search...]    │                                              │
│                  │                                              │
│   • pod_dash     │                                              │
│   • node_dash    │                                              │
│                  │                                              │
│   ──────────     ├──────────────────────────────────────────────┤
│   [↕ Sync]       │   SQL PANEL (shown when SQL filter active)   │
│                  │   SELECT * FROM data WHERE ...    [▶ Run SQL] │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## Areas

| Area | Description |
|------|-------------|
| **Header** | App logo, "Docs" link, theme toggle, last-updated timestamp, connection status dot |
| **Sidebar** | Dashboard list with search; Sync button at the bottom |
| **Main content** | The selected Dashboard rendered as a sortable, filterable table |
| **SQL panel** | Hidden by default; appears when you write an SQL filter |
| **Connection banners** | Full-width banners at the top when the backend connection is lost or recovering |

---

## Quick navigation

- [Sidebar & Navigation](sidebar-and-navigation.md) — search dashboards, select a dashboard
- [Column Filter & Sort](column-filter-and-sort.md) — per-column filters, multi-value selection, sorting
- [SQL Filter](sql-filter.md) — write SQL queries to filter the visible data
- [Data Amount & Paging](data-amount-and-paging.md) — row limits and scroll behaviour
- [Sync & Refresh](sync-and-refresh.md) — manual sync, auto-refresh, connection banners
- [Theme & Settings](theme-and-settings.md) — dark/light mode
