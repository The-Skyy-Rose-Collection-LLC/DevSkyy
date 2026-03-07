"""
Feature Flags REST API
======================

CRUD endpoints for managing feature flags.
Protected by admin role.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/flags", tags=["feature-flags"])


class FlagCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    enabled: bool = False
    rollout_percentage: int = Field(default=0, ge=0, le=100)
    enabled_for_users: list[str] = Field(default_factory=list)
    disabled_for_users: list[str] = Field(default_factory=list)


class FlagResponse(BaseModel):
    name: str
    enabled: bool
    rollout_percentage: int
    enabled_for_users: list[str]
    disabled_for_users: list[str]
    kill_switch: bool = False


class RolloutRequest(BaseModel):
    percentage: int = Field(..., ge=0, le=100)


@router.get("", response_model=list[FlagResponse])
async def list_flags() -> list[FlagResponse]:
    """List all feature flags."""
    from core.feature_flags.flag_manager import flag_manager

    flags = flag_manager.get_all_flags()
    return [
        FlagResponse(
            name=f.name,
            enabled=f.enabled,
            rollout_percentage=f.rollout_percentage,
            enabled_for_users=list(f.enabled_for_users),
            disabled_for_users=list(f.disabled_for_users),
            kill_switch=f.kill_switch,
        )
        for f in flags.values()
    ]


@router.put("/{flag_name}", response_model=FlagResponse)
async def upsert_flag(flag_name: str, request: FlagCreateRequest) -> FlagResponse:
    """Create or update a feature flag."""
    from core.feature_flags.flag_manager import FeatureFlag, flag_manager

    flag = FeatureFlag(
        name=flag_name,
        enabled=request.enabled,
        rollout_percentage=request.rollout_percentage,
        enabled_for_users=set(request.enabled_for_users),
        disabled_for_users=set(request.disabled_for_users),
    )
    flag_manager.set_flag(flag)

    return FlagResponse(
        name=flag.name,
        enabled=flag.enabled,
        rollout_percentage=flag.rollout_percentage,
        enabled_for_users=list(flag.enabled_for_users),
        disabled_for_users=list(flag.disabled_for_users),
        kill_switch=flag.kill_switch,
    )


@router.post("/{flag_name}/rollout", response_model=FlagResponse)
async def update_rollout(flag_name: str, request: RolloutRequest) -> FlagResponse:
    """Update rollout percentage for a flag."""
    from core.feature_flags.flag_manager import flag_manager

    flags = flag_manager.get_all_flags()
    flag = flags.get(flag_name)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")

    flag.rollout_percentage = request.percentage
    flag_manager.set_flag(flag)

    return FlagResponse(
        name=flag.name,
        enabled=flag.enabled,
        rollout_percentage=flag.rollout_percentage,
        enabled_for_users=list(flag.enabled_for_users),
        disabled_for_users=list(flag.disabled_for_users),
        kill_switch=flag.kill_switch,
    )


@router.delete("/{flag_name}")
async def delete_flag(flag_name: str) -> dict[str, str]:
    """Delete a feature flag."""
    from core.feature_flags.flag_manager import flag_manager

    if hasattr(flag_manager, "delete_flag"):
        flag_manager.delete_flag(flag_name)
    else:
        # In-memory only: just remove from dict
        flag_manager._flags.pop(flag_name, None)

    return {"status": "deleted", "flag": flag_name}
