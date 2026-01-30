"""Elementor 3D Integration API.

Provides endpoints for integrating 3D models with WordPress Elementor widgets.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from security.jwt_oauth2_auth import RoleChecker, UserRole

elementor_3d_router = APIRouter(tags=["elementor-3d"])

# Role-based access control
require_admin = RoleChecker([UserRole.ADMIN])
require_developer = RoleChecker([UserRole.ADMIN, UserRole.DEVELOPER])


class ElementorWidgetConfig(BaseModel):
    """Configuration for Elementor 3D widget."""

    widget_id: str = Field(..., description="Unique widget identifier")
    model_url: str = Field(..., description="URL to 3D model (GLB/GLTF)")
    thumbnail_url: str | None = Field(None, description="Preview thumbnail URL")
    autoplay: bool = Field(True, description="Auto-rotate model")
    background_color: str = Field("#ffffff", description="Widget background color")


class ElementorWidgetResponse(BaseModel):
    """Response for widget configuration."""

    widget_id: str
    shortcode: str
    embed_code: str


@elementor_3d_router.get("/widgets", summary="List 3D widgets")
async def list_widgets(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(require_developer),
):
    """List all Elementor 3D widgets."""
    # TODO: Implement actual widget listing from database
    return {"widgets": [], "total": 0, "skip": skip, "limit": limit}


@elementor_3d_router.post(
    "/widgets",
    response_model=ElementorWidgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create 3D widget",
)
async def create_widget(
    config: ElementorWidgetConfig,
    current_user: dict = Depends(require_developer),
):
    """Create a new Elementor 3D widget configuration."""
    # Generate shortcode for WordPress
    shortcode = f'[skyyrose_3d id="{config.widget_id}" model="{config.model_url}"]'

    # Generate embed code
    embed_code = f"""
<div id="elementor-3d-{config.widget_id}"
     data-model="{config.model_url}"
     data-thumbnail="{config.thumbnail_url or ''}"
     data-autoplay="{str(config.autoplay).lower()}"
     data-bg-color="{config.background_color}"
     class="skyyrose-3d-viewer">
</div>
""".strip()

    return ElementorWidgetResponse(
        widget_id=config.widget_id,
        shortcode=shortcode,
        embed_code=embed_code,
    )


@elementor_3d_router.get("/widgets/{widget_id}", summary="Get widget configuration")
async def get_widget(
    widget_id: str,
    current_user: dict = Depends(require_developer),
):
    """Get configuration for a specific widget."""
    # TODO: Implement actual widget retrieval from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Widget {widget_id} not found",
    )


@elementor_3d_router.delete(
    "/widgets/{widget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete widget",
)
async def delete_widget(
    widget_id: str,
    current_user: dict = Depends(require_admin),
):
    """Delete an Elementor 3D widget."""
    # TODO: Implement actual widget deletion
    return None
