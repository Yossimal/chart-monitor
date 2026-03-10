"""
Chart-Monitor Quickstart – GitHub Pull Requests Example
=======================================================
Drop this file (and github_dashboard.py) into the directory pointed to
by CHART_MONITOR_STORE_DIR (default: ./store/) and restart the server.

Set GITHUB_TOKEN in your environment before starting:
  export GITHUB_TOKEN=ghp_xxxx
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from src.models.collector import Collector, secret


class GitHubPRCollector(Collector):
    """Fetches open Pull Requests from a GitHub repository.

    Environment variables required:
      GITHUB_TOKEN     – A personal access token with repo:read scope.

    Collector-level defaults (overridable by the Dashboard):
      max_data         – Controlled by CHART_MONITOR_MAX_DATA (default 500)
      scrape_interval  – Controlled by CHART_MONITOR_SCRAPE_INTERVAL (default 30s)
    """

    # Override defaults for this specific collector
    max_data: int = 50
    scrape_interval: int = 60

    ORG = "my-org"
    REPO = "my-repo"

    @secret("GITHUB_TOKEN")
    def collect(self, secrets: dict[str, str] | None = None) -> Iterable[dict[str, Any]]:
        import urllib.request
        import json

        token = (secrets or {}).get("GITHUB_TOKEN", "")
        url = f"https://api.github.com/repos/{self.ORG}/{self.REPO}/pulls?state=open&per_page=100"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
