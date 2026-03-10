"""Generic HTTP Collector base class.

Subclasses must implement ``url()`` and optionally override ``headers()``
for auth. The response body is expected to be JSON (list or object).
If the response is a single object it is automatically wrapped in a list
so the downstream FieldExtractor always receives a uniform row iterable.
"""
from __future__ import annotations

from typing import Any
import requests

from src.models.collector import Collector


class HTTPCollector(Collector):
    """Base collector that performs an authenticated GET request against a JSON API."""

    def url(self) -> str:
        raise NotImplementedError("url() must be implemented by the subclass")

    def headers(self) -> dict[str, str]:
        """Override to supply custom headers (e.g. Authorization)."""
        return {}

    def collect(self) -> list[dict[str, Any]]:
        response = requests.get(self.url(), headers=self.headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        # Normalise: always return a list of dicts
        if isinstance(data, list):
            return data
        return [data]
