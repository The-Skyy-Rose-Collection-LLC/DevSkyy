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
        logger.error("Theme deploy timed out after %ds; killing subprocess", _DEPLOY_TIMEOUT_S)
        # wait_for cancelled communicate(): the pipe readers are in an
        # indeterminate state, so kill + reap with wait() — never a second
        # communicate() (can deadlock). Guard the race where the process
        # already exited between the timeout and the kill.
        try:
            proc.kill()
            await proc.wait()
        except ProcessLookupError:
            pass
        return {
            "success": False,
            "returncode": proc.returncode if proc.returncode is not None else -1,
            "environment": request.environment,
            "message": f"deploy timed out after {_DEPLOY_TIMEOUT_S}s (subprocess killed)",
            "log_tail": [],
        }
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
