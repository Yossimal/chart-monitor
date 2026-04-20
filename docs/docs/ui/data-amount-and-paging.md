# Data Amount & Paging

This page explains how Chart-Monitor handles large result sets and what controls are available for managing row counts.

---

## Row limits

Each Collector has a `max_data` attribute that caps the number of rows returned per scrape. The default is **500 rows**, configurable via the `CHART_MONITOR_MAX_DATA` environment variable.

A Dashboard author can override this per-Collector:

```python
def getCollector(self) -> Collector:
    c = MyCollector()
    c.max_data = 1000
    return c
```

When the row cap is reached, Chart-Monitor silently truncates the result and logs a debug message on the backend. The UI displays the truncated rows without a warning.

---

## Row count display

The table toolbar shows the number of rows currently displayed:

```
Showing 47 of 500 rows          [SQL filter ×]  [Clear all filters]
```

- **"Showing N of M"** — N is the number of rows after filters, M is the total rows from the Collector
- When no filter is active, only M is shown: `500 rows`

---

## Scroll behaviour

All rows are rendered to the DOM and the table is scrollable. There is no pagination — all rows are visible by scrolling.

For very large datasets (500+ rows), vertical scrolling within the browser window handles navigation. The column headers remain fixed at the top while you scroll.

---

## Performance recommendations

If your Dashboard shows thousands of rows and feels slow:

1. **Filter at the source** — reduce `max_data` or add a `WHERE` clause in your Collector's data fetch
2. **Use a SQL Collector** — aggregate or filter rows at collect time before they reach the UI
3. **Use column filters or SQL filter** — the browser renders only the filtered subset for interaction purposes, though all rows are loaded into memory

---

## Future: virtual scrolling

For very large datasets (10k+ rows), virtual scrolling support may be added in a future release. Currently, all rows are rendered to the DOM.
