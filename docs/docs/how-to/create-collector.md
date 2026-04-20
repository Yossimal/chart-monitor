# Create a Collector

A Collector is a Python class that fetches data and returns rows. This guide walks you through creating one from scratch.

**Prerequisites**: [Connect your Git repository](../getting-started/connect-git.md) · [Understand Collectors](../concepts/collectors.md)

---

## 1. Create the file

In your connected Git repository, create a new `.py` file. The filename becomes part of the Collector's identity, so use something descriptive:

```
your-repo/
└── pods.py
```

---

## 2. Implement the Collector class

```python
from src.models.collector import Collector

class PodCollector(Collector):
    max_data = 200          # optional: override the row cap (default: 500)
    scrape_interval = 30    # optional: seconds between browser polls (default: 30)

    def collect(self):
        # Replace this with your real data source
        return [
            {"name": "web-pod-1", "status": "Running", "restarts": 0},
            {"name": "web-pod-2", "status": "CrashLoopBackOff", "restarts": 14},
        ]
```

### Class attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_data` | `int` | `500` (env: `CHART_MONITOR_MAX_DATA`) | Maximum rows returned |
| `scrape_interval` | `int` | `30` (env: `CHART_MONITOR_SCRAPE_INTERVAL`) | Seconds between browser polls |

---

## 3. The `collect()` method

`collect()` is the only method you must implement. It can:

**Return a list:**
```python
def collect(self):
    return [{"key": "value"}, {"key": "value2"}]
```

**Yield rows (generator):**
```python
def collect(self):
    for item in some_large_source():
        yield {"key": item.key, "value": item.value}
```

### Return shape

Every row must be a Python `dict`. Keys are column names; values can be strings, numbers, booleans, or `None`.

```python
# Good
{"name": "pod-1", "status": "Running", "restarts": 0}

# Bad — you can use nested dicst but not classes inside the dicts
{"metadata": Socket}
```

---

## 4. Calling external APIs

You can call any accessible service from `collect()`. For example, using the `requests` library (available in the sandbox):

```python
import requests
from src.models.collector import Collector

class WeatherCollector(Collector):
    def collect(self):
        resp = requests.get("https://api.example.com/weather", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return [{"city": item["city"], "temp": item["temp_c"]} for item in data]
```

---

## 5. RestrictedPython sandbox constraints

Collector scripts run inside a **RestrictedPython** sandbox. The following are available:

**Allowed:**
- Standard Python built-ins: `len`, `range`, `zip`, `enumerate`, `sorted`, `dict`, `list`, `str`, `int`, `float`, `bool`, `None`, `True`, `False`, etc.
- `import requests` — HTTP client
- `import json` — JSON encode/decode
- `import datetime` — date/time utilities
- `import re` — regular expressions
- `import math` — math functions
- List comprehensions, dict comprehensions, generator expressions
- `try`/`except` blocks

**Blocked:**
- `import os` — no direct OS access
- `import subprocess` — no shell execution
- `open()` for writing — no filesystem writes
- `import sys` — no interpreter access
- `exec()`, `eval()` — no dynamic code execution
- Direct `os.environ` access — use [`@secret`](../concepts/secrets.md) instead

!!! warning "Import errors"
    If your script tries to import a blocked module, the Collector will fail with an `ImportError`. Use the allowed alternatives or fetch data via HTTP.

---

## 6. Commit and sync

Once your file is committed to the Git repository:

1. In the Chart-Monitor UI, click **↕ Sync Scripts** in the sidebar
2. Enter your `SYNC_SECRET` and click **Sync**
3. The new Collector is available immediately — create a [Dashboard](create-dashboard.md) to display it

---

## Common errors

??? failure "TypeError: collect() returned non-iterable"
    Your `collect()` method returned something other than a list or generator. Check the return statement.

??? failure "collect() rows must be dicts, got <class 'str'>"
    Each item in the returned list must be a dict. Wrap string/number values: `{"value": my_string}`.

??? failure "max_data reached — truncating"
    More rows were collected than `max_data` allows. Raise `max_data` on the class or filter at the source.
