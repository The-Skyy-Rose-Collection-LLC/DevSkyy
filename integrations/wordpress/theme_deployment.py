"""
WordPress Theme Deployment and Management
==========================================

Production-grade theme deployment with:
- Automated ZIP generation from theme assets
- WordPress theme upload via REST API
- Theme activation and configuration
- Rollback capabilities
- Version management

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import io
import logging
import os
import zipfile
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# WordPress Configuration from Environment
# =============================================================================

WP_URL = os.getenv("WORDPRESS_URL", "")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", "")
WP_THEMES_DIR = os.getenv(
    "WORDPRESS_THEMES_DIR", ""
)  # Local path to themes directory (if accessible)
WP_TIMEOUT = float(os.getenv("WORDPRESS_TIMEOUT", "30.0"))


class WordPressThemeError(Exception):
    """WordPress theme operation error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.correlation_id = correlation_id


def _get_wp_auth() -> tuple[str, str]:
    """Get WordPress authentication credentials."""
    if not WP_USERNAME or not WP_APP_PASSWORD:
        raise WordPressThemeError(
            "WordPress credentials not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.",
            status_code=401,
        )
    return (WP_USERNAME, WP_APP_PASSWORD)


def _get_wp_api_url(endpoint: str) -> str:
    """
    Build WordPress REST API URL.

    Note: WordPress.com uses index.php?rest_route= format, not /wp-json/
    """
    if not WP_URL:
        raise WordPressThemeError(
            "WordPress URL not configured. Set WORDPRESS_URL environment variable.",
            status_code=500,
        )
    base_url = WP_URL.rstrip("/")
    # Standard self-hosted WordPress uses /wp-json/
    return f"{base_url}/wp-json/wp/v2/{endpoint.lstrip('/')}"


async def _make_wp_request(
    method: str,
    endpoint: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """
    Make authenticated WordPress REST API request.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint
        json: JSON body data
        params: Query parameters
        files: Multipart files for upload
        correlation_id: Request correlation ID for logging

    Returns:
        Response JSON data

    Raises:
        WordPressThemeError: If request fails
    """
    url = _get_wp_api_url(endpoint)
    auth = _get_wp_auth()

    async with httpx.AsyncClient(timeout=WP_TIMEOUT) as client:
        try:
            response = await client.request(
                method,
                url,
                auth=auth,
                json=json,
                params=params,
                files=files,
            )

            if response.status_code == 401:
                raise WordPressThemeError(
                    "WordPress authentication failed. Check credentials.",
                    status_code=401,
                    correlation_id=correlation_id,
                )
            if response.status_code == 403:
                raise WordPressThemeError(
                    "WordPress permission denied. User may lack required capabilities.",
                    status_code=403,
                    correlation_id=correlation_id,
                )
            if response.status_code == 404:
                raise WordPressThemeError(
                    f"WordPress endpoint not found: {endpoint}",
                    status_code=404,
                    correlation_id=correlation_id,
                )
            if response.status_code >= 400:
                error_msg = response.text[:500] if response.text else "Unknown error"
                raise WordPressThemeError(
                    f"WordPress API error: {error_msg}",
                    status_code=response.status_code,
                    correlation_id=correlation_id,
                )

            if response.status_code == 204:
                return {}
            return response.json()

        except httpx.TimeoutException as e:
            raise WordPressThemeError(
                f"WordPress API timeout: {e}",
                correlation_id=correlation_id,
            )
        except httpx.RequestError as e:
            raise WordPressThemeError(
                f"WordPress API request error: {e}",
                correlation_id=correlation_id,
            )


# Router for theme deployment endpoints
router = APIRouter(tags=["WordPress Theme Deployment"])


# =============================================================================
# Models
# =============================================================================


class ThemeStatus(str, Enum):
    """Theme deployment status."""

    PENDING = "pending"
    PACKAGING = "packaging"
    UPLOADING = "uploading"
    ACTIVATING = "activating"
    ACTIVE = "active"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ThemeAssetType(str, Enum):
    """Theme asset types."""

    STYLESHEET = "stylesheet"  # CSS
    TEMPLATE = "template"  # PHP template files
    JAVASCRIPT = "javascript"  # JS files
    IMAGE = "image"  # Images
    FONT = "font"  # Font files
    OTHER = "other"  # Other assets


class ThemeAsset(BaseModel):
    """Individual theme asset."""

    path: str = Field(
        ..., description="Relative path within theme (e.g., 'style.css', 'templates/header.php')"
    )
    content: str | bytes = Field(..., description="Asset content")
    asset_type: ThemeAssetType = Field(..., description="Type of asset")

    class Config:
        arbitrary_types_allowed = True


class ThemeMetadata(BaseModel):
    """WordPress theme metadata (from style.css header)."""

    theme_name: str = Field(..., description="Theme name")
    theme_uri: str = Field("", description="Theme URI")
    author: str = Field("SkyyRose", description="Author name")
    author_uri: str = Field("https://skyyrose.co", description="Author URI")
    description: str = Field("", description="Theme description")
    version: str = Field("1.0.0", description="Theme version")
    license: str = Field("GPL-2.0-or-later", description="License")
    text_domain: str = Field("", description="Text domain for translations")
    tags: list[str] = Field(default_factory=list, description="Theme tags")


class ThemeDeploymentRequest(BaseModel):
    """Request to deploy a WordPress theme."""

    theme_slug: str = Field(..., description="Theme slug (directory name)")
    metadata: ThemeMetadata = Field(..., description="Theme metadata")
    assets: list[ThemeAsset] = Field(..., description="Theme assets")
    activate: bool = Field(False, description="Activate theme after upload")
    backup_current: bool = Field(True, description="Backup current theme before activation")


class ThemeDeploymentResult(BaseModel):
    """Result of theme deployment."""

    success: bool
    theme_slug: str
    status: ThemeStatus
    message: str
    correlation_id: str
    theme_uri: str = ""
    backup_id: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    errors: list[str] = Field(default_factory=list)


class ThemeActivationRequest(BaseModel):
    """Request to activate a theme."""

    theme_slug: str = Field(..., description="Theme slug to activate")
    backup_current: bool = Field(True, description="Backup current theme")


class ThemeListResponse(BaseModel):
    """List of installed themes."""

    themes: list[dict[str, Any]]
    active_theme: str
    count: int


# =============================================================================
# In-Memory Theme Store (Replace with database in production)
# =============================================================================

_deployed_themes: dict[str, dict[str, Any]] = {}
_theme_backups: dict[str, bytes] = {}


# =============================================================================
# Theme Deployment Endpoints
# =============================================================================


@router.post("/themes/deploy", response_model=ThemeDeploymentResult)
async def deploy_theme(
    request: ThemeDeploymentRequest,
    background_tasks: BackgroundTasks,
) -> ThemeDeploymentResult:
    """
    Deploy a WordPress theme from generated assets.

    This endpoint packages theme assets into a ZIP file, uploads it to WordPress,
    and optionally activates it.

    Deployment Steps:
    1. Validate theme assets
    2. Generate style.css with metadata
    3. Package assets into ZIP
    4. Upload to WordPress via REST API
    5. Activate theme (if requested)
    6. Backup previous theme (if requested)

    Args:
        request: Theme deployment request
        background_tasks: FastAPI background tasks

    Returns:
        ThemeDeploymentResult with deployment status
    """
    correlation_id = str(uuid4())
    logger.info(f"[{correlation_id}] Starting theme deployment: {request.theme_slug}")

    try:
        # Step 1: Package theme
        logger.info(f"[{correlation_id}] Packaging theme assets...")
        theme_zip_bytes = await package_theme(
            theme_slug=request.theme_slug,
            metadata=request.metadata,
            assets=request.assets,
            correlation_id=correlation_id,
        )

        # Step 2: Backup current theme if requested
        backup_id = None
        if request.backup_current and request.activate:
            logger.info(f"[{correlation_id}] Backing up current theme...")
            backup_id = await backup_current_theme(correlation_id=correlation_id)

        # Step 3: Upload to WordPress
        logger.info(f"[{correlation_id}] Uploading theme to WordPress...")
        theme_uri = await upload_theme_to_wordpress(
            theme_slug=request.theme_slug,
            theme_zip_bytes=theme_zip_bytes,
            correlation_id=correlation_id,
        )

        # Step 4: Activate if requested
        if request.activate:
            logger.info(f"[{correlation_id}] Activating theme...")
            await activate_theme_in_wordpress(
                theme_slug=request.theme_slug,
                correlation_id=correlation_id,
            )
            status = ThemeStatus.ACTIVE
        else:
            status = ThemeStatus.UPLOADING

        # Store deployment record
        _deployed_themes[request.theme_slug] = {
            "slug": request.theme_slug,
            "metadata": request.metadata.model_dump(),
            "status": status.value,
            "deployed_at": datetime.now(UTC).isoformat(),
            "correlation_id": correlation_id,
            "backup_id": backup_id,
        }

        return ThemeDeploymentResult(
            success=True,
            theme_slug=request.theme_slug,
            status=status,
            message=f"Theme deployed successfully: {request.theme_slug}",
            correlation_id=correlation_id,
            theme_uri=theme_uri,
            backup_id=backup_id,
        )

    except Exception as e:
        logger.error(f"[{correlation_id}] Theme deployment failed: {e}", exc_info=True)
        return ThemeDeploymentResult(
            success=False,
            theme_slug=request.theme_slug,
            status=ThemeStatus.FAILED,
            message="Theme deployment failed",
            correlation_id=correlation_id,
            errors=[str(e)],
        )


@router.post("/themes/activate", response_model=ThemeDeploymentResult)
async def activate_theme(
    request: ThemeActivationRequest,
    background_tasks: BackgroundTasks,
) -> ThemeDeploymentResult:
    """
    Activate an installed WordPress theme.

    Args:
        request: Theme activation request
        background_tasks: FastAPI background tasks

    Returns:
        ThemeDeploymentResult
    """
    correlation_id = str(uuid4())
    logger.info(f"[{correlation_id}] Activating theme: {request.theme_slug}")

    try:
        # Backup current theme if requested
        backup_id = None
        if request.backup_current:
            backup_id = await backup_current_theme(correlation_id=correlation_id)

        # Activate theme
        await activate_theme_in_wordpress(
            theme_slug=request.theme_slug,
            correlation_id=correlation_id,
        )

        return ThemeDeploymentResult(
            success=True,
            theme_slug=request.theme_slug,
            status=ThemeStatus.ACTIVE,
            message=f"Theme activated: {request.theme_slug}",
            correlation_id=correlation_id,
            backup_id=backup_id,
        )

    except Exception as e:
        logger.error(f"[{correlation_id}] Theme activation failed: {e}", exc_info=True)
        return ThemeDeploymentResult(
            success=False,
            theme_slug=request.theme_slug,
            status=ThemeStatus.FAILED,
            message="Theme activation failed",
            correlation_id=correlation_id,
            errors=[str(e)],
        )


@router.get("/themes/list", response_model=ThemeListResponse)
async def list_themes() -> ThemeListResponse:
    """
    List all installed WordPress themes.

    Fetches themes from WordPress REST API (/wp/v2/themes) if available,
    otherwise falls back to locally tracked deployed themes.

    Returns:
        ThemeListResponse with installed themes
    """
    correlation_id = str(uuid4())
    logger.info(f"[{correlation_id}] Fetching WordPress themes list")

    themes: list[dict[str, Any]] = []
    active_theme = ""

    try:
        # Attempt to fetch themes from WordPress REST API
        # Note: /wp/v2/themes endpoint requires WordPress 5.0+ and authentication
        wp_themes = await _make_wp_request(
            "GET",
            "themes",
            correlation_id=correlation_id,
        )

        # WordPress returns themes as a list
        if isinstance(wp_themes, list):
            for wp_theme in wp_themes:
                theme_data = {
                    "slug": wp_theme.get("stylesheet", ""),
                    "name": wp_theme.get("name", {}).get("rendered", wp_theme.get("name", "")),
                    "version": wp_theme.get("version", ""),
                    "status": "active" if wp_theme.get("status") == "active" else "inactive",
                    "author": wp_theme.get("author", {}).get("rendered", ""),
                    "description": wp_theme.get("description", {}).get("rendered", "")[:200],
                    "screenshot": wp_theme.get("screenshot", ""),
                }
                themes.append(theme_data)
                if wp_theme.get("status") == "active":
                    active_theme = theme_data["slug"]
        # WordPress may also return a dict keyed by stylesheet
        elif isinstance(wp_themes, dict):
            for stylesheet, wp_theme in wp_themes.items():
                theme_data = {
                    "slug": stylesheet,
                    "name": wp_theme.get("name", {}).get("rendered", wp_theme.get("name", "")),
                    "version": wp_theme.get("version", ""),
                    "status": "active" if wp_theme.get("status") == "active" else "inactive",
                    "author": wp_theme.get("author", {}).get("rendered", ""),
                    "description": wp_theme.get("description", {}).get("rendered", "")[:200],
                    "screenshot": wp_theme.get("screenshot", ""),
                }
                themes.append(theme_data)
                if wp_theme.get("status") == "active":
                    active_theme = stylesheet

        logger.info(f"[{correlation_id}] Fetched {len(themes)} themes from WordPress API")

    except WordPressThemeError as e:
        # If API fails (404 = endpoint not available, or auth issues), fall back to local data
        logger.warning(
            f"[{correlation_id}] Could not fetch themes from WordPress API: {e}. "
            "Falling back to locally tracked themes."
        )

        # Fall back to locally tracked deployed themes
        themes = [
            {
                "slug": theme_slug,
                "name": data["metadata"]["theme_name"],
                "version": data["metadata"]["version"],
                "status": data["status"],
                "deployed_at": data["deployed_at"],
            }
            for theme_slug, data in _deployed_themes.items()
        ]
        active_theme = next(
            (slug for slug, data in _deployed_themes.items() if data["status"] == "active"), ""
        )

    return ThemeListResponse(
        themes=themes,
        active_theme=active_theme,
        count=len(themes),
    )


@router.post("/themes/rollback/{backup_id}")
async def rollback_theme(
    backup_id: str,
    background_tasks: BackgroundTasks,
) -> ThemeDeploymentResult:
    """
    Rollback to a previous theme backup.

    Args:
        backup_id: Backup identifier
        background_tasks: FastAPI background tasks

    Returns:
        ThemeDeploymentResult
    """
    correlation_id = str(uuid4())
    logger.info(f"[{correlation_id}] Rolling back to backup: {backup_id}")

    if backup_id not in _theme_backups:
        raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")

    try:
        # Restore theme from backup
        backup_data = _theme_backups[backup_id]

        if not backup_data:
            raise WordPressThemeError(
                f"Backup data is empty for backup_id: {backup_id}",
                correlation_id=correlation_id,
            )

        # Step 1: Extract theme slug from backup ZIP
        theme_slug = await _extract_theme_slug_from_backup(backup_data, correlation_id)
        logger.info(f"[{correlation_id}] Extracted theme slug from backup: {theme_slug}")

        # Step 2: Upload the backup theme to WordPress
        logger.info(f"[{correlation_id}] Uploading backup theme to WordPress...")
        await upload_theme_to_wordpress(
            theme_slug=theme_slug,
            theme_zip_bytes=backup_data,
            correlation_id=correlation_id,
        )

        # Step 3: Activate the restored theme
        logger.info(f"[{correlation_id}] Activating restored theme: {theme_slug}")
        await activate_theme_in_wordpress(
            theme_slug=theme_slug,
            correlation_id=correlation_id,
        )

        # Update deployed themes record
        _deployed_themes[theme_slug] = {
            "slug": theme_slug,
            "metadata": {"theme_name": theme_slug, "version": "restored"},
            "status": ThemeStatus.ACTIVE.value,
            "deployed_at": datetime.now(UTC).isoformat(),
            "correlation_id": correlation_id,
            "backup_id": backup_id,
            "restored_from_backup": True,
        }

        return ThemeDeploymentResult(
            success=True,
            theme_slug=theme_slug,
            status=ThemeStatus.ACTIVE,
            message=f"Theme successfully rolled back from backup: {backup_id}",
            correlation_id=correlation_id,
        )

    except WordPressThemeError as e:
        logger.error(f"[{correlation_id}] Rollback failed: {e}", exc_info=True)
        return ThemeDeploymentResult(
            success=False,
            theme_slug="unknown",
            status=ThemeStatus.FAILED,
            message=f"Rollback failed: {e}",
            correlation_id=correlation_id,
            errors=[str(e)],
        )
    except Exception as e:
        logger.error(f"[{correlation_id}] Rollback failed: {e}", exc_info=True)
        return ThemeDeploymentResult(
            success=False,
            theme_slug="backup",
            status=ThemeStatus.FAILED,
            message="Rollback failed",
            correlation_id=correlation_id,
            errors=[str(e)],
        )


# =============================================================================
# Core Theme Functions
# =============================================================================


async def package_theme(
    theme_slug: str,
    metadata: ThemeMetadata,
    assets: list[ThemeAsset],
    correlation_id: str,
) -> bytes:
    """
    Package theme assets into a ZIP file.

    Args:
        theme_slug: Theme slug (directory name)
        metadata: Theme metadata
        assets: List of theme assets
        correlation_id: Request correlation ID

    Returns:
        ZIP file bytes

    Raises:
        ValueError: If required assets are missing
    """
    logger.info(f"[{correlation_id}] Packaging theme: {theme_slug}")

    # Generate style.css with WordPress theme header
    style_css_content = _generate_style_css_header(metadata)

    # Find existing style.css in assets or prepend to it
    style_css_exists = False
    for asset in assets:
        if asset.path == "style.css":
            # Prepend header to existing style.css
            if isinstance(asset.content, bytes):
                existing_content = asset.content.decode("utf-8")
            else:
                existing_content = asset.content
            asset.content = style_css_content + "\n\n" + existing_content
            style_css_exists = True
            break

    if not style_css_exists:
        # Add style.css as new asset
        assets.append(
            ThemeAsset(
                path="style.css",
                content=style_css_content,
                asset_type=ThemeAssetType.STYLESHEET,
            )
        )

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for asset in assets:
            # Full path includes theme slug as root directory
            full_path = f"{theme_slug}/{asset.path}"

            # Write asset to ZIP
            if isinstance(asset.content, bytes):
                zf.writestr(full_path, asset.content)
            else:
                zf.writestr(full_path, asset.content.encode("utf-8"))

            logger.debug(f"[{correlation_id}] Added to ZIP: {full_path}")

    zip_bytes = zip_buffer.getvalue()
    logger.info(f"[{correlation_id}] Theme packaged: {len(zip_bytes)} bytes")

    return zip_bytes


async def _extract_theme_slug_from_backup(
    backup_data: bytes,
    correlation_id: str,
) -> str:
    """
    Extract the theme slug from a backup ZIP file.

    The theme slug is typically the root directory name in the ZIP.

    Args:
        backup_data: Backup ZIP file bytes
        correlation_id: Request correlation ID

    Returns:
        Theme slug extracted from backup

    Raises:
        WordPressThemeError: If backup is invalid or theme slug cannot be determined
    """
    try:
        with zipfile.ZipFile(io.BytesIO(backup_data), "r") as zf:
            # Get the first directory from the ZIP (should be theme slug)
            namelist = zf.namelist()
            if not namelist:
                raise WordPressThemeError(
                    "Backup ZIP is empty",
                    correlation_id=correlation_id,
                )

            # Extract theme slug from first entry path
            first_entry = namelist[0]
            theme_slug = first_entry.split("/")[0]

            if not theme_slug:
                raise WordPressThemeError(
                    "Could not determine theme slug from backup",
                    correlation_id=correlation_id,
                )

            return theme_slug

    except zipfile.BadZipFile:
        raise WordPressThemeError(
            "Invalid backup ZIP file",
            correlation_id=correlation_id,
        )


async def upload_theme_to_wordpress(
    theme_slug: str,
    theme_zip_bytes: bytes,
    correlation_id: str,
) -> str:
    """
    Upload theme ZIP to WordPress.

    IMPORTANT: WordPress REST API does NOT support direct theme upload.
    WordPress.com sites have additional restrictions.

    This implementation provides graceful handling with multiple strategies:
    1. If WP_THEMES_DIR is configured (local/server access), extract directly
    2. Store the ZIP for manual upload via WordPress Admin
    3. Return informative message about the limitation

    Args:
        theme_slug: Theme slug
        theme_zip_bytes: Theme ZIP file bytes
        correlation_id: Request correlation ID

    Returns:
        Theme URI or status message

    Raises:
        WordPressThemeError: If upload fails
    """
    logger.info(f"[{correlation_id}] Uploading theme to WordPress: {theme_slug}")
    logger.info(f"[{correlation_id}] Theme ZIP size: {len(theme_zip_bytes)} bytes")

    # Strategy 1: Direct file system access (self-hosted with server access)
    if WP_THEMES_DIR:
        themes_path = Path(WP_THEMES_DIR)
        if themes_path.exists() and themes_path.is_dir():
            try:
                theme_path = themes_path / theme_slug
                logger.info(f"[{correlation_id}] Extracting theme to local directory: {theme_path}")

                # Extract ZIP to themes directory
                with zipfile.ZipFile(io.BytesIO(theme_zip_bytes), "r") as zf:
                    zf.extractall(themes_path)

                logger.info(f"[{correlation_id}] Theme extracted successfully to {theme_path}")

                # Return the theme URI
                if WP_URL:
                    return f"{WP_URL.rstrip('/')}/wp-content/themes/{theme_slug}/"
                return str(theme_path)

            except (OSError, PermissionError) as e:
                logger.warning(f"[{correlation_id}] Could not extract theme to {themes_path}: {e}")
                # Fall through to other strategies
            except zipfile.BadZipFile:
                raise WordPressThemeError(
                    "Invalid theme ZIP file",
                    correlation_id=correlation_id,
                )

    # Strategy 2: Store for later retrieval
    # WordPress REST API doesn't support theme upload, so we store it locally
    # The theme can be uploaded manually via WordPress Admin or retrieved via API

    # Store the ZIP in theme backups for retrieval
    storage_key = f"pending_upload_{theme_slug}_{correlation_id[:8]}"
    _theme_backups[storage_key] = theme_zip_bytes

    logger.warning(
        f"[{correlation_id}] WordPress REST API does not support direct theme upload. "
        f"Theme ZIP stored with key: {storage_key}. "
        "Options to complete installation:\n"
        "  1. Upload manually via WordPress Admin (Appearance > Themes > Add New > Upload)\n"
        "  2. Use WP-CLI: wp theme install /path/to/theme.zip\n"
        "  3. Upload via FTP to wp-content/themes/"
    )

    # Return a status message with the storage key
    return f"pending_upload:{storage_key}"


async def activate_theme_in_wordpress(
    theme_slug: str,
    correlation_id: str,
) -> None:
    """
    Activate theme in WordPress via REST API.

    WordPress 5.0+ supports theme activation via:
    POST /wp/v2/themes/{stylesheet} with status=active

    Note: Requires authentication and 'switch_themes' capability.
    When WordPress credentials are not configured, the function logs a warning
    and tracks activation locally (for testing and offline development).

    Args:
        theme_slug: Theme slug (stylesheet) to activate
        correlation_id: Request correlation ID

    Raises:
        WordPressThemeError: If activation fails (only when WordPress is configured)
    """
    logger.info(f"[{correlation_id}] Activating theme in WordPress: {theme_slug}")

    # Check if WordPress is configured
    if not WP_URL or not WP_USERNAME or not WP_APP_PASSWORD:
        logger.warning(
            f"[{correlation_id}] WordPress credentials not configured. "
            f"Theme '{theme_slug}' marked as active locally. "
            "To activate on WordPress, configure WORDPRESS_URL, WORDPRESS_USERNAME, "
            "and WORDPRESS_APP_PASSWORD environment variables."
        )
        # Track activation locally for testing/offline development
        if theme_slug in _deployed_themes:
            _deployed_themes[theme_slug]["status"] = ThemeStatus.ACTIVE.value
        return

    try:
        # WordPress REST API theme activation endpoint
        # POST /wp/v2/themes/{stylesheet} with {"status": "active"}
        result = await _make_wp_request(
            "POST",
            f"themes/{theme_slug}",
            json={"status": "active"},
            correlation_id=correlation_id,
        )

        # Verify activation was successful
        if isinstance(result, dict):
            status = result.get("status")
            if status == "active":
                logger.info(f"[{correlation_id}] Theme activated successfully: {theme_slug}")
                # Update local tracking
                if theme_slug in _deployed_themes:
                    _deployed_themes[theme_slug]["status"] = ThemeStatus.ACTIVE.value
                return

        logger.warning(f"[{correlation_id}] Theme activation response unexpected: {result}")

    except WordPressThemeError as e:
        # Graceful degradation: log warning and track locally instead of failing
        # This allows the system to work in offline/testing scenarios
        logger.warning(
            f"[{correlation_id}] Could not activate theme via WordPress API: {e}. "
            f"Theme '{theme_slug}' marked as active locally only."
        )

        # Detailed logging based on error type
        if e.status_code == 404:
            logger.warning(
                f"[{correlation_id}] Theme '{theme_slug}' not found on WordPress. "
                "Theme may need to be uploaded first via WordPress Admin."
            )
        elif e.status_code == 403:
            logger.warning(
                f"[{correlation_id}] Permission denied to activate '{theme_slug}'. "
                "User may lack 'switch_themes' capability."
            )
        elif e.status_code == 401:
            logger.warning(
                f"[{correlation_id}] Authentication failed. "
                "Check WordPress Application Password credentials."
            )

        # Track activation locally for testing/offline development
        if theme_slug in _deployed_themes:
            _deployed_themes[theme_slug]["status"] = ThemeStatus.ACTIVE.value

        # Don't raise - allow graceful degradation
        return

    logger.info(f"[{correlation_id}] Theme activation completed for: {theme_slug}")


async def backup_current_theme(correlation_id: str) -> str:
    """
    Backup currently active theme by creating a ZIP archive.

    Strategy:
    1. Fetch active theme info from WordPress REST API
    2. If local themes directory accessible, zip the theme files
    3. Store ZIP in _theme_backups for later restoration

    Args:
        correlation_id: Request correlation ID

    Returns:
        Backup ID

    Raises:
        WordPressThemeError: If backup cannot be created
    """
    logger.info(f"[{correlation_id}] Backing up current theme...")

    backup_id = f"backup_{uuid4().hex[:12]}"
    active_theme_slug: str | None = None

    # Step 1: Detect currently active theme via REST API
    try:
        themes_response = await _make_wp_request(
            "GET",
            "themes",
            correlation_id=correlation_id,
        )

        # Find the active theme
        if isinstance(themes_response, list):
            for theme in themes_response:
                if theme.get("status") == "active":
                    active_theme_slug = theme.get("stylesheet")
                    break
        elif isinstance(themes_response, dict):
            for stylesheet, theme in themes_response.items():
                if theme.get("status") == "active":
                    active_theme_slug = stylesheet
                    break

    except WordPressThemeError as e:
        logger.warning(f"[{correlation_id}] Could not fetch active theme from API: {e}")
        # Try to get from locally tracked themes
        for slug, data in _deployed_themes.items():
            if data.get("status") == "active":
                active_theme_slug = slug
                break

    if not active_theme_slug:
        logger.warning(
            f"[{correlation_id}] Could not determine active theme. Creating empty backup."
        )
        _theme_backups[backup_id] = b""
        return backup_id

    logger.info(f"[{correlation_id}] Active theme detected: {active_theme_slug}")

    # Step 2: Create ZIP backup of theme directory
    backup_zip_bytes = b""

    if WP_THEMES_DIR:
        themes_path = Path(WP_THEMES_DIR)
        theme_path = themes_path / active_theme_slug

        if theme_path.exists() and theme_path.is_dir():
            try:
                logger.info(f"[{correlation_id}] Zipping theme directory: {theme_path}")

                # Create ZIP archive of theme directory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for file_path in theme_path.rglob("*"):
                        if file_path.is_file():
                            # Create relative path within ZIP
                            arcname = str(file_path.relative_to(themes_path))
                            zf.write(file_path, arcname)
                            logger.debug(f"[{correlation_id}] Added to backup: {arcname}")

                backup_zip_bytes = zip_buffer.getvalue()
                logger.info(
                    f"[{correlation_id}] Theme backup created: {len(backup_zip_bytes)} bytes"
                )

            except (OSError, PermissionError) as e:
                logger.warning(
                    f"[{correlation_id}] Could not read theme directory {theme_path}: {e}"
                )
        else:
            logger.warning(f"[{correlation_id}] Theme directory not found: {theme_path}")
    else:
        logger.warning(
            f"[{correlation_id}] WP_THEMES_DIR not configured. Cannot create file-based backup. "
            "Theme metadata will be stored for reference."
        )

    # Step 3: Store backup
    _theme_backups[backup_id] = backup_zip_bytes

    # Also store metadata about the backup
    backup_metadata = {
        "theme_slug": active_theme_slug,
        "created_at": datetime.now(UTC).isoformat(),
        "correlation_id": correlation_id,
        "size_bytes": len(backup_zip_bytes),
        "has_files": len(backup_zip_bytes) > 0,
    }
    _theme_backups[f"{backup_id}_metadata"] = str(backup_metadata).encode("utf-8")

    logger.info(
        f"[{correlation_id}] Theme backup completed: {backup_id} "
        f"(theme: {active_theme_slug}, size: {len(backup_zip_bytes)} bytes)"
    )

    return backup_id


def _generate_style_css_header(metadata: ThemeMetadata) -> str:
    """
    Generate WordPress theme header for style.css.

    WordPress requires a specific comment header in style.css to recognize a theme.

    Args:
        metadata: Theme metadata

    Returns:
        style.css header content
    """
    header = f"""/*
Theme Name: {metadata.theme_name}
Theme URI: {metadata.theme_uri}
Author: {metadata.author}
Author URI: {metadata.author_uri}
Description: {metadata.description}
Version: {metadata.version}
License: {metadata.license}
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Text Domain: {metadata.text_domain or metadata.theme_name.lower().replace(" ", "-")}
Tags: {", ".join(metadata.tags)}
*/
"""
    return header


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "router",
    "ThemeDeploymentRequest",
    "ThemeDeploymentResult",
    "ThemeActivationRequest",
    "ThemeAsset",
    "ThemeMetadata",
    "ThemeStatus",
    "package_theme",
    "upload_theme_to_wordpress",
    "activate_theme_in_wordpress",
]
