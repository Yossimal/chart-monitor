"""Kubernetes Pods Collector.

Fetches all pods across all namespaces from the K8s API server using a
ServiceAccount token.  The token is injected via the ``@secret`` annotation
so it never needs to be hardcoded.

Required environment variable:
  K8S_TOKEN   – Bearer token for the chart-monitor ServiceAccount.
                Get it with:
                  $t = kubectl get secret chart-monitor-token -n default \\
                       -o jsonpath="{.data.token}"
                  [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($t))
                Then: set K8S_TOKEN=<that value>

Optional environment variable:
  K8S_API_SERVER  – K8s API URL (default: https://kubernetes.docker.internal:6443)
"""
from __future__ import annotations

import os
from typing import Any

from store.http_collector import HTTPCollector
from src.models.collector import secret


_API_SERVER = os.environ.get("K8S_API_SERVER", "https://kubernetes.docker.internal:6443")


class PodsCollector(HTTPCollector):
    """Collects all pods across all namespaces."""

    max_data: int = 200
    scrape_interval: int = 15

    def url(self) -> str:
        return f"{_API_SERVER}/api/v1/pods"

    @secret("K8S_TOKEN")
    def collect(self, secrets: dict[str, str] | None = None) -> list[dict[str, Any]]:
        import requests

        token = (secrets or {}).get("K8S_TOKEN", "")
        response = requests.get(
            self.url(),
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
            verify=False,   # docker-desktop uses a self-signed cert
        )
        response.raise_for_status()
        # K8s returns {"items": [...], "kind": "PodList", ...}
        items = response.json().get("items", [])
        return items
