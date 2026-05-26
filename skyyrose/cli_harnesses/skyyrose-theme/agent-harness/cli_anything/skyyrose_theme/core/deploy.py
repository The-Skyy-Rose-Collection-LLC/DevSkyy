"""
Deploy orchestration for the SkyyRose theme.

Wraps scripts/deploy-theme.sh (hot-swap by default, --with-maintenance flag).
All production-touching operations require:
  1. build_deploy_manifest() → caller prints and waits for --confirm
  2. run_deploy(manifest, confirmed=True)

STOP-AND-SHOW contract:
  - build_deploy_manifest() never touches the site — returns a structured dict.
  - run_deploy() raises DeployNotConfirmedError if confirmed=False.
  - Subprocess args are always lists; shell=True is never used.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULT_THEME_ROOT = Path(
    os.environ.get(
        "SKYYROSE_THEME_ROOT",
        str(Path.home() / "DevSkyy/wordpress-theme/skyyrose-flagship"),
    )
)
_DEFAULT_DEPLOY_SCRIPT = Path(
    os.environ.get(
        "SKYYROSE_DEPLOY_SCRIPT",
        str(Path.home() / "DevSkyy/scripts/deploy-theme.sh"),
    )
)
_DEFAULT_PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://skyyrose.co")

# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class DeployError(RuntimeError):
    """Base class for deploy errors."""


class DeployScriptNotFoundError(DeployError):
    """Raised when deploy-theme.sh cannot be found."""


class DeployNotConfirmedError(DeployError):
    """Raised when run_deploy is called without explicit confirmation."""


class DeployFailedError(DeployError):
    """Raised when deploy-theme.sh exits non-zero."""


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeployManifest:
    theme_root: Path
    deploy_script: Path
    dry_run: bool
    with_maintenance: bool
    public_url: str
    mode: str  # "hot-swap" | "maintenance"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": "deploy",
            "theme_root": str(self.theme_root),
            "deploy_script": str(self.deploy_script),
            "dry_run": self.dry_run,
            "mode": self.mode,
            "public_url": self.public_url,
            "cost": "$0 (no paid API calls)",
            "irreversible": not self.dry_run,
        }


def build_deploy_manifest(
    dry_run: bool = False,
    with_maintenance: bool = False,
    theme_root: Path | None = None,
    deploy_script: Path | None = None,
    public_url: str | None = None,
) -> DeployManifest:
    """
    Build a DeployManifest describing what would happen.

    Never touches the live site — pure data construction.

    Args:
        dry_run: If True, pass --dry-run to deploy-theme.sh.
        with_maintenance: If True, pass --with-maintenance (site lock during deploy).
        theme_root: Override SKYYROSE_THEME_ROOT.
        deploy_script: Override SKYYROSE_DEPLOY_SCRIPT.
        public_url: Override PUBLIC_URL.

    Returns:
        DeployManifest

    Raises:
        DeployScriptNotFoundError: if the deploy script doesn't exist.
    """
    script = deploy_script or _DEFAULT_DEPLOY_SCRIPT
    if not script.exists():
        raise DeployScriptNotFoundError(
            f"deploy-theme.sh not found at {script}. "
            "Set SKYYROSE_DEPLOY_SCRIPT env var or ensure DevSkyy repo is checked out."
        )

    root = theme_root or _DEFAULT_THEME_ROOT
    url = public_url or _DEFAULT_PUBLIC_URL
    mode = "maintenance" if with_maintenance else "hot-swap"

    return DeployManifest(
        theme_root=root,
        deploy_script=script,
        dry_run=dry_run,
        with_maintenance=with_maintenance,
        public_url=url,
        mode=mode,
    )


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def run_deploy(
    manifest: DeployManifest,
    confirmed: bool = False,
) -> subprocess.CompletedProcess:
    """
    Execute deploy-theme.sh according to *manifest*.

    Args:
        manifest: Built by build_deploy_manifest().
        confirmed: Must be True. DeployNotConfirmedError otherwise.

    Returns:
        subprocess.CompletedProcess

    Raises:
        DeployNotConfirmedError: if confirmed=False.
        DeployFailedError: if the script exits non-zero.
    """
    if not confirmed:
        raise DeployNotConfirmedError(
            "run_deploy requires confirmed=True. "
            "Print the manifest and get explicit user confirmation first."
        )

    cmd: list[str] = ["bash", str(manifest.deploy_script)]
    if manifest.dry_run:
        cmd.append("--dry-run")
    if manifest.with_maintenance:
        cmd.append("--with-maintenance")

    env = {**os.environ, "PUBLIC_URL": manifest.public_url}

    result = subprocess.run(
        cmd,
        capture_output=False,  # stream to terminal
        text=True,
        cwd=str(manifest.theme_root),
        env=env,
    )

    if result.returncode != 0:
        raise DeployFailedError(
            f"deploy-theme.sh exited {result.returncode}. Check terminal output for details."
        )

    return result


# ---------------------------------------------------------------------------
# Cache purge (wp-cli over SSH)
# ---------------------------------------------------------------------------

_SSH_HOST = os.environ.get("SKYYROSE_SSH_HOST", "skyyrose.wordpress.com@ssh.wp.com")
_WP_ROOT = os.environ.get("SKYYROSE_WP_ROOT", "/srv/htdocs")
_WP_CLI = os.environ.get("SKYYROSE_WP_CLI", "/usr/local/bin/wp")
_ADMIN_USER = os.environ.get("SKYYROSE_ADMIN_USER", "corey@skyyrose.co")


def purge_cache(
    ssh_host: str | None = None,
    wp_root: str | None = None,
    wp_cli: str | None = None,
) -> subprocess.CompletedProcess:
    """
    Flush Jetpack / server-side caches via wp-cli over SSH.

    Runs: ssh <host> "wp cache flush --path=<root> --allow-root"

    Raises:
        DeployFailedError: if ssh/wp-cli exits non-zero.
    """
    host = ssh_host or _SSH_HOST
    root = wp_root or _WP_ROOT
    cli = wp_cli or _WP_CLI

    remote_cmd = f"{cli} cache flush --path={root} --allow-root"
    cmd = ["ssh", host, remote_cmd]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DeployFailedError(
            f"wp cache flush failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result
