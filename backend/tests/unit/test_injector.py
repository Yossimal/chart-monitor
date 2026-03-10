"""Unit tests: VariableInjector / @secret annotation (TDD – write first)."""
from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any

import pytest

from src.models.collector import Collector, secret


# ── Helper collectors ─────────────────────────────────────────────────────────

class SingleSecretCollector(Collector):
    @secret("MY_TOKEN")
    def collect(self, secrets: dict[str, str] | None = None) -> Iterable[dict[str, Any]]:
        return [{"token": (secrets or {}).get("MY_TOKEN", "")}]


class NoSecretCollector(Collector):
    def collect(self) -> Iterable[dict[str, Any]]:
        return [{"value": 42}]


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSecretInjection:
    def test_secret_injected_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_TOKEN", "super-secret")
        c = SingleSecretCollector()
        results = list(c.safe_collect())
        assert results == [{"token": "super-secret"}]

    def test_missing_secret_raises_key_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MY_TOKEN", raising=False)
        c = SingleSecretCollector()
        with pytest.raises(KeyError, match="MY_TOKEN"):
            c.safe_collect()

    def test_no_secret_collector_works(self) -> None:
        c = NoSecretCollector()
        results = list(c.safe_collect())
        assert results == [{"value": 42}]


class TestMaxData:
    def test_list_truncated_to_max_data(self) -> None:
        class BigCollector(Collector):
            def collect(self) -> Iterable[dict[str, Any]]:
                return [{"i": i} for i in range(1000)]

        c = BigCollector()
        c.max_data = 5
        results = c.safe_collect()
        assert len(results) == 5

    def test_generator_truncated_to_max_data(self) -> None:
        class InfiniteCollector(Collector):
            def collect(self) -> Iterable[dict[str, Any]]:
                i = 0
                while True:
                    yield {"i": i}
                    i += 1

        c = InfiniteCollector()
        c.max_data = 10
        results = c.safe_collect()
        assert len(results) == 10

    def test_default_max_data_comes_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Must import after patching because env defaults are read at import time
        monkeypatch.setenv("CHART_MONITOR_MAX_DATA", "7")
        import importlib
        import src.models.collector as mod
        importlib.reload(mod)
        assert mod._DEFAULT_MAX_DATA == 7
        # Cleanup: reload without the patched env so other tests aren't affected
        monkeypatch.delenv("CHART_MONITOR_MAX_DATA", raising=False)
        importlib.reload(mod)
