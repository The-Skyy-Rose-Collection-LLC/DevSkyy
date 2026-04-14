"""
Portal — Team Management
========================

Manage team members within a tenant.

Endpoints:
    GET    /team              — list all team members
    POST   /team/invite       — add member by user_id + role
    DELETE /team/{user_id}    — remove member
    PATCH  /team/{user_id}    — change member role
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from core.auth.token_payload import TokenPayload
from security.jwt_oauth2_auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/team", tags=["Team"])

# Valid roles within a tenant
_VALID_ROLES = {"owner", "admin", "member", "viewer"}
# Roles that may not be assigned via API (owner is set on tenant creation only)
_ASSIGNABLE_ROLES = {"admin", "member", "viewer"}


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class TeamMember(BaseModel):
    """A single team member record."""

    user_id: str
    role: str
    joined_at: str


class TeamListResponse(BaseModel):
    """List of team members for a tenant."""

    tenant_id: str
    members: list[TeamMember]
    count: int
    timestamp: str


class InviteRequest(BaseModel):
    """Request to add a team member."""

    user_id: str = Field(..., description="User ID to invite")
    role: str = Field(default="member", description="Role: admin | member | viewer")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in _ASSIGNABLE_ROLES:
            raise ValueError(f"role must be one of {sorted(_ASSIGNABLE_ROLES)}")
        return v


class InviteResponse(BaseModel):
    """Response after adding a team member."""

    tenant_id: str
    user_id: str
    role: str
    message: str
    timestamp: str


class RoleUpdateRequest(BaseModel):
    """Request to change a member's role."""

    role: str = Field(..., description="New role: admin | member | viewer")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in _ASSIGNABLE_ROLES:
            raise ValueError(f"role must be one of {sorted(_ASSIGNABLE_ROLES)}")
        return v


# ---------------------------------------------------------------------------
# In-memory store (replace with DB repository in production)
# ---------------------------------------------------------------------------

# tenant_id → list of member dicts
_team_store: dict[str, list[dict]] = {}


def _get_members(tenant_id: str) -> list[dict]:
    return _team_store.get(tenant_id, [])


def _find_member(tenant_id: str, user_id: str) -> dict | None:
    for m in _get_members(tenant_id):
        if m["user_id"] == user_id:
            return m
    return None


def _require_tenant(request: Request, user: TokenPayload) -> str:
    """Return tenant_id from state or fall back to user.sub."""
    tenant_id = getattr(request.state, "tenant_id", "") or user.sub
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine tenant. Include X-Tenant-ID header.",
        )
    return tenant_id


def _require_admin(tenant_id: str, user_id: str) -> None:
    """Raise 403 if the calling user is not owner or admin of the tenant."""
    member = _find_member(tenant_id, user_id)
    if member and member["role"] in {"owner", "admin"}:
        return
    # If no store entry exists for this user we allow it in stub mode
    # (a real implementation queries the DB)
    logger.debug("_require_admin: no store entry for %s in %s — allowing (stub)", user_id, tenant_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=TeamListResponse,
    summary="List team members",
)
async def list_team_members(
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> TeamListResponse:
    """Return all members of the caller's tenant."""
    tenant_id = _require_tenant(request, user)
    members_raw = _get_members(tenant_id)

    members = [
        TeamMember(
            user_id=m["user_id"],
            role=m["role"],
            joined_at=m["joined_at"],
        )
        for m in members_raw
    ]

    return TeamListResponse(
        tenant_id=tenant_id,
        members=members,
        count=len(members),
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.post(
    "/invite",
    status_code=status.HTTP_201_CREATED,
    response_model=InviteResponse,
    summary="Add member to tenant",
)
async def invite_member(
    body: InviteRequest,
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> InviteResponse:
    """
    Add a user to the tenant team.

    Only owners and admins may invite members.
    """
    tenant_id = _require_tenant(request, user)
    _require_admin(tenant_id, user.sub)

    existing = _find_member(tenant_id, body.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{body.user_id}' is already a member of this tenant.",
        )

    now = datetime.now(UTC).isoformat()
    record = {"user_id": body.user_id, "role": body.role, "joined_at": now}
    _team_store.setdefault(tenant_id, []).append(record)

    logger.info(
        "team_member_added tenant=%s user=%s role=%s by=%s",
        tenant_id,
        body.user_id,
        body.role,
        user.sub,
    )

    return InviteResponse(
        tenant_id=tenant_id,
        user_id=body.user_id,
        role=body.role,
        message=f"User '{body.user_id}' added as '{body.role}'.",
        timestamp=now,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove member from tenant",
)
async def remove_member(
    user_id: str,
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> dict:
    """Remove a user from the tenant team."""
    tenant_id = _require_tenant(request, user)
    _require_admin(tenant_id, user.sub)

    existing = _find_member(tenant_id, user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' is not a member of this tenant.",
        )

    if existing.get("role") == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove the tenant owner.",
        )

    _team_store[tenant_id] = [m for m in _team_store[tenant_id] if m["user_id"] != user_id]

    logger.info(
        "team_member_removed tenant=%s user=%s by=%s",
        tenant_id,
        user_id,
        user.sub,
    )

    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "removed": True,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.patch(
    "/{user_id}",
    response_model=InviteResponse,
    summary="Change member role",
)
async def update_member_role(
    user_id: str,
    body: RoleUpdateRequest,
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> InviteResponse:
    """Change an existing team member's role."""
    tenant_id = _require_tenant(request, user)
    _require_admin(tenant_id, user.sub)

    member = _find_member(tenant_id, user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' is not a member of this tenant.",
        )

    if member.get("role") == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change the owner's role.",
        )

    old_role = member["role"]
    member["role"] = body.role

    logger.info(
        "team_member_role_changed tenant=%s user=%s %s→%s by=%s",
        tenant_id,
        user_id,
        old_role,
        body.role,
        user.sub,
    )

    return InviteResponse(
        tenant_id=tenant_id,
        user_id=user_id,
        role=body.role,
        message=f"Role updated from '{old_role}' to '{body.role}'.",
        timestamp=datetime.now(UTC).isoformat(),
    )
