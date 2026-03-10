"""Background auto-polling task that periodically reloads the FileStore.

The Store directory is re-scanned every ``CHART_MONITOR_POLL_INTERVAL``
seconds (default 30). This ensures new / updated Collector and Dashboard
definitions become available without restarting the server.
"""
from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)

_POLL_INTERVAL: int = int(os.environ.get("CHART_MONITOR_POLL_INTERVAL", "30"))
_task: asyncio.Task[None] | None = None


async def _polling_loop() -> None:
    """Infinite loop that reloads the store at a fixed interval."""
    from src.storage.store import store

    while True:
        await asyncio.sleep(_POLL_INTERVAL)
        try:
            logger.info("Poller: reloading store …")
            store.reload()
        except Exception as exc:
            logger.error("Poller: store reload failed: %s", exc, exc_info=True)


async def start_poller() -> None:
    """Launch the background polling task (idempotent)."""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_polling_loop(), name="store-poller")
        logger.info("Store poller started (interval=%ds).", _POLL_INTERVAL)


async def stop_poller() -> None:
    """Cancel the background polling task gracefully."""
    global _task
    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        logger.info("Store poller stopped.")
    _task = None
