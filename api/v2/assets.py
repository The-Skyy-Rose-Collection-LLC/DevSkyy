"""
Enterprise API v2 — Asset Management

Provides read and delete access to generated assets (renders, 3D models,
social packs, copy, character sheets). Assets are tracked via Redis
metadata keys written by the pipeline consumer.

Prefix: /api/v2/assets
Auth:   X-API-Key header (matches v1 pattern)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["Assets v2"])

# ---------------------------------------------------------------------------
# Redis key constants
# ---------------------------------------------------------------------------

_ASSET_KEY_PREFIX = "elite_studio:v2:asset:"
_RESULT_KEY_PREFIX = "elite_studio:result:"

# Valid asset types surfaced by the pipeline
_VALID_ASSET_TYPES = frozenset({"render", "3d-model", "social-pack", "copy", "character-sheet"})


# ---------------------------------------------------------------------------
# Auth dependency (mirrors v1)
# ---------------------------------------------------------------------------


def _get_api_key_dependency():
    async def _check_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
        expected = os.getenv("API_KEY", "")
        if not expected:
            return None
        if x_api_key != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key header",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        return x_api_key

    return _check_api_key


_api_key_dep = _get_api_key_dependency()


# ---------------------------------------------------------------------------
# Pydantic V2 models
# ---------------------------------------------------------------------------


class AssetResponse(BaseModel):
    asset_id: str
    operation_id: str
    sku: str
    asset_type: str  # "render", "3d-model", "social-pack", "copy", "character-sheet"
    file_path: str
    created_at: str
    size_bytes: int = 0


class AssetListResponse(BaseModel):
    assets: list[AssetResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------------


def _get_redis() -> Any | None:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis as redis_lib

        r = redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=3)
        r.ping()
        return r
    except Exception as exc:
        logger.warning("assets v2: Redis unavailable — %s", exc)
        return None


def _require_redis() -> Any:
    r = _get_redis()
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable — cannot process request",
        )
    return r


def _fetch_asset(r: Any, asset_id: str) -> AssetResponse | None:
    key = f"{_ASSET_KEY_PREFIX}{asset_id}"
    raw = r.get(key)
    if not raw:
        return None
    try:
        return AssetResponse.model_validate_json(raw)
    except Exception as exc:
        logger.warning("Failed to deserialise asset %s: %s", asset_id, exc)
        return None


def _file_size(file_path: str) -> int:
    """Return file size in bytes, 0 if not accessible."""
    try:
        return Path(file_path).stat().st_size
    except OSError:
        return 0


def _collect_assets_from_results(r: Any) -> list[AssetResponse]:
    """
    Derive asset records from legacy v1 result keys for backward compatibility.

    The pipeline consumer stores EliteStudioJobResult objects. We extract
    output_paths from those results and synthesise AssetResponse objects.
    """
    import json

    assets: list[AssetResponse] = []
    try:
        keys = r.keys(f"{_RESULT_KEY_PREFIX}*")
    except Exception:
        return assets

    for key in keys:
        raw = r.get(key)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        job_id = data.get("job_id", "")
        sku = data.get("sku", "")
        completed_at = data.get("completed_at", "")
        output_paths: list[str] = data.get("output_paths", [])

        for path in output_paths:
            if not path:
                continue
            # Derive asset type from file path suffix
            asset_type = _infer_asset_type(path)
            asset_id = f"{job_id}:{Path(path).name}"
            assets.append(
                AssetResponse(
                    asset_id=asset_id,
                    operation_id=job_id,
                    sku=sku,
                    asset_type=asset_type,
                    file_path=path,
                    created_at=completed_at,
                    size_bytes=_file_size(path),
                )
            )
    return assets


def _infer_asset_type(path: str) -> str:
    """Guess asset type from file path."""
    lower = path.lower()
    if any(ext in lower for ext in (".glb", ".obj", ".fbx", ".stl", ".usdz")):
        return "3d-model"
    if "social" in lower:
        return "social-pack"
    if "copy" in lower or lower.endswith(".txt") or lower.endswith(".md"):
        return "copy"
    if "character" in lower or "sheet" in lower:
        return "character-sheet"
    return "render"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=AssetListResponse,
    summary="List assets (filterable by sku, asset_type)",
)
async def list_assets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sku: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    _auth=Depends(_api_key_dep),
):
    """List generated assets.

    Combines assets from the dedicated v2 asset registry with legacy
    v1 result records for full backward compatibility.
    Filters: ``sku``, ``asset_type``.
    """
    if asset_type and asset_type not in _VALID_ASSET_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"asset_type must be one of {sorted(_VALID_ASSET_TYPES)}",
        )

    r = _require_redis()

    assets: list[AssetResponse] = []

    # Collect v2 native assets
    try:
        keys = r.keys(f"{_ASSET_KEY_PREFIX}*")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {exc}",
        ) from exc

    for key in keys:
        raw = r.get(key)
        if not raw:
            continue
        try:
            assets.append(AssetResponse.model_validate_json(raw))
        except Exception:
            continue

    # Merge in legacy result-derived assets
    legacy_assets = _collect_assets_from_results(r)
    # De-duplicate by asset_id
    existing_ids = {a.asset_id for a in assets}
    for asset in legacy_assets:
        if asset.asset_id not in existing_ids:
            assets.append(asset)
            existing_ids.add(asset.asset_id)

    # Apply filters
    if sku:
        assets = [a for a in assets if a.sku == sku.lower()]
    if asset_type:
        assets = [a for a in assets if a.asset_type == asset_type]

    assets.sort(key=lambda a: a.created_at, reverse=True)
    total = len(assets)
    start = (page - 1) * page_size
    paginated = assets[start : start + page_size]

    return AssetListResponse(assets=paginated, total=total, page=page, page_size=page_size)


@router.get(
    "/{asset_id:path}",
    response_model=AssetResponse,
    summary="Get asset metadata by ID",
)
async def get_asset(
    asset_id: str,
    _auth=Depends(_api_key_dep),
):
    """Return metadata for a single asset.

    Note: This endpoint returns metadata only, not the binary file content.
    """
    r = _require_redis()
    asset = _fetch_asset(r, asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset not found: {asset_id}",
        )
    return asset


@router.delete(
    "/{asset_id:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an asset",
)
async def delete_asset(
    asset_id: str,
    _auth=Depends(_api_key_dep),
):
    """Delete an asset's metadata record from Redis.

    Does not delete the underlying file from disk/storage.
    Returns 404 if the asset record does not exist.
    """
    r = _require_redis()
    key = f"{_ASSET_KEY_PREFIX}{asset_id}"
    deleted = r.delete(key)
    if not deleted:
        # Check if it exists in legacy results
        legacy_assets = _collect_assets_from_results(r)
        if not any(a.asset_id == asset_id for a in legacy_assets):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset not found: {asset_id}",
            )
    return None
