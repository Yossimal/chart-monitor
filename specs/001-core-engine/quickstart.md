# Chart-Monitor Quickstart

Welcome to Chart-Monitor! This guide shows you how to define a data source (`Collector`) and a presentation layer (`TableDashboard`).

## 1. Create a Collector

A `Collector` fetches raw data. It runs in a secure sandbox (`RestrictedPython`).

Create `github_prs.py` in your GitOps store:

```python
from chart_monitor.models import Collector, secret
import requests

class GitHubPRCollector(Collector):
    
    # Resolves from Host Environment as GITHUB_TOKEN
    @secret("GITHUB_TOKEN")
    def collect(self, secrets):
        headers = {"Authorization": f"Bearer {secrets['GITHUB_TOKEN']}"}
        response = requests.get("https://api.github.com/repos/my-org/my-repo/pulls", headers=headers)
        response.raise_for_status()
        
        # You can return a list...
        return response.json()
        
        # ...OR yield items individually (up to max_data)
        # for pr in response.json():
        #     yield pr
```

## 2. Create a Dashboard

A `TableDashboard` transforms that raw data into stylized columns.

Create `github_dashboard.py` in your GitOps store:

```python
from chart_monitor.models import TableDashboard, dashboardColumn
from .github_prs import GitHubPRCollector

class PRDashboard(TableDashboard):
    
    def getCollector(self):
        # Configure and attach the collector
        collector = GitHubPRCollector()
        # Optionally override the collector's default limits
        collector.max_data = 100
        collector.scrape_interval = 60
        return collector
        
    @dashboardColumn("PR Title")
    def extract_title(self, row):
        return {"value": row.get("title", "Unknown"), "style": "font-weight: bold; color: #111827;"}
        
    @dashboardColumn("Author")
    def extract_author(self, row):
        return {"value": row["user"]["login"], "style": "color: #3b82f6;"}
        
    @dashboardColumn("State")
    def extract_state(self, row):
        state = row.get("state", "closed")
        style = "color: #10b981;" if state == "open" else "color: #ef4444;"
        return {"value": state.upper(), "style": style}
```

## 3. View the Result

1. Add both files to your configured GitOps directory.
2. The Chart-Monitor backend will automatically poll and load them.
3. Open the frontend UI, select "PRDashboard", and watch the data stream in!
