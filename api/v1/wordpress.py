"""WordPress Integration API.

Provides endpoints for syncing content and media with WordPress.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from security.jwt_oauth2_auth import RoleChecker, UserRole

router = APIRouter(tags=["wordpress"], prefix="/wordpress")
require_developer = RoleChecker([UserRole.ADMIN, UserRole.DEVELOPER])


class WordPressSyncRequest(BaseModel):
    """Request to sync content to WordPress."""

    post_type: str = "post"
    title: str
    content: str
    status: str = "draft"


class WordPressSyncResponse(BaseModel):
    """Response from WordPress sync."""

    success: bool
    wordpress_id: int | None = None
    url: str | None = None
    error: str | None = None


@router.post("/sync", response_model=WordPressSyncResponse, summary="Sync to WordPress")
async def sync_to_wordpress(
    request: WordPressSyncRequest,
    current_user: dict = Depends(require_developer),
):
    """Sync content to WordPress site."""
    # TODO: Implement actual WordPress API integration
    return WordPressSyncResponse(
        success=False,
        error="WordPress sync not yet implemented",
    )


@router.get("/status", summary="Get WordPress connection status")
async def get_wordpress_status(
    current_user: dict = Depends(require_developer),
):
    """Check WordPress connection status."""
    return {
        "connected": False,
        "site_url": None,
        "version": None,
    }
