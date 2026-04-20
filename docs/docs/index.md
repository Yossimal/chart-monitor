# Chart-Monitor

Chart-Monitor is a dynamic data extraction and visualization engine for monitoring dashboards. You write small Python scripts that pull data from any source — Kubernetes APIs, databases, REST endpoints, or anything else — and Chart-Monitor turns the output into live, filterable, sortable tables in your browser.

## Core Concepts

| Concept | What it does |
|---------|-------------|
| **Collector** | A Python class that fetches data from an external system and returns rows |
| **SQL Collector** | A Collector that joins or transforms data from other Collectors using SQL |
| **Dashboard** | A Python class that binds a Collector to a set of named, styled columns |
| **Secret** | An environment variable injected into a Collector at runtime via the `@secret` decorator |

## Quick Start

New here? Follow these steps:

1. [Connect your Git repository](getting-started/connect-git.md) — required before anything else works
2. [Understand Collectors and Dashboards](concepts/collectors.md) — the two building blocks
3. [Create your first Collector](how-to/create-collector.md) — write a Python data source
4. [Create your first Dashboard](how-to/create-dashboard.md) — bind the Collector to a table view

## All Sections

<div class="grid cards" markdown>

- :material-source-repository: **Getting Started**

    ---

    Connect Chart-Monitor to your Git repository so it can load your monitoring scripts.

    [Connect a Git Repository →](getting-started/connect-git.md)

- :material-book-open-outline: **Concepts**

    ---

    Understand the building blocks before you write any code.

    [Collectors](concepts/collectors.md) · [Dashboards](concepts/dashboards.md) · [Secrets](concepts/secrets.md)

- :material-hammer-wrench: **How-To Guides**

    ---

    Step-by-step walkthroughs for every task.

    [Create Collector](how-to/create-collector.md) · [SQL Collector](how-to/create-sql-collector.md) · [Secrets](how-to/load-secrets.md) · [Dashboard](how-to/create-dashboard.md)

- :material-monitor-dashboard: **Using the UI**

    ---

    Make the most of the Chart-Monitor interface.

    [Overview](ui/index.md) · [Filters & Sort](ui/column-filter-and-sort.md) · [SQL Filter](ui/sql-filter.md) · [Sync](ui/sync-and-refresh.md)

- :material-cog-outline: **How It Works**

    ---

    Architecture, data flow, and internals for power users.

    [Overview](internals/index.md) · [End-to-End Flow](internals/data-flow-end-to-end.md)

</div>
