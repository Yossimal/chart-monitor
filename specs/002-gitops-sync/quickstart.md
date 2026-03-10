# GitOps Support - Quickstart

This guide explains how to configure Chart-Monitor to sync Python scripts dynamically from a remote Git repository.

## Prerequisites

1. **SSH Key Pair**: You must have an SSH private key that has read access to your target Git repository.
   - We recommend a dedicated deploy key with read-only permissions for security.
2. **Repository Structure**: The remote repository should only contain `.py` and `.txt` files in the root or configured subdirectories. Any other file types will cause the sync validation to abort for security reasons.

## Configuration

To enable GitOps Support, you must launch the Chart-Monitor backend with the following environment variables:

| Variable           | Description                                                           | Example                                             |
| ------------------ | --------------------------------------------------------------------- | --------------------------------------------------- |
| `GIT_SSH_URL`      | The SSH URL to the git repository containing your scripts.            | `git@github.com:your-org/chart-monitor-scripts.git` |
| `GIT_SSH_KEY_PATH` | The absolute path on the container/host to the private SSH key.       | `/root/.ssh/id_rsa_deploy`                          |
| `GIT_TARGET_PATH`  | The absolute path where the system will clone and read the scripts.   | `/app/store`                                        |
| `SYNC_SECRET`      | A secure token used to authenticate manual sync requests from the UI. | `SuperSecretToken123`                               |

*Note: If any of these variables are missing, the Sync feature may fail or operate in degraded mode.*

## Using the Feature

1. Open the Chart-Monitor web UI.
2. Ensure your backend is running with the correct environment variables.
3. Click the **"Sync"** button located at the bottom of the dashboards sidebar.
4. A prompt will appear asking for the `SYNC_SECRET`. Enter the secret you configured (e.g., `MySecureSyncToken2026`). You can check **"Remember me"** to save it in your browser for next time.
5. The system will securely connect to the repository and pull down the latest `.py` and `.txt` files into the `GIT_TARGET_PATH` using your host shell.
6. Upon success, an alert will confirm the scripts were rerendered. If any syntax errors or connection timeouts occur, a detailed error alert will display.

For provider-specific key setup instructions (GitHub, GitLab, Bitbucket), click the configuration link next to the Sync button in the UI.
