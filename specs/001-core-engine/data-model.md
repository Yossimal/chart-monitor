# Chart-Monitor Data Models

This document outlines the core entities and data structures for the Chart-Monitor Core Engine.

## Core Entities

### 1. `Collector` (Source Base Class)

The abstract Python class that users extend to define how to fetch data from an external system.

**Attributes / Annotations:**
- `@secret("secret_name")`: A class or method-level annotation that instructs the `VariableInjector` to resolve a secret from the Host Environment.
- `max_data` (int): A configuration parameter preventing infinite yields or limiting memory usage. Provides a default in the base Collector, but can be overridden by the Dashboard.
- `scrape_interval` (int): Frequency in seconds for the frontend to poll data. Defaults to an environment variable loaded by the root Collector, but can be overridden by the Dashboard.

**Methods:**
- `collect(self, **kwargs) -> Iterable[Dict[str, Any]]`: The primary method executed by the `CodeExecutor`. It must return a List or yield a generator of dictionaries representing the raw data rows.

### 2. `TableDashboard` (Dashboard Base Class)

The abstract Python class that users extend to process the data from a `Collector` into a format suitable for the UI.

**Attributes / Methods:**
- `getCollector(self) -> Collector`: A method that identifies the `Collector` to be executed and provides its configuration (like `max_data`).
- `@dashboardColumn("Column Name")`: An annotation applied to methods/properties. The method takes a raw data row and returns the processed cell value and its associated CSS styling.

## API Contracts

### `DashboardDataResponse` (JSON)

The structure returned by the FastAPI backend to the Vanilla frontend polling mechanism.

```json
{
  "dashboard_id": "string",
  "scrape_interval_seconds": 30,
  "columns": ["ID", "Status", "Metrics"],
  "rows": [
    {
      "ID": {"value": "pod-1", "style": "text-gray-900"},
      "Status": {"value": "Running", "style": "text-green-500 font-bold"},
      "Metrics": {"value": "95%", "style": "text-red-500"}
    }
  ],
  "error": null
}
```

### Error State (`DashboardDataResponse`)

If an exception occurs during the `collect()` phase.

```json
{
  "dashboard_id": "string",
  "scrape_interval_seconds": 60,
  "columns": [],
  "rows": [],
  "error": "Failed to connect to Kubernetes API: Timeout"
}
```
