# Secrets

A **Secret** is a named value (typically a token, password, or API key) that is injected into a Collector at runtime from the server's environment. Secrets let you call authenticated APIs without ever writing credentials into your Python scripts or Git repository.

---

## Why Secrets exist

If you hardcode a token in a Collector script, it ends up in your Git history and in any logs that record the script source. Secrets solve this by:

- Keeping credential values **outside the repository** entirely
- Resolving the value **at runtime** from environment variables
- Making the script **declare** which secrets it needs via the `@secret` decorator

---

## How Secrets flow

```
Environment variable (server)
        ↓
  @secret("MY_API_KEY") decorator on collect()
        ↓
  secrets["MY_API_KEY"] inside collect()
        ↓
  Used to authenticate an API call
        ↓
  Value never logged, never in YAML, never in Dashboard output
```

---

## The `@secret` decorator

Use `@secret("ENV_VAR_NAME")` to declare that a Collector needs a specific environment variable. The decorator resolves the variable and passes it to `collect()` as the `secrets` dict.

```python
from src.models.collector import Collector, secret

class GitHubCollector(Collector):
    @secret("GITHUB_TOKEN")
    def collect(self, secrets: dict) -> list[dict]:
        token = secrets["GITHUB_TOKEN"]
        # Use token to call GitHub API
        ...
```

### Multiple secrets

Stack decorators to require more than one secret:

```python
class MultiSecretCollector(Collector):
    @secret("DB_PASSWORD")
    @secret("API_KEY")
    def collect(self, secrets: dict) -> list[dict]:
        db_pass = secrets["DB_PASSWORD"]
        api_key = secrets["API_KEY"]
        ...
```

---

## Setting secrets

Set secrets as environment variables on the server before starting the backend:

```bash
export GITHUB_TOKEN=ghp_your_token_here
export DB_PASSWORD=super_secret_password
```

!!! warning "Never commit secret values"
    Use a `.env` file (gitignored), Docker secrets, Kubernetes secrets, or a secrets manager like HashiCorp Vault. Never put the values in your Git repository.

---

## What happens when a secret is missing

If the environment variable is not set when `collect()` runs, Chart-Monitor raises a `KeyError` with a descriptive message:

```
Secret 'GITHUB_TOKEN' not found in environment.
Set the environment variable 'GITHUB_TOKEN' to proceed.
```

The error is logged on the backend and surfaces as an error message in the Dashboard. The rest of the application continues running — a missing secret causes that one Collector to fail, not a full crash.

---

## Security guarantees

- Secret values are **never written to YAML, JSON, or any persisted file**
- Secret values are **never included in Dashboard API responses**
- Secret values are **never logged** (only the variable name appears in error messages)
- Scripts run inside a RestrictedPython sandbox that prevents direct `os.environ` access — secrets must be declared via `@secret`

See [Load Secrets](../how-to/load-secrets.md) for a complete walkthrough.
