"""Base ``Collector`` class, the ``@secret`` annotation, and ``SQLCollector``.

Users extend ``Collector`` to define data sources. The ``collect`` method
must be implemented and may either return a list or use ``yield``.

Users extend ``SQLCollector`` to define data sources that join or transform
data from other collectors using SQL. Implement ``init_tables()`` to register
source collectors and define views, then implement ``sql()`` to return the
SELECT query to run.

Environment-variable resolution
--------------------------------
Secrets are resolved via ``os.environ`` at call time.  The root
``Collector`` reads ``CHART_MONITOR_SCRAPE_INTERVAL`` and
``CHART_MONITOR_MAX_DATA`` as defaults so operators can configure
global limits without touching every collector file.

The defaults can be overridden per-dashboard by setting
``collector.scrape_interval`` / ``collector.max_data`` in
``TableDashboard.getCollector()``.
"""
from __future__ import annotations

import dataclasses
import functools
import json
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ── Module-level environment-driven defaults ──────────────────────────────────
_DEFAULT_MAX_DATA: int = int(os.environ.get("CHART_MONITOR_MAX_DATA", "500"))
_DEFAULT_SCRAPE_INTERVAL: int = int(
    os.environ.get("CHART_MONITOR_SCRAPE_INTERVAL", "30")
)


# ─────────────────────────────────────────────────────────────────────────────
# @secret decorator
# ─────────────────────────────────────────────────────────────────────────────

def secret(secret_name: str) -> Callable:
    """Annotation that injects a named environment variable into ``collect``.

    Usage::

        class MyCollector(Collector):
            @secret("MY_API_TOKEN")
            def collect(self, secrets: dict[str, str]) -> list[dict]:
                token = secrets["MY_API_TOKEN"]
                ...

    If the environment variable is not set, a ``KeyError`` is raised which
    propagates up to the ``CodeExecutor`` error handler (logged, no crash).
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self: "Collector", *args: Any, **kwargs: Any) -> Any:
            value = os.environ.get(secret_name)
            if value is None:
                raise KeyError(
                    f"Secret '{secret_name}' not found in environment. "
                    f"Set the environment variable '{secret_name}' to proceed."
                )
            resolved: dict[str, str] = {secret_name: value}
            # Merge with any already-resolved secrets passed as kwargs
            if "secrets" in kwargs:
                kwargs["secrets"].update(resolved)
            else:
                kwargs["secrets"] = resolved
            return fn(self, *args, **kwargs)
        # Tag the wrapper so VariableInjector can pre-validate required secrets
        wrapper._requires_secrets = getattr(fn, "_requires_secrets", []) + [secret_name]  # type: ignore[attr-defined]
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Collector base class
# ─────────────────────────────────────────────────────────────────────────────

class Collector(ABC):
    """Abstract base class for all Chart-Monitor data sources.

    Attributes
    ----------
    max_data:
        Maximum number of rows to collect.  Defaults to the value of the
        ``CHART_MONITOR_MAX_DATA`` environment variable (default: 500).
    scrape_interval:
        How many seconds the frontend waits between polls.  Defaults to the
        value of ``CHART_MONITOR_SCRAPE_INTERVAL`` (default: 30).
    """

    max_data: int = _DEFAULT_MAX_DATA
    scrape_interval: int = _DEFAULT_SCRAPE_INTERVAL

    @abstractmethod
    def collect(self, **kwargs: Any) -> Iterable[dict[str, Any]]:
        """Fetch data from the external system.

        Returns or yields an iterable of plain-dict rows.
        """

    def safe_collect(self) -> list[dict[str, Any]]:
        """Execute ``collect`` with ``max_data`` enforcement.

        Supports both list-returning and generator-yielding implementations.
        """
        rows: list[dict[str, Any]] = []
        try:
            result = self.collect()
            for item in result:
                rows.append(item)
                if len(rows) >= self.max_data:
                    logger.debug(
                        "%s: max_data=%d reached, truncating.",
                        self.__class__.__name__, self.max_data,
                    )
                    break
        except Exception as exc:
            logger.error(
                "Collector %s raised an error: %s",
                self.__class__.__name__, exc, exc_info=True,
            )
            raise
        return rows


# ─────────────────────────────────────────────────────────────────────────────
# SQLCollector internal dataclasses  (T003)
# ─────────────────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class _ViewColumnDef:
    """A single column mapping within a view."""
    column_name: str
    path: str
    json_path: str  # computed: '$.' + path


@dataclasses.dataclass
class _ViewDef:
    """Metadata for a registered logical view."""
    view_name: str
    table_name: str
    columns: list[_ViewColumnDef] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class _TableDef:
    """Metadata for a registered logical table."""
    table_name: str
    collector: type[Collector] | Collector
    secrets: dict[str, str] | None = None


# ─────────────────────────────────────────────────────────────────────────────
# SQLCollector base class  (T004 skeleton → T005-T009 full implementation)
# ─────────────────────────────────────────────────────────────────────────────

class SQLCollector(Collector):
    """Abstract ``Collector`` that joins data from other collectors via SQL.

    Subclass and implement two abstract methods:

    * ``init_tables()`` — call ``define_table``, ``define_view``, and
      ``view_column`` to register sources and column mappings.
    * ``sql()`` — return the SELECT query to execute.

    The ``collect()`` pipeline runs on every scrape:

    1. Call ``init_tables()`` (once, guarded by ``_initialized``).
    2. For each registered table, fetch rows from its source collector.
    3. Create an in-memory SQLite database.
    4. Populate raw tables (one JSON text column per table).
    5. Create views that extract JSON fields into named SQL columns.
    6. Execute ``sql()`` and return results as ``list[dict]``.

    Example::

        class PodsByRegion(SQLCollector):
            def init_tables(self):
                self.define_table(PodsCollector, "pods")
                self.define_table(NodesCollector, "nodes")

                self.define_view("pods_view", "pods")
                self.view_column("pods_view", "pod_name", "metadata.name")
                self.view_column("pods_view", "node", "spec.nodeName")

                self.define_view("nodes_view", "nodes")
                self.view_column("nodes_view", "node", "metadata.name")
                self.view_column("nodes_view", "region", "metadata.labels.region")

            def sql(self):
                return '''
                    SELECT p.pod_name, n.region
                    FROM pods_view p
                    JOIN nodes_view n ON p.node = n.node
                '''
    """

    def __init__(self) -> None:
        self._tables: dict[str, _TableDef] = {}
        self._views: dict[str, _ViewDef] = {}
        self._initialized: bool = False

    # ── Registration methods (called from init_tables) ────────────────────────

    def define_table(
        self,
        collector: type[Collector] | Collector,
        table_name: str,
        secrets: dict[str, str] | None = None,
    ) -> None:
        """Register a logical table backed by *collector*'s data.

        Parameters
        ----------
        collector:
            A ``Collector`` subclass (will be instantiated) or instance.
        table_name:
            SQL-safe name for the table (alphanumeric + underscore).
        secrets:
            Optional dict of secrets passed to the source collector's
            ``collect()`` call as the ``secrets`` keyword argument.
        """
        if table_name in self._tables:
            raise ValueError(
                f"Table '{table_name}' is already defined. "
                "Each table name must be unique."
            )
        self._tables[table_name] = _TableDef(
            table_name=table_name,
            collector=collector,
            secrets=secrets,
        )

    def define_view(self, view_name: str, table_name: str) -> None:
        """Create a logical view projected over *table_name*.

        Parameters
        ----------
        view_name:
            Name of the SQL view users will query.
        table_name:
            Must reference a table already registered via ``define_table``.
        """
        if view_name in self._views:
            raise ValueError(
                f"View '{view_name}' is already defined. "
                "Each view name must be unique."
            )
        if table_name not in self._tables:
            raise ValueError(
                f"Table '{table_name}' not found. "
                f"Call define_table('{table_name}', ...) before define_view."
            )
        self._views[view_name] = _ViewDef(
            view_name=view_name,
            table_name=table_name,
        )

    def view_column(self, view_name: str, column_name: str, path: str) -> None:
        """Add a column mapping to an existing view.

        Parameters
        ----------
        view_name:
            Must reference a view already registered via ``define_view``.
        column_name:
            The SQL column alias users will reference in queries.
        path:
            Dot-notation JSON path into the source dict rows
            (e.g. ``"metadata.name"``).  Translated to SQLite JSON path
            ``$.metadata.name`` internally.
        """
        if view_name not in self._views:
            raise ValueError(
                f"View '{view_name}' not found. "
                f"Call define_view('{view_name}', ...) before view_column."
            )
        self._views[view_name].columns.append(
            _ViewColumnDef(
                column_name=column_name,
                path=path,
                json_path=f"$.{path}",
            )
        )

    # ── Abstract methods (user implements) ────────────────────────────────────

    @abstractmethod
    def init_tables(self) -> None:
        """Register tables, views, and column mappings.

        Call ``define_table``, ``define_view``, and ``view_column`` here.
        This method is invoked exactly once before the first ``collect()``.
        """

    @abstractmethod
    def sql(self) -> str:
        """Return the SQL query to execute against the registered tables/views.

        Must be a SELECT or WITH statement (read-only).
        """

    # ── collect() pipeline ────────────────────────────────────────────────────

    def collect(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Execute the full SQL pipeline and return results as a list of dicts.

        Pipeline:
        1. init_tables() [once]
        2. Validate sql() is read-only
        3. Collect rows from each source collector
        4. Build in-memory SQLite DB (raw tables + views)
        5. Execute sql() query
        6. Return list[dict] results
        """
        # Step 1: initialise tables once
        if not self._initialized:
            self.init_tables()
            self._initialized = True

        if not self._tables:
            raise ValueError(
                f"{self.__class__.__name__}: No tables defined. "
                "Call define_table() inside init_tables()."
            )

        # Step 2: validate sql() is read-only
        query = self.sql().strip()
        _upper = query.upper()
        if not (_upper.startswith("SELECT") or _upper.startswith("WITH")):
            raise ValueError(
                f"{self.__class__.__name__}: sql() must return a SELECT or "
                f"WITH statement. Got: {query[:80]!r}"
            )

        # Step 3: collect rows from each source collector
        source_data: dict[str, list[dict[str, Any]]] = {}
        for table_name, table_def in self._tables.items():
            src = table_def.collector
            instance: Collector = src() if isinstance(src, type) else src
            try:
                # Gather secrets required by this collector using the _requires_secrets
                # metadata set by the @secret decorator — no hardcoded names.
                needed: list[str] = getattr(instance.collect, "_requires_secrets", [])
                env_secrets: dict[str, str] = {
                    name: os.environ[name]
                    for name in needed
                    if name in os.environ
                }
                # Explicit secrets from define_table() take priority over env-resolved ones
                merged: dict[str, str] = {**env_secrets, **(table_def.secrets or {})}
                rows = list(instance.collect(
                    **({"secrets": merged} if merged else {})
                ))
            except Exception as exc:
                raise RuntimeError(
                    f"{self.__class__.__name__}: Failed to collect data for "
                    f"table '{table_name}': {exc}"
                ) from exc
            source_data[table_name] = rows

        # Step 4: build in-memory SQLite DB
        conn = sqlite3.connect(":memory:")
        try:
            # Create raw tables and insert JSON rows
            for table_name, rows in source_data.items():
                raw = f"raw_{table_name}"
                conn.execute(f"CREATE TABLE {raw} (json_text TEXT)")
                conn.executemany(
                    f"INSERT INTO {raw} VALUES (?)",
                    [(json.dumps(row),) for row in rows],
                )

            # Create views with JSON path extractions
            for view_def in self._views.values():
                raw = f"raw_{view_def.table_name}"
                if view_def.columns:
                    col_exprs = ", ".join(
                        f"json_text->>'{c.json_path}' AS {c.column_name}"
                        for c in view_def.columns
                    )
                else:
                    col_exprs = "json_text"
                conn.execute(
                    f"CREATE VIEW {view_def.view_name} AS "
                    f"SELECT {col_exprs} FROM {raw}"
                )

            # Step 5: execute user query
            try:
                cursor = conn.execute(query)
            except sqlite3.Error as exc:
                raise RuntimeError(
                    f"{self.__class__.__name__}: SQL execution failed: {exc}\n"
                    f"Query: {query}"
                ) from exc

            columns = [desc[0] for desc in cursor.description or []]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        finally:
            conn.close()
