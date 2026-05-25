# Connect a Git Repository

Chart-Monitor loads all Collector and Dashboard scripts from a Git repository. Until a repository is configured, the app shows the setup page and no dashboards are available.

!!! info "Why Git?"
    Storing monitoring scripts in Git gives you version history, code review, and branch-based workflows for your entire monitoring configuration.

## Connection methods

Chart-Monitor supports three ways to authenticate with a Git repository:

| Method | Value | Best for |
|--------|-------|----------|
| SSH key | `ssh` (default) | GitHub, GitLab, any server with SSH deploy keys |
| HTTP token | `http-token` | Servers that accept a single bearer/access token |
| HTTP username + token | `http-user-token` | Servers that require Basic auth (username + password/PAT) |

Set `GIT_CONNECTION_METHOD` (or `gitops.connection` in Helm) to select the method.

---

## SSH connection (default)

### Step 1: Generate an SSH Key Pair

Run this command on the machine that hosts Chart-Monitor:

```bash
ssh-keygen -t ed25519 -C "chart-monitor-deploy" \
  -f ~/.ssh/id_rsa_chart_monitor -N ""
```

This creates two files:

| File | Purpose |
|------|---------|
| `~/.ssh/id_rsa_chart_monitor` | Private key — stays on the server, never shared |
| `~/.ssh/id_rsa_chart_monitor.pub` | Public key — added to your Git provider |

### Step 2: Add the Deploy Key to Your Git Provider

=== "GitHub"

    1. Open your repository on GitHub
    2. Go to **Settings → Deploy keys → Add deploy key**
    3. Paste the public key into the **Key** field
    4. Give it a title (e.g. `chart-monitor`)
    5. Leave **Allow write access** unchecked unless your scripts need to push
    6. Click **Add key**

=== "GitLab"

    1. Open your project on GitLab
    2. Go to **Settings → Repository → Deploy keys**
    3. Click **Add new deploy key**
    4. Paste the public key and give it a name
    5. Click **Add key**

=== "Bitbucket"

    1. Open your repository on Bitbucket
    2. Go to **Repository settings → Access keys**
    3. Click **Add key**
    4. Paste the public key and give it a label
    5. Click **Add key**

### Step 3: Set Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GIT_CONNECTION_METHOD` | Connection method | `ssh` |
| `GIT_SSH_URL` | SSH clone URL | `git@github.com:your-org/your-repo.git` |
| `GIT_SSH_KEY_PATH` | Absolute path to the **private** key file | `/home/user/.ssh/id_rsa_chart_monitor` |
| `GIT_TARGET_PATH` | Directory where scripts will be cloned | `/app/store` |
| `SYNC_SECRET` | Secret to authenticate manual sync requests | `change-me-to-something-strong` |
| `GIT_SKIP_VERIFY` | Set to `true` to bypass SSH host key verification (on-prem only) | `false` (default) |

```bash
export GIT_CONNECTION_METHOD=ssh
export GIT_SSH_URL=git@github.com:your-org/your-repo.git
export GIT_SSH_KEY_PATH=/home/user/.ssh/id_rsa_chart_monitor
export GIT_TARGET_PATH=/app/store
export SYNC_SECRET=change-me-to-something-strong
```

!!! warning "Keep private key and SYNC_SECRET private"
    Never commit these values. Use a `.env` file (gitignored) or your secrets manager.

---

## HTTP token authentication

Use this method when your Git server supports token-based authentication over HTTPS (GitLab deploy tokens, GitHub fine-grained tokens, Gitea tokens, etc.).

### Set Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GIT_CONNECTION_METHOD` | Connection method | `http-token` |
| `GIT_REPO_URL` | HTTPS clone URL | `https://github.com/your-org/your-repo.git` |
| `GIT_HTTP_TOKEN` | Repository access token | `ghp_xxxxxxxxxxxx` |
| `GIT_TARGET_PATH` | Directory where scripts will be cloned | `/app/store` |
| `SYNC_SECRET` | Secret to authenticate manual sync requests | `change-me-to-something-strong` |

```bash
export GIT_CONNECTION_METHOD=http-token
export GIT_REPO_URL=https://github.com/your-org/your-repo.git
export GIT_HTTP_TOKEN=ghp_xxxxxxxxxxxx
export GIT_TARGET_PATH=/app/store
export SYNC_SECRET=change-me-to-something-strong
```

**Via Helm:**

```yaml
gitops:
  connection: http-token
  httpToken:
    url: "https://github.com/your-org/your-repo.git"
```

Add `GIT_HTTP_TOKEN` to your Kubernetes Secret:

```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<sync-token> \
  --from-literal=GIT_HTTP_TOKEN=<repo-token> \
  -n chart-monitor
```

---

## HTTP username + token authentication

Use this method when your Git server requires a username alongside the token (Bitbucket Server, some self-hosted GitLab/Gitea instances).

### Set Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GIT_CONNECTION_METHOD` | Connection method | `http-user-token` |
| `GIT_REPO_URL` | HTTPS clone URL | `https://gitlab.company.internal/org/repo.git` |
| `GIT_HTTP_USERNAME` | Username | `svc-account` |
| `GIT_HTTP_TOKEN` | Password or personal access token | `glpat-xxxxxxxxxxxx` |
| `GIT_TARGET_PATH` | Directory where scripts will be cloned | `/app/store` |
| `SYNC_SECRET` | Secret to authenticate manual sync requests | `change-me-to-something-strong` |

```bash
export GIT_CONNECTION_METHOD=http-user-token
export GIT_REPO_URL=https://gitlab.company.internal/org/repo.git
export GIT_HTTP_USERNAME=svc-account
export GIT_HTTP_TOKEN=glpat-xxxxxxxxxxxx
export GIT_TARGET_PATH=/app/store
export SYNC_SECRET=change-me-to-something-strong
```

**Via Helm:**

```yaml
gitops:
  connection: http-user-token
  httpUserToken:
    url: "https://gitlab.company.internal/org/repo.git"
    username: "svc-account"
```

Add `GIT_HTTP_TOKEN` to your Kubernetes Secret:

```bash
kubectl create secret generic chart-monitor \
  --from-literal=SYNC_SECRET=<sync-token> \
  --from-literal=GIT_HTTP_TOKEN=<password-or-pat> \
  -n chart-monitor
```

---

## Using a self-signed or on-prem Git server

Set `GIT_SKIP_VERIFY=true` to bypass certificate verification. This works for both SSH (host key) and HTTPS (TLS certificate) connections:

```bash
export GIT_SKIP_VERIFY=true
```

**Via Helm:**

```yaml
gitops:
  connection: http-user-token
  httpUserToken:
    url: "https://git.company.internal/org/repo.git"
    username: "svc-account"
  skipVerify: true
```

!!! warning "Security note"
    Only enable `GIT_SKIP_VERIFY` on trusted internal networks. Bypassing verification removes protection against man-in-the-middle attacks on the Git connection.

---

## Migrating from 0.1.x to 0.2.0

The `gitops:` Helm values block has been restructured. Update your values file:

```yaml
# Before (0.1.x):
gitops:
  sshUrl: "git@github.com:org/repo.git"

# After (0.2.0):
gitops:
  connection: ssh
  ssh:
    url: "git@github.com:org/repo.git"
```

---

## Step 4: Restart the Backend

After setting the environment variables, restart Chart-Monitor:

```bash
cd backend && uvicorn src.main:app --reload
```

The GitOps setup page disappears automatically once all required variables are detected.

---

## Troubleshooting

??? failure "Permission denied (publickey)"
    The private key path is wrong, or the public key was not saved correctly to the Git provider.
    Verify with: `ssh -i ~/.ssh/id_rsa_chart_monitor -T git@github.com`

??? failure "Setup page still appears after restart"
    Check that all required variables are exported in the same shell session that starts uvicorn.
    Run `env | grep GIT` and `env | grep SYNC` to confirm.

??? failure "Host key verification failed"
    For public Git providers: run `ssh-keyscan github.com >> ~/.ssh/known_hosts` before starting the backend.
    For on-premises Git servers: set `GIT_SKIP_VERIFY=true` (see section above).

??? failure "HTTP 401 Unauthorized"
    Check that `GIT_HTTP_TOKEN` in the Secret is correct and not expired.
    For `http-user-token`: verify `GIT_HTTP_USERNAME` matches the account that owns the token.

??? failure "TLS certificate error"
    Your Git server uses a self-signed or internally signed HTTPS certificate.
    Set `GIT_SKIP_VERIFY=true` on trusted internal networks.
