# Connect a Git Repository

Chart-Monitor loads all Collector and Dashboard scripts from a Git repository. Until a repository is configured, the app shows the setup page and no dashboards are available.

!!! info "Why Git?"
    Storing monitoring scripts in Git gives you version history, code review, and branch-based workflows for your entire monitoring configuration.

## Prerequisites

- A Git repository (GitHub, GitLab, or Bitbucket)
- SSH access to the machine running Chart-Monitor
- The Chart-Monitor backend running (or about to be started)

---

## Step 1: Generate an SSH Key Pair

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

Copy the public key to your clipboard:

```bash
cat ~/.ssh/id_rsa_chart_monitor.pub
```

---

## Step 2: Add the Deploy Key to Your Git Provider

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

---

## Step 3: Set Environment Variables

Set all four environment variables before starting (or restarting) the backend:

| Variable | Description | Example |
|----------|-------------|---------|
| `GIT_SSH_URL` | SSH clone URL of your repository | `git@github.com:your-org/your-repo.git` |
| `GIT_SSH_KEY_PATH` | Absolute path to the **private** key file | `/home/user/.ssh/id_rsa_chart_monitor` |
| `GIT_TARGET_PATH` | Directory where scripts will be cloned | `/app/store` |
| `SYNC_SECRET` | A strong secret used to authenticate manual sync requests | `change-me-to-something-strong` |

Example (Linux/macOS shell):

```bash
export GIT_SSH_URL=git@github.com:your-org/your-repo.git
export GIT_SSH_KEY_PATH=/home/user/.ssh/id_rsa_chart_monitor
export GIT_TARGET_PATH=/app/store
export SYNC_SECRET=change-me-to-something-strong
```

!!! warning "Keep `GIT_SSH_KEY_PATH` and `SYNC_SECRET` private"
    Never commit these values. Use a `.env` file (gitignored) or your secrets manager.

---

## Step 4: Restart the Backend

After setting the environment variables, restart Chart-Monitor:

```bash
cd backend && uvicorn src.main:app --reload
```

The GitOps setup page disappears automatically once all four variables are detected.

---

## Troubleshooting

??? failure "Permission denied (publickey)"
    The private key path is wrong, or the public key was not saved correctly to the Git provider.
    Verify with: `ssh -i ~/.ssh/id_rsa_chart_monitor -T git@github.com`

??? failure "Setup page still appears after restart"
    Check that all four variables are exported in the same shell session that starts uvicorn.
    Run `env | grep GIT` and `env | grep SYNC` to confirm.

??? failure "Host key verification failed"
    Run `ssh-keyscan github.com >> ~/.ssh/known_hosts` (replace `github.com` with your provider) before starting the backend.
