# Load Secrets

Secrets let you pass credentials (tokens, passwords, API keys) to Collectors at runtime without storing them in your Git repository.

**Prerequisites**: [Understand Secrets](../concepts/secrets.md) · [Create a Collector](create-collector.md)

---

## Step 1: Define the secret on the server

Set the secret as an environment variable on the machine running Chart-Monitor:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

For production, use a `.env` file (gitignored), Docker secrets, Kubernetes Secrets, or a secrets manager. Never hardcode values.

---

## Step 2: Declare the secret in your Collector

Use the `@secret` decorator on the `collect()` method to declare which environment variable the Collector needs:

```python
from src.models.collector import Collector, secret

class GitHubIssuesCollector(Collector):

    @secret("GITHUB_TOKEN")
    def collect(self, secrets: dict) -> list[dict]:
        token = secrets["GITHUB_TOKEN"]

        import requests
        resp = requests.get(
            "https://api.github.com/repos/your-org/your-repo/issues",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()

        return [
            {"number": i["number"], "title": i["title"], "state": i["state"]}
            for i in resp.json()
        ]
```

### How the decorator works

1. When `collect()` is called, `@secret("GITHUB_TOKEN")` looks up `GITHUB_TOKEN` in the server's environment
2. It injects the value into the `secrets` dict passed to `collect()`
3. If the variable is not set, a `KeyError` is raised immediately

---

## Multiple secrets

Stack decorators to require more than one secret:

```python
class DatabaseCollector(Collector):

    @secret("DB_HOST")
    @secret("DB_PASSWORD")
    def collect(self, secrets: dict) -> list[dict]:
        host = secrets["DB_HOST"]
        password = secrets["DB_PASSWORD"]
        # connect to database ...
```

---

## Complete example

```python
import requests
from src.models.collector import Collector, secret

class JiraCollector(Collector):
    scrape_interval = 60

    @secret("JIRA_BASE_URL")
    @secret("JIRA_TOKEN")
    def collect(self, secrets: dict) -> list[dict]:
        base_url = secrets["JIRA_BASE_URL"]
        token = secrets["JIRA_TOKEN"]

        resp = requests.get(
            f"{base_url}/rest/api/3/search?jql=project=OPS",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        issues = resp.json().get("issues", [])

        return [
            {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "status": issue["fields"]["status"]["name"],
                "priority": issue["fields"]["priority"]["name"],
            }
            for issue in issues
        ]
```

---

## What happens when a secret is missing

If `JIRA_TOKEN` is not set:

1. The `@secret` decorator raises a `KeyError` with a clear message:
   ```
   Secret 'JIRA_TOKEN' not found in environment.
   Set the environment variable 'JIRA_TOKEN' to proceed.
   ```
2. The error is logged on the backend
3. The Dashboard shows an error state instead of data
4. Other Dashboards and Collectors continue running normally

---

## Security guarantees

!!! success "Your secrets are protected"
    - Secret values are **never written to files** by Chart-Monitor
    - Secret values are **never included in API responses** or Dashboard output
    - Secret values are **never logged** (only the variable name appears in error messages)
    - Collector scripts run in a RestrictedPython sandbox that blocks `import os` and direct `os.environ` access — scripts can only access secrets declared via `@secret`
