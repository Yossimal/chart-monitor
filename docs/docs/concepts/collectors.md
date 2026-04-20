# Collectors

A **Collector** is a Python class that fetches data from an external system and returns it as a list of rows. Each row is a plain Python dictionary.

Collectors are the **data source** layer of Chart-Monitor. Everything a Dashboard displays comes from a Collector.

---

## Standard Collector

A standard Collector extends the `Collector` base class and implements one method: `collect()`.

```python
from src.models.collector import Collector

class PodCollector(Collector):
    def collect(self):
        # Fetch data from any source
        return [
            {"name": "web-pod-1", "status": "Running", "node": "node-a"},
            {"name": "web-pod-2", "status": "Pending", "node": "node-b"},
        ]
```

The `collect()` method can:

- Return a list of dicts
- Use `yield` to produce rows lazily (generator style)
- Call external APIs, databases, files, or any Python-accessible source

### Row limits

Each Collector has a `max_data` class attribute that caps the number of rows returned. The default comes from the `CHART_MONITOR_MAX_DATA` environment variable (default: **500 rows**).

```python
class BigCollector(Collector):
    max_data = 1000  # override for this specific collector
```

### Scrape interval

`scrape_interval` controls how many seconds the browser waits between polls. The default comes from `CHART_MONITOR_SCRAPE_INTERVAL` (default: **30 seconds**).

```python
class FastCollector(Collector):
    scrape_interval = 10  # poll every 10 seconds
```

---

## SQL Collector

A **SQL Collector** extends `SQLCollector` and joins or transforms data from other Collectors using SQL instead of writing Python logic.

See [Concepts: SQL Collector](../how-to/create-sql-collector.md) and the [SQL Collector how-to guide](../how-to/create-sql-collector.md) for details.

---

## Where Collectors live

Collectors are `.py` files stored in your connected Git repository. Chart-Monitor scans the entire repository directory recursively and registers any class that inherits from `Collector`.

```
your-repo/
├── pods.py          # defines PodCollector
├── nodes.py         # defines NodeCollector
└── pod_by_node.py   # defines PodByNodeCollector (SQLCollector)
```

!!! tip "One file per Collector"
    Although multiple classes in one file work, one Collector per file keeps things readable and makes Git diffs cleaner.

---

## Relationship to Dashboards

A Collector produces raw rows. A [Dashboard](dashboards.md) binds a Collector to a named set of styled columns and controls what the user sees in the UI.

```
Collector.collect() → list[dict]
                           ↓
                    Dashboard.columns → styled table rows
```

One Collector can be used by multiple Dashboards. One Dashboard uses exactly one Collector (or a SQL Collector that references multiple upstream Collectors).
