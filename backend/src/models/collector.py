"""Base ``Collector`` class and the ``@secret`` annotation.

Users extend this class to define data sources. The ``collect`` method
must be implemented and may either return a list or use ``yield``.

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

import functools
import logging
import os
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
