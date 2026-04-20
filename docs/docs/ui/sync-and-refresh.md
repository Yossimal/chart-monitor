# Sync & Refresh

This page covers how Chart-Monitor keeps data up to date: automatic scrape polling, manual Git sync, and connection status.

---

## Auto-refresh (scrape polling)

Chart-Monitor automatically refreshes Dashboard data at a configurable interval. The interval is set by the Collector's `scrape_interval` attribute (default: **30 seconds**, configurable via `CHART_MONITOR_SCRAPE_INTERVAL`).

The **last updated** timestamp in the header shows when data was last received from the backend.

You do not need to do anything to enable auto-refresh — it starts as soon as a Dashboard is selected.

---

## Manual sync from Git

The **↕ Sync Scripts** button at the bottom of the sidebar triggers a manual re-pull from your connected Git repository. Use this after committing new or updated Collector/Dashboard scripts to see the changes immediately rather than waiting for the next automatic background sync (if configured).

### Sync flow

1. Click **↕ Sync Scripts**
2. A modal appears asking for the `SYNC_SECRET`

    ```
    ┌──────────────────────────────────────┐
    │ 🔐 Sync from Git                   × │
    │                                      │
    │ Enter the SYNC_SECRET to             │
    │ authenticate the sync request.       │
    │                                      │
    │ [Enter SYNC_SECRET .............]    │
    │ ☐ Remember me (saves to browser)     │
    │                                      │
    │             [Cancel]  [Sync]         │
    └──────────────────────────────────────┘
    ```

3. Enter the `SYNC_SECRET` value (set via environment variable on the backend)
4. Click **Sync**

The backend pulls the latest commits from the Git repository, reloads all Collector and Dashboard definitions, and returns a success or error message.

### Remember me

Check **Remember me** to save the `SYNC_SECRET` in your browser's local storage. On future visits, the field is pre-filled. The value is stored only in your browser and is never sent except as part of a sync request.

!!! warning "Shared machines"
    Avoid using "Remember me" on shared or public computers. Clear browser storage to remove the saved secret.

---

## Connection status

The **status dot** in the header shows the current backend connection state:

| Dot colour | Meaning |
|-----------|---------|
| 🟢 Green | Connected — data is live |
| 🔴 Red | Disconnected — data is frozen at last-known state |

### Disconnected banner

When the backend cannot be reached, a red banner appears at the top of the page:

```
⚠ Disconnected — data is frozen
```

Data from the last successful fetch remains visible. No data is cleared.

### Reconnecting banner

While Chart-Monitor is attempting to reconnect, a yellow banner appears:

```
↻ Reconnecting…
```

Once the backend responds, the banner disappears and data resumes refreshing automatically.

---

## Background Git sync (automatic)

The backend can be configured to automatically pull new commits from Git on a schedule (via environment variables or backend configuration). This is separate from the manual sync — it happens server-side with no user interaction required. Check your deployment configuration for details.
