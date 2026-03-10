"""VariableInjector – pre-validates that all secrets required by a Collector
are present in the host environment before execution begins.

This is a pre-flight check that surfaces missing secrets early, before
any code runs, so the error message is clear and actionable.
"""
from __future__ import annotations

import inspect
import logging
import os
from typing import Any

from src.models.collector import Collector

logger = logging.getLogger(__name__)


class VariableInjector:
    """Validates and resolves environment-variable secrets for a Collector.

    Call :meth:`validate` before running ``safe_collect`` to get a clear
    error when a required secret is missing rather than a cryptic failure
    mid-execution.
    """

    def validate(self, collector: Collector) -> dict[str, str]:
        """Return a dict of {secret_name: value} for all @secret annotations.

        Raises
        ------
        KeyError
            If any required secret is missing from the environment.
        """
        required: list[str] = []

        # Walk the MRO and collect all _requires_secrets tags from @secret
        for _name, method in inspect.getmembers(collector, predicate=inspect.ismethod):
            required.extend(getattr(method, "_requires_secrets", []))

        resolved: dict[str, str] = {}
        missing: list[str] = []
        for name in set(required):
            value = os.environ.get(name)
            if value is None:
                missing.append(name)
            else:
                resolved[name] = value

        if missing:
            raise KeyError(
                f"Required secret(s) not found in environment: {missing!r}. "
                "Set the corresponding environment variable(s) before starting."
            )

        logger.debug("VariableInjector: resolved secrets %s", list(resolved.keys()))
        return resolved
