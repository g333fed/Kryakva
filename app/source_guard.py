from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from app.config import ROOT_DIR

logger = logging.getLogger(__name__)

EXPECTED_GITHUB_HOST = "github.com"


class SourceGuardError(RuntimeError):
    """Raised when source provenance check fails."""


def _git_remote_url(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def ensure_github_source() -> None:
    """Allow running only when repository origin points to GitHub.

    Can be bypassed with environment variable `KRYAKVA_ALLOW_UNVERIFIED_SOURCE=1`.
    """
    if os.getenv("KRYAKVA_ALLOW_UNVERIFIED_SOURCE") == "1":
        logger.warning("Source guard bypassed via KRYAKVA_ALLOW_UNVERIFIED_SOURCE=1")
        return

    repo_root = ROOT_DIR
    if not (repo_root / ".git").exists():
        raise SourceGuardError(
            "Source guard: .git metadata not found. Download/use project from GitHub clone."
        )

    try:
        remote_url = _git_remote_url(repo_root)
    except Exception as error:
        raise SourceGuardError("Source guard: unable to verify git origin.") from error

    if EXPECTED_GITHUB_HOST not in remote_url.lower():
        raise SourceGuardError(
            f"Source guard: unsupported origin '{remote_url}'. Only GitHub sources are allowed."
        )

    logger.info("Source guard passed: %s", remote_url)
