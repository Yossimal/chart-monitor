"""Abstract base class for the Chart-Monitor Store interface.

Any concrete Store must be able to discover, load, and expose Collector
and TableDashboard definitions from its backing source (file system, k8s
ConfigMap, database, etc.).
"""
from __future__ import annotations

import importlib.util
import inspect
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from types import ModuleType
from typing import Any

logger = logging.getLogger(__name__)


class Store(ABC):
    """Abstract store for loading Collector and Dashboard definitions."""

    @abstractmethod
    def reload(self) -> None:
        """Re-scan the backing source and refresh in-memory definitions."""

    @abstractmethod
    def get_dashboards(self) -> dict[str, Any]:
        """Return a mapping of dashboard_id -> TableDashboard class."""

    @abstractmethod
    def get_collector_for(self, dashboard_id: str) -> Any | None:
        """Return the Collector class bound to the given dashboard, or None."""


# ──────────────────────────────────────────────────────────────────────────────
# FileStore  –  loads .py files from a user-configured directory
# ──────────────────────────────────────────────────────────────────────────────

class FileStore(Store):
    """Loads Collector and TableDashboard subclasses from a directory of .py files.

    The store scans ``store_dir`` recursively, imports every ``.py`` file it
    finds (ignoring Python protected names like ``__init__.py``), and registers
    any class that inherits from ``Collector`` or ``TableDashboard``.

    Malformed files (syntax errors, import failures) are logged as warnings
    and silently skipped so valid definitions continue to be served.
    """

    def __init__(self, store_dir: str | Path) -> None:
        self._store_dir = Path(store_dir).resolve()
        self._dashboards: dict[str, Any] = {}   # dashboard_id -> Dashboard class
        self._collectors: dict[str, Any] = {}   # class name  -> Collector class
        
        # Inject the parent dir into sys.path so dashboard scripts
        # can import each other via `from store.collector import X`
        import sys
        parent_dir = str(self._store_dir.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            
        self.reload()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_python_files(self) -> list[Path]:
        if not self._store_dir.exists():
            logger.warning("Store directory %s does not exist.", self._store_dir)
            return []
        return [
            p for p in self._store_dir.rglob("*.py")
            if p.name != "__init__.py"
        ]

    def _load_module(self, path: Path) -> ModuleType | None:
        """Dynamically import a .py file and return the module, or None on error."""
        module_name = f"chart_monitor_store.{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot create spec for {path}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
        except Exception as exc:
            logger.warning(
                "Skipping malformed configuration file %s: %s", path, exc,
                exc_info=True,
            )
            return None

    def _register_classes(self, mod: ModuleType) -> None:
        """Inspect a module and register Collector / TableDashboard subclasses."""
        # Import lazily to avoid circular imports at module level
        from src.models.collector import Collector
        from src.models.dashboard import TableDashboard

        for _name, obj in inspect.getmembers(mod, inspect.isclass):
            if obj.__module__ != mod.__name__:
                # Skip re-exported base classes
                continue
            if issubclass(obj, TableDashboard) and obj is not TableDashboard:
                dashboard_id = _name
                self._dashboards[dashboard_id] = obj
                logger.info("Registered dashboard: %s", dashboard_id)
            elif issubclass(obj, Collector) and obj is not Collector:
                self._collectors[obj.__name__] = obj
                logger.info("Registered collector: %s", obj.__name__)

    # ------------------------------------------------------------------
    # Store interface
    # ------------------------------------------------------------------

    def reload(self) -> None:
        """Re-scan the store directory and rebuild all definitions."""
        self._dashboards.clear()
        self._collectors.clear()
        for path in self._iter_python_files():
            mod = self._load_module(path)
            if mod is not None:
                self._register_classes(mod)
        logger.info(
            "FileStore reloaded: %d dashboard(s), %d collector(s)",
            len(self._dashboards), len(self._collectors),
        )

    def get_dashboards(self) -> dict[str, Any]:
        return dict(self._dashboards)

    def get_collector_for(self, dashboard_id: str) -> Any | None:
        dashboard_cls = self._dashboards.get(dashboard_id)
        if dashboard_cls is None:
            return None
        # Instantiate dashboard; call getCollector() to get the bound collector
        try:
            dashboard = dashboard_cls()
            return dashboard.getCollector()
        except Exception as exc:
            logger.error(
                "Failed to instantiate collector for dashboard %s: %s",
                dashboard_id, exc, exc_info=True,
            )
            return None


# ──────────────────────────────────────────────────────────────────────────────
# Module-level singleton used throughout the app
# ──────────────────────────────────────────────────────────────────────────────

_STORE_DIR_ENV = os.environ.get("CHART_MONITOR_STORE_DIR")
if _STORE_DIR_ENV:
    _STORE_DIR = _STORE_DIR_ENV
else:
    # Default: <project_root>/store  (resolved relative to this file's location)
    # backend/src/storage/store.py → ../../../store
    _STORE_DIR = str(Path(__file__).resolve().parent.parent.parent.parent / "store")

store: FileStore = FileStore(_STORE_DIR)

