# Collector Execution

This page explains what happens from the moment a Dashboard data request arrives until rows are returned.

---

## Pipeline overview

```
GET /api/v1/dashboards/{id}/data
        ↓
pipeline.run_dashboard(id)
        ↓
FileStore.get_collector_for(id)  →  Collector class
        ↓
FileStore.get_dashboards()[id]   →  Dashboard class
        ↓
dashboard.getCollector()         →  Collector instance
        ↓
executor.execute(collector)      →  RestrictedPython sandbox
        ↓
collector.safe_collect()         →  list[dict] rows
        ↓
dashboard.get_columns()          →  [(name, extractor), ...]
        ↓
[extractor(row) for row in rows] →  list[CellResult]
        ↓
JSON response
```

---

## RestrictedPython sandbox

Collector scripts run inside a [RestrictedPython](https://restrictedpython.readthedocs.io/) sandbox. This prevents scripts from performing unsafe operations while still allowing useful data collection.

### What is allowed

- Standard safe built-ins: `len`, `range`, `zip`, `enumerate`, `sorted`, `dict`, `list`, `str`, `int`, `float`, `bool`, `None`, `True`, `False`, `print`, `type`, etc.
- `import requests` — HTTP client for API calls
- `import json` — JSON encode/decode
- `import datetime` — date and time utilities
- `import re` — regular expressions
- `import math` — mathematical functions
- List/dict/set comprehensions and generator expressions
- `try`/`except`/`finally` blocks
- Class and function definitions

### What is blocked

- `import os` — no direct OS interaction
- `import subprocess` — no shell command execution
- `open()` for writing — no filesystem writes
- `import sys` — no interpreter access
- `exec()` and `eval()` — no dynamic code execution
- `import socket` — no raw socket access
- Direct `os.environ` access — use the `@secret` decorator instead

### Why these restrictions?

Chart-Monitor allows users to write arbitrary Python scripts. Without sandboxing, a script could read secrets from the environment, write files, spawn processes, or exfiltrate data. RestrictedPython provides a controlled execution environment where scripts can safely fetch data from external systems while the host remains protected.

---

## Row limit enforcement

After `collect()` returns (or yields) rows, `safe_collect()` enforces the `max_data` limit:

```python
for item in result:
    rows.append(item)
    if len(rows) >= self.max_data:
        break  # silently truncate
```

The truncation is logged at DEBUG level on the backend.

---

## Error handling

If `collect()` raises any exception:

1. The exception is logged with full traceback on the backend
2. The exception re-raises to `pipeline.run_dashboard()`
3. The API response includes `{"error": "...error message..."}` alongside empty `rows` and `columns`
4. The Dashboard in the UI shows the error message instead of a table
5. Other Dashboards and Collectors are unaffected

This means a broken Collector never crashes the backend — it only affects its own Dashboard.

---

## Dashboard column extraction

After rows are collected, the Dashboard's `@dashboardColumn` methods are called once per row per column:

```python
for row in rows:
    styled_row = {}
    for col_name, extractor in dashboard.get_columns():
        styled_row[col_name] = extractor(row)
    result_rows.append(styled_row)
```

Each extractor receives the raw dict row and returns a `CellResult` with `value`, optional `display`, and `style`.
