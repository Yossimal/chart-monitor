"""GitOps Sync – Git repository operations via shell commands.

This module handles all interaction with the remote Git repository.
All operations use the system ``git`` binary directly (via subprocess)
so no external Python Git libraries are required.

Environment Variables
---------------------
GIT_CONNECTION_METHOD : Connection method: "ssh" (default), "http-token", or
                        "http-user-token".
GIT_SSH_URL           : SSH URL of the remote repository (ssh method).
GIT_SSH_KEY_PATH      : Absolute path to the private SSH key file (ssh method).
GIT_REPO_URL          : HTTPS URL of the remote repository (http-* methods).
GIT_HTTP_TOKEN        : Access token or password for HTTP authentication.
GIT_HTTP_USERNAME     : Username for the http-user-token method.
GIT_TARGET_PATH       : Absolute path where the repo will be cloned / pulled.
SYNC_SECRET           : Bearer token used to authenticate sync API requests.
GIT_SKIP_VERIFY       : Set to "true", "1", or "yes" to bypass SSH host key
                        verification (ssh method) or TLS certificate verification
                        (http-* methods). Defaults to false (secure-by-default).
"""
from __future__ import annotations

import logging
import os
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ── Allowed extensions ────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".py", ".txt"})

_VALID_CONNECTION_METHODS = ("ssh", "http-token", "http-user-token")


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class GitOpsConfig:
    """Parsed GitOps configuration from environment variables."""
    git_target_path: str
    sync_secret: str
    connection_method: str = "ssh"
    git_ssh_url: str = ""
    git_ssh_key_path: str = ""
    git_repo_url: str = ""
    git_http_token: str = ""
    git_http_username: str = ""
    git_skip_verify: bool = False


def load_gitops_config() -> Optional[GitOpsConfig]:
    """Load GitOps configuration from environment variables.

    Returns None and logs descriptive messages if any variable is missing.
    """
    connection_method = os.environ.get("GIT_CONNECTION_METHOD", "ssh").lower().strip()

    if connection_method not in _VALID_CONNECTION_METHODS:
        logger.error(
            "GitOps is DISABLED. GIT_CONNECTION_METHOD=%r is invalid. "
            "Valid values: %s",
            connection_method,
            ", ".join(_VALID_CONNECTION_METHODS),
        )
        return None

    missing: list[str] = []

    git_target_path = os.environ.get("GIT_TARGET_PATH")
    sync_secret = os.environ.get("SYNC_SECRET")
    git_skip_verify = os.environ.get("GIT_SKIP_VERIFY", "").lower() in ("true", "1", "yes")

    if not git_target_path:
        missing.append("GIT_TARGET_PATH (e.g. /app/store)")
    if not sync_secret:
        missing.append("SYNC_SECRET (a secret token to authenticate sync requests)")

    # Method-specific required variables
    git_ssh_url = ""
    git_ssh_key_path = ""
    git_repo_url = ""
    git_http_token = ""
    git_http_username = ""

    if connection_method == "ssh":
        git_ssh_url = os.environ.get("GIT_SSH_URL", "")
        git_ssh_key_path = os.environ.get("GIT_SSH_KEY_PATH", "")
        if not git_ssh_url:
            missing.append("GIT_SSH_URL (e.g. git@github.com:your-org/scripts.git)")
        if not git_ssh_key_path:
            missing.append("GIT_SSH_KEY_PATH (e.g. /app/secrets/id_rsa)")

    elif connection_method in ("http-token", "http-user-token"):
        git_repo_url = os.environ.get("GIT_REPO_URL", "")
        git_http_token = os.environ.get("GIT_HTTP_TOKEN", "")
        if not git_repo_url:
            missing.append("GIT_REPO_URL (e.g. https://github.com/your-org/repo.git)")
        if not git_http_token:
            missing.append("GIT_HTTP_TOKEN (repository access token or password)")
        if connection_method == "http-user-token":
            git_http_username = os.environ.get("GIT_HTTP_USERNAME", "")
            if not git_http_username:
                missing.append("GIT_HTTP_USERNAME (username for HTTP authentication)")

    if missing:
        logger.error(
            "GitOps is DISABLED. The following environment variables are missing or empty:\n%s\n"
            "Please set these variables to enable GitOps sync.",
            "\n".join(f"  - {v}" for v in missing),
        )
        return None

    return GitOpsConfig(
        git_target_path=git_target_path,  # type: ignore[arg-type]
        sync_secret=sync_secret,  # type: ignore[arg-type]
        connection_method=connection_method,
        git_ssh_url=git_ssh_url,
        git_ssh_key_path=git_ssh_key_path,
        git_repo_url=git_repo_url,
        git_http_token=git_http_token,
        git_http_username=git_http_username,
        git_skip_verify=git_skip_verify,
    )


# ── Module-level singleton ─────────────────────────────────────────────────────
gitops_config: Optional[GitOpsConfig] = load_gitops_config()


def is_gitops_enabled() -> bool:
    """Return True if GitOps is properly configured."""
    return gitops_config is not None


# ── Git helpers ────────────────────────────────────────────────────────────────

def _build_git_env(key_path: str, skip_verify: bool = False) -> dict[str, str]:
    """Build git environment for SSH auth, injecting the key via GIT_SSH_COMMAND."""
    env = os.environ.copy()
    safe_key_path = key_path.replace("\\", "/")
    host_check = "no" if skip_verify else "accept-new"
    env["GIT_SSH_COMMAND"] = (
        f'ssh -i "{safe_key_path}"'
        f" -o StrictHostKeyChecking={host_check}"
        f" -o UserKnownHostsFile=/dev/null"
        f" -o BatchMode=yes"
        f" -o ConnectTimeout=30"
        f" -o ControlMaster=no"
        f" -o ControlPath=none"
    )
    return env


def _build_http_env(
    repo_url: str,
    token: str,
    username: str,
    skip_verify: bool = False,
) -> tuple[dict[str, str], str]:
    """Build git environment for HTTP auth using a temporary .netrc file.

    Credentials are written to $TMPDIR/.netrc (mode 0600) and HOME is pointed
    at that directory so git reads the file automatically. Caller must delete
    the returned tmp_dir in a finally block.

    Returns (env_dict, tmp_dir).
    """
    hostname = urlparse(repo_url).hostname or ""
    login = username if username else "oauth2"

    tmp_dir = tempfile.mkdtemp(prefix="chart-monitor-git-")
    netrc_path = os.path.join(tmp_dir, ".netrc")
    with open(netrc_path, "w") as f:
        f.write(f"machine {hostname} login {login} password {token}\n")
    os.chmod(netrc_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600

    env = os.environ.copy()
    env["HOME"] = tmp_dir
    if skip_verify:
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "http.sslVerify"
        env["GIT_CONFIG_VALUE_0"] = "false"
    return env, tmp_dir


def _run_git(args: list[str], cwd: str, env: dict[str, str]) -> subprocess.CompletedProcess:
    """Execute a git command and return the completed process."""
    logger.info("Running git command: git %s (cwd=%s)", " ".join(args), cwd)
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


# ── File validation ────────────────────────────────────────────────────────────

def validate_repo_extensions(target_path: str) -> Optional[str]:
    """Check all files in the repository. Return an error message if any are invalid.

    Returns None if all files are safe, or a descriptive error string.
    """
    root = Path(target_path)
    invalid_files: list[str] = []

    for p in root.rglob("*"):
        # Skip hidden files/directories (like .git) and __pycache__
        parts = p.parts
        if any(part.startswith(".") or part == "__pycache__" for part in parts):
            continue
        if p.is_file() and p.suffix not in ALLOWED_EXTENSIONS:
            invalid_files.append(str(p.relative_to(root)))

    if invalid_files:
        file_list = "\n".join(f"  - {f}" for f in invalid_files[:10])
        if len(invalid_files) > 10:
            file_list += f"\n  ... and {len(invalid_files) - 10} more."
        return (
            f"Security abort: repository contains {len(invalid_files)} file(s) "
            f"with disallowed extensions.\nOnly .py and .txt are permitted.\n"
            f"Offending files:\n{file_list}"
        )
    return None


# ── Core sync operation ────────────────────────────────────────────────────────

@dataclass
class SyncResult:
    """Result of a GitOps sync operation."""
    success: bool
    message: str
    details: str = ""


def perform_sync() -> SyncResult:
    """Perform the full GitOps sync: clone-or-pull, validate, and signal reload.

    Returns a SyncResult that describes the outcome.
    """
    if not is_gitops_enabled() or gitops_config is None:
        return SyncResult(
            success=False,
            message="GitOps is not configured.",
            details=(
                "One or more required environment variables are missing. "
                "Set GIT_CONNECTION_METHOD (ssh/http-token/http-user-token) and the "
                "corresponding credentials, GIT_TARGET_PATH, and SYNC_SECRET."
            ),
        )

    cfg = gitops_config
    target = cfg.git_target_path
    target_path = Path(target)
    tmp_dir: Optional[str] = None

    try:
        # ── Build connection environment ───────────────────────────────────────
        if cfg.connection_method == "ssh":
            git_env = _build_git_env(cfg.git_ssh_key_path, skip_verify=cfg.git_skip_verify)
            repo_url = cfg.git_ssh_url
        else:
            git_env, tmp_dir = _build_http_env(
                cfg.git_repo_url,
                cfg.git_http_token,
                cfg.git_http_username,
                skip_verify=cfg.git_skip_verify,
            )
            repo_url = cfg.git_repo_url

        try:
            # ── Clone or pull ──────────────────────────────────────────────────
            is_existing_repo = (target_path / ".git").exists()

            if not is_existing_repo:
                logger.info("Setting up repo %s in %s", repo_url, target)
                target_path.mkdir(parents=True, exist_ok=True)
                if not any(target_path.iterdir()):
                    result = _run_git(["clone", repo_url, "."], cwd=target, env=git_env)
                else:
                    logger.info("Directory is not empty, manually initializing repo...")
                    _run_git(["init"], cwd=target, env=git_env)
                    _run_git(["remote", "add", "origin", repo_url], cwd=target, env=git_env)
                    is_existing_repo = True

            if is_existing_repo:
                logger.info("Syncing existing repo at %s", target)
                _run_git(["fetch", "origin"], cwd=target, env=git_env)

                # Detect default branch from local remote-tracking ref (no extra network call).
                # git clone always populates refs/remotes/origin/HEAD; fall back to "main".
                default_branch = "main"
                sym_ref = _run_git(
                    ["symbolic-ref", "refs/remotes/origin/HEAD", "--short"],
                    cwd=target,
                    env=git_env,
                )
                if sym_ref.returncode == 0:
                    default_branch = sym_ref.stdout.strip().removeprefix("origin/")

                _run_git(["checkout", "-B", default_branch, f"origin/{default_branch}"], cwd=target, env=git_env)
                result = _run_git(["reset", "--hard", f"origin/{default_branch}"], cwd=target, env=git_env)

            if result.returncode != 0:
                stderr = result.stderr.strip()
                logger.error("Git operation failed: %s", stderr)
                return SyncResult(
                    success=False,
                    message="Git operation failed.",
                    details=stderr,
                )

            logger.info("Git operation succeeded: %s", result.stdout.strip() or "(up to date)")

            # ── File extension validation ──────────────────────────────────────
            validation_error = validate_repo_extensions(target)
            if validation_error:
                logger.error("File validation failed after pull:\n%s", validation_error)
                _run_git(["reset", "--hard", "HEAD~1"], cwd=target, env=git_env)
                return SyncResult(
                    success=False,
                    message="Sync aborted: repository contains disallowed files.",
                    details=validation_error,
                )

            # ── Signal store reload ────────────────────────────────────────────
            from src.storage.store import store
            store.reload()
            logger.info("Store reloaded successfully after sync.")

            return SyncResult(
                success=True,
                message="Sync completed successfully. Scripts have been updated.",
            )

        except subprocess.TimeoutExpired:
            logger.error("Git operation timed out after 60 seconds.")
            return SyncResult(
                success=False,
                message="Git operation timed out.",
                details="The connection to the Git server timed out after 60 seconds. Check connectivity.",
            )
        except FileNotFoundError:
            logger.error("'git' binary not found. Please ensure git is installed and in PATH.")
            return SyncResult(
                success=False,
                message="git binary not found.",
                details="The 'git' command is not available on this system. Please install git.",
            )
        except Exception as exc:
            logger.error("Unexpected error during sync: %s", exc, exc_info=True)
            return SyncResult(
                success=False,
                message="Unexpected error during sync.",
                details=str(exc),
            )

    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
