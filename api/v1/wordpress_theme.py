"""WordPress Theme Management API.

Endpoints for managing WordPress theme configuration and deployment.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from security.jwt_oauth2_auth import RoleChecker, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(tags=["wordpress-theme"], prefix="/wordpress/theme")
require_admin = RoleChecker([UserRole.ADMIN])

# Resolved once at import time; api/v1/wordpress_theme.py → repo root is two parents up.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEPLOY_SCRIPT = _PROJECT_ROOT / "scripts" / "deploy-theme.sh"
_DEPLOY_TIMEOUT_S = 600
# Bound on reaping a SIGKILL'd child so a D-state process can't hang the loop.
_REAP_TIMEOUT_S = 10


async def _kill_and_reap(proc: asyncio.subprocess.Process) -> None:
    """SIGKILL a still-running deploy child and reap it without hanging the loop.

    kill() (SIGKILL, uncatchable) is used over terminate() so the deploy script
    cannot ignore it. The child is reaped with proc.wait() — never a second
    communicate(), whose pipe readers are indeterminate after the cancelled await
    and could deadlock. wait() is itself bounded so a process stuck in an
    uninterruptible (D-state) kernel wait cannot block the event loop forever.
    """
    try:
        proc.kill()
    except ProcessLookupError:
        return  # already exited between the timeout and the kill
    try:
        await asyncio.wait_for(proc.wait(), timeout=_REAP_TIMEOUT_S)
    except TimeoutError:
        logger.warning(
            "Deploy child still alive %ds after SIGKILL; leaving it for the OS to reap",
            _REAP_TIMEOUT_S,
        )


class ThemeConfig(BaseModel):
    """WordPress theme configuration."""

    name: str
    version: str
    primary_color: str = "#B76E79"
    enable_3d_viewer: bool = True
    enable_ar: bool = True


class ThemeDeployRequest(BaseModel):
    """Request to deploy theme to WordPress."""

    environment: str = "production"
    backup_first: bool = True
    with_maintenance: bool = False


@router.get("/config", response_model=ThemeConfig, summary="Get theme config")
async def get_theme_config(
    current_user: dict = Depends(require_admin),
) -> ThemeConfig:
    """Get current WordPress theme configuration."""
    return ThemeConfig(
        name="skyyrose-flagship",
        version="3.2.0",
        primary_color="#B76E79",
        enable_3d_viewer=True,
        enable_ar=True,
    )


@router.post("/deploy", summary="Deploy theme")
async def deploy_theme(
    request: ThemeDeployRequest,
    current_user: dict = Depends(require_admin),
) -> dict[str, Any]:
    """Deploy WordPress theme via the production deploy script.

    Non-production environments are always run with --dry-run (safe preview).
    The deploy script always takes a backup before hot-swapping; backup_first
    is informational only and noted in the response message.
    """
    if not _DEPLOY_SCRIPT.exists():
        raise HTTPException(status_code=500, detail=f"Deploy script not found: {_DEPLOY_SCRIPT}")

    is_dry_run = request.environment != "production"
    flags: list[str] = ["--dry-run"] if is_dry_run else []
    if request.with_maintenance:
        flags.append("--with-maintenance")

    proc: asyncio.subprocess.Process | None = None
    try:
        proc = await asyncio.create_subprocess_exec(
            "bash",
            str(_DEPLOY_SCRIPT),
            *flags,
            cwd=str(_PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=_DEPLOY_TIMEOUT_S
        )
    except TimeoutError:
        logger.error("Theme deploy timed out after %ds", _DEPLOY_TIMEOUT_S)
        # wait_for cancelled communicate() but the child is still running in the OS.
        # SIGKILL + bounded reap so we neither leak a zombie nor hang the loop.
        # (proc is always bound here — TimeoutError only comes from wait_for, after
        # create_subprocess_exec succeeded — but guard for the type-checker.)
        if proc is not None:
            await _kill_and_reap(proc)
        return {
            "success": False,
            "returncode": -1,
            "environment": request.environment,
            "message": f"deploy timed out after {_DEPLOY_TIMEOUT_S}s",
            "log_tail": [],
        }
    except asyncio.CancelledError:
        # Request cancelled (client disconnect / server shutdown). Kill the child
        # so the deploy does not keep running unattended. Do NOT await here — the
        # task is unwinding; the OS reaps the killed child when this process exits.
        if proc is not None and proc.returncode is None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
        raise
    except FileNotFoundError as exc:
        logger.error("bash or deploy script not found: %s", exc)
        raise HTTPException(status_code=500, detail="bash or deploy script not found") from exc

    combined = (stdout_bytes + b"\n" + stderr_bytes).decode("utf-8", errors="replace")
    log_tail = [line for line in combined.splitlines() if line.strip()][-20:]

    success = proc.returncode == 0
    dry_label = " (dry-run)" if is_dry_run else ""
    backup_note = " Script always backs up before hot-swap." if request.backup_first else ""

    if success:
        message = f"Theme deploy ({request.environment}){dry_label} succeeded.{backup_note}"
    else:
        message = (
            f"Theme deploy ({request.environment}){dry_label} failed (exit code {proc.returncode})."
        )

    logger.info("Theme deploy returncode=%d env=%s", proc.returncode, request.environment)
    return {
        "success": success,
        "returncode": proc.returncode,
        "environment": request.environment,
        "message": message,
        "log_tail": log_tail,
    }
