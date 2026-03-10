"""GitOps Sync – Git repository operations via shell commands.

This module handles all interaction with the remote Git repository.
All operations use the system ``git`` binary directly (via subprocess)
so no external Python Git libraries are required.

Environment Variables
---------------------
GIT_SSH_URL      : SSH URL of the remote repository.
GIT_SSH_KEY_PATH : Absolute path to the private SSH key file.
GIT_TARGET_PATH  : Absolute path where the repo will be cloned / pulled.
SYNC_SECRET      : Bearer token used to authenticate sync API requests.
"""
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Allowed extensions ────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".py", ".txt"})


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class GitOpsConfig:
    """Parsed GitOps configuration from environment variables."""
    git_ssh_url: str
    git_ssh_key_path: str
    git_target_path: str
    sync_secret: str


def load_gitops_config() -> Optional[GitOpsConfig]:
    """Load GitOps configuration from environment variables.

    Returns None and logs descriptive messages if any variable is missing.
    """
    missing: list[str] = []

    git_ssh_url = os.environ.get("GIT_SSH_URL")
    git_ssh_key_path = os.environ.get("GIT_SSH_KEY_PATH")
    git_target_path = os.environ.get("GIT_TARGET_PATH")
    sync_secret = os.environ.get("SYNC_SECRET")

    if not git_ssh_url:
        missing.append("GIT_SSH_URL (e.g. git@github.com:your-org/scripts.git)")
    if not git_ssh_key_path:
        missing.append("GIT_SSH_KEY_PATH (e.g. /app/secrets/id_rsa)")
    if not git_target_path:
        missing.append("GIT_TARGET_PATH (e.g. /app/store)")
    if not sync_secret:
        missing.append("SYNC_SECRET (a secret token to authenticate sync requests)")

    if missing:
        logger.error(
            "GitOps is DISABLED. The following environment variables are missing or empty:\n%s\n"
            "Please set these variables to enable GitOps sync.",
            "\n".join(f"  - {v}" for v in missing),
        )
        return None

    return GitOpsConfig(
        git_ssh_url=git_ssh_url,  # type: ignore[arg-type]
        git_ssh_key_path=git_ssh_key_path,  # type: ignore[arg-type]
        git_target_path=git_target_path,  # type: ignore[arg-type]
        sync_secret=sync_secret,  # type: ignore[arg-type]
    )


# ── Module-level singleton ─────────────────────────────────────────────────────
gitops_config: Optional[GitOpsConfig] = load_gitops_config()


def is_gitops_enabled() -> bool:
    """Return True if GitOps is properly configured."""
    return gitops_config is not None


# ── Git helpers ────────────────────────────────────────────────────────────────

def _build_git_env(key_path: str) -> dict[str, str]:
    """Build a clean environment for git, injecting SSH key via GIT_SSH_COMMAND."""
    env = os.environ.copy()
    
    # Ensure Windows paths are properly handled by SSH (use forward slashes and quotes)
    safe_key_path = key_path.replace('\\', '/')
    env["GIT_SSH_COMMAND"] = (
        f'ssh -i "{safe_key_path}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    )
    return env


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
            details="One or more required environment variables (GIT_SSH_URL, GIT_SSH_KEY_PATH, GIT_TARGET_PATH, SYNC_SECRET) are missing.",
        )

    cfg = gitops_config
    target = cfg.git_target_path
    target_path = Path(target)
    git_env = _build_git_env(cfg.git_ssh_key_path)

    try:
        # ── Clone or pull ──────────────────────────────────────────────────────
        is_existing_repo = (target_path / ".git").exists()

        if not is_existing_repo:
            logger.info("Setting up repo %s in %s", cfg.git_ssh_url, target)
            target_path.mkdir(parents=True, exist_ok=True)
            if not any(target_path.iterdir()):
                result = _run_git(["clone", cfg.git_ssh_url, "."], cwd=target, env=git_env)
                # If clone succeeds, we are good. If it fails, rely on returncode check below.
            else:
                logger.info("Directory is not empty, manually initializing repo...")
                _run_git(["init"], cwd=target, env=git_env)
                _run_git(["remote", "add", "origin", cfg.git_ssh_url], cwd=target, env=git_env)
                is_existing_repo = True

        if is_existing_repo:
            logger.info("Syncing existing repo at %s", target)
            _run_git(["fetch", "origin"], cwd=target, env=git_env)
            
            # Fetch default branch
            default_branch = "main"
            remote_info = _run_git(["remote", "show", "origin"], cwd=target, env=git_env)
            if "HEAD branch:" in remote_info.stdout:
                for line in remote_info.stdout.splitlines():
                    if "HEAD branch:" in line:
                        default_branch = line.split(":")[1].strip()
                        break
                        
            # Force checkout the default branch tracking the remote
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

        # ── File extension validation ──────────────────────────────────────────
        validation_error = validate_repo_extensions(target)
        if validation_error:
            logger.error("File validation failed after pull:\n%s", validation_error)
            # Attempt to recover by resetting to previous HEAD
            _run_git(["reset", "--hard", "HEAD~1"], cwd=target, env=git_env)
            return SyncResult(
                success=False,
                message="Sync aborted: repository contains disallowed files.",
                details=validation_error,
            )

        # ── Signal store reload ────────────────────────────────────────────────
        # Import here to avoid circular imports at module level
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
