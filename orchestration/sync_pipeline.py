"""
Asset Sync Pipeline
===================
Orchestrates synchronization between HuggingFace, DevSkyy, and WordPress.

This module provides:
- Round Table results → HuggingFace dataset export
- HuggingFace assets → WordPress media library sync
- Cross-system status tracking
- Automated sync scheduling

Architecture:
    Round Table Results → HuggingFace Dataset
                       ↓
    HuggingFace Spaces → DevSkyy (local cache)
                       ↓
    DevSkyy Assets → WordPress Media Library
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# =============================================================================
# Security Constants
# =============================================================================

# Maximum JSON file size to prevent memory exhaustion (10MB)
MAX_JSON_FILE_SIZE = 10 * 1024 * 1024
# Maximum items in sync operations
MAX_SYNC_ITEMS = 1000
# Maximum summary text length
MAX_SUMMARY_LENGTH = 500
# Timeout for external API calls (seconds)
API_TIMEOUT_SECONDS = 30

# =============================================================================
# Configuration
# =============================================================================

ROUND_TABLE_RESULTS_PATH = Path("assets/ai-enhanced-images/ROUND_TABLE_ELITE_RESULTS.json")
EXPORTS_DIR = Path("assets/exports")
SYNC_STATE_PATH = Path("data/sync_state.json")

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_ACCESS_TOKEN")
HF_USERNAME = os.getenv("HF_USERNAME", "damBruh")

WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")


# =============================================================================
# Security Helpers
# =============================================================================


def _safe_load_json(path: Path, max_size: int = MAX_JSON_FILE_SIZE) -> dict[str, Any]:
    """
    Safely load JSON file with size limits to prevent memory exhaustion.

    Args:
        path: Path to JSON file
        max_size: Maximum file size in bytes

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is too large or invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    file_size = path.stat().st_size
    if file_size > max_size:
        logger.warning(f"File too large: {path} ({file_size} bytes > {max_size})")
        raise ValueError(f"File exceeds maximum size of {max_size // (1024 * 1024)}MB")

    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        raise ValueError(f"Invalid JSON format: {e.msg}")


def _sanitize_text(text: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
    """Sanitize and truncate text for safe logging and storage."""
    if not isinstance(text, str):
        return ""
    # Remove control characters and truncate
    sanitized = "".join(c for c in text if c.isprintable() or c in "\n\t")
    return sanitized[:max_length]


# =============================================================================
# Data Models
# =============================================================================


class SyncDirection(str, Enum):
    """Synchronization direction."""

    RT_TO_HF = "round_table_to_huggingface"
    HF_TO_DEVSKYY = "huggingface_to_devskyy"
    DEVSKYY_TO_WP = "devskyy_to_wordpress"
    FULL = "full"


class SyncStatus(str, Enum):
    """Sync operation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class SyncRecord:
    """Record of a single sync operation."""

    id: str
    direction: SyncDirection
    status: SyncStatus
    started_at: str
    completed_at: str | None = None
    items_synced: int = 0
    items_failed: int = 0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class SystemStatus(BaseModel):
    """Status of a system in the sync chain."""

    system: str = Field(..., description="System name")
    available: bool = Field(..., description="Whether system is available")
    last_sync: str | None = Field(None, description="Last sync timestamp")
    items_count: int = Field(default=0, description="Number of items")
    error: str | None = Field(None, description="Error if unavailable")


class SyncPipelineStatus(BaseModel):
    """Overall sync pipeline status."""

    status: str = Field(..., description="Pipeline status")
    systems: list[SystemStatus] = Field(..., description="Individual system statuses")
    last_full_sync: str | None = Field(None, description="Last full sync timestamp")
    pending_syncs: int = Field(default=0, description="Number of pending sync items")
    recent_errors: list[str] = Field(default_factory=list, description="Recent errors")
    updated_at: str = Field(..., description="Status check timestamp")


class SyncTriggerResponse(BaseModel):
    """Response from triggering a sync operation."""

    success: bool = Field(..., description="Whether trigger succeeded")
    sync_id: str = Field(..., description="Sync operation ID")
    direction: str = Field(..., description="Sync direction")
    message: str = Field(..., description="Status message")


# =============================================================================
# Sync Pipeline Class
# =============================================================================


class AssetSyncPipeline:
    """
    Orchestrates asset synchronization across HuggingFace, DevSkyy, and WordPress.

    This pipeline manages:
    1. Exporting Round Table winning scene specs to HuggingFace datasets
    2. Downloading HuggingFace-enhanced assets to local storage
    3. Uploading local assets to WordPress media library
    4. Tracking sync state across all systems

    Example:
        pipeline = AssetSyncPipeline()

        # Check status
        status = await pipeline.get_status()

        # Trigger full sync
        result = await pipeline.sync(direction=SyncDirection.FULL)

        # Sync Round Table to HuggingFace
        result = await pipeline.sync_round_table_to_hf()
    """

    def __init__(self):
        """Initialize sync pipeline."""
        self._sync_records: list[SyncRecord] = []
        self._sync_state: dict[str, Any] = {}
        self._load_state()

    def _load_state(self) -> None:
        """Load sync state from disk with safe JSON loading."""
        if SYNC_STATE_PATH.exists():
            try:
                # Use safe JSON loading with smaller size limit for state file (1MB)
                self._sync_state = _safe_load_json(SYNC_STATE_PATH, max_size=1024 * 1024)
                logger.info(f"Loaded sync state from {SYNC_STATE_PATH}")
            except (FileNotFoundError, ValueError) as e:
                logger.error(f"Failed to load sync state: {e}")
                self._sync_state = {}
            except Exception as e:
                logger.error(f"Unexpected error loading sync state: {e}")
                self._sync_state = {}
        else:
            self._sync_state = {
                "last_full_sync": None,
                "systems": {},
                "records": [],
            }

    def _save_state(self) -> None:
        """Save sync state to disk."""
        try:
            SYNC_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(SYNC_STATE_PATH, "w") as f:
                json.dump(self._sync_state, f, indent=2)
            logger.debug(f"Saved sync state to {SYNC_STATE_PATH}")
        except Exception as e:
            logger.error(f"Failed to save sync state: {e}")

    def _generate_sync_id(self, direction: SyncDirection) -> str:
        """Generate unique sync operation ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"sync_{direction.value}_{timestamp}"

    async def get_status(self) -> SyncPipelineStatus:
        """
        Get current sync pipeline status.

        Returns:
            Status of all systems and pending operations
        """
        systems: list[SystemStatus] = []
        recent_errors: list[str] = []

        # Check Round Table results
        rt_available = ROUND_TABLE_RESULTS_PATH.exists()
        rt_count = 0
        if rt_available:
            try:
                with open(ROUND_TABLE_RESULTS_PATH) as f:
                    rt_data = json.load(f)
                    rt_count = len(rt_data.get("collections", {}))
            except Exception as e:
                recent_errors.append(f"RT read error: {str(e)}")

        systems.append(
            SystemStatus(
                system="round_table",
                available=rt_available,
                last_sync=self._sync_state.get("systems", {})
                .get("round_table", {})
                .get("last_sync"),
                items_count=rt_count,
                error=None if rt_available else "Results file not found",
            )
        )

        # Check HuggingFace
        hf_available = bool(HF_TOKEN)
        systems.append(
            SystemStatus(
                system="huggingface",
                available=hf_available,
                last_sync=self._sync_state.get("systems", {})
                .get("huggingface", {})
                .get("last_sync"),
                items_count=0,  # Would need API call to check
                error=None if hf_available else "HF_TOKEN not configured",
            )
        )

        # Check WordPress
        wp_available = bool(WP_URL and WP_APP_PASSWORD)
        systems.append(
            SystemStatus(
                system="wordpress",
                available=wp_available,
                last_sync=self._sync_state.get("systems", {}).get("wordpress", {}).get("last_sync"),
                items_count=0,  # Would need API call to check
                error=None if wp_available else "WordPress credentials not configured",
            )
        )

        # Check local exports
        exports_count = len(list(EXPORTS_DIR.glob("*.json"))) if EXPORTS_DIR.exists() else 0
        systems.append(
            SystemStatus(
                system="local_exports",
                available=True,
                last_sync=self._sync_state.get("systems", {})
                .get("local_exports", {})
                .get("last_sync"),
                items_count=exports_count,
            )
        )

        # Calculate overall status
        all_available = all(s.available for s in systems[:3])  # RT, HF, WP
        status = "healthy" if all_available else "degraded"

        return SyncPipelineStatus(
            status=status,
            systems=systems,
            last_full_sync=self._sync_state.get("last_full_sync"),
            pending_syncs=len([r for r in self._sync_records if r.status == SyncStatus.PENDING]),
            recent_errors=recent_errors[-5:],  # Last 5 errors
            updated_at=datetime.utcnow().isoformat(),
        )

    async def sync(self, direction: SyncDirection = SyncDirection.FULL) -> SyncTriggerResponse:
        """
        Trigger sync operation.

        Args:
            direction: Which direction to sync

        Returns:
            Trigger result with sync ID
        """
        sync_id = self._generate_sync_id(direction)

        logger.info(f"Sync triggered: {sync_id} ({direction.value})")

        try:
            if direction == SyncDirection.RT_TO_HF:
                result = await self.sync_round_table_to_hf()
            elif direction == SyncDirection.HF_TO_DEVSKYY:
                result = await self.sync_hf_to_devskyy()
            elif direction == SyncDirection.DEVSKYY_TO_WP:
                result = await self.sync_devskyy_to_wordpress()
            elif direction == SyncDirection.FULL:
                result = await self._full_sync()
            else:
                raise ValueError(f"Unknown sync direction: {direction}")

            return SyncTriggerResponse(
                success=True,
                sync_id=sync_id,
                direction=direction.value,
                message=f"Sync completed: {result.get('items_synced', 0)} items",
            )

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            return SyncTriggerResponse(
                success=False,
                sync_id=sync_id,
                direction=direction.value,
                message=f"Sync failed: {str(e)}",
            )

    async def sync_round_table_to_hf(self) -> dict[str, Any]:
        """
        Export Round Table results to HuggingFace dataset.

        Returns:
            Sync result with items count

        Raises:
            FileNotFoundError: If Round Table results not found
            ValueError: If results file is too large or invalid
        """
        logger.info("Starting Round Table → HuggingFace sync")

        # Use safe JSON loader with size limits
        rt_data = _safe_load_json(ROUND_TABLE_RESULTS_PATH)

        collections = rt_data.get("collections", {})

        if not collections:
            logger.warning("No collections found in Round Table results")
            return {"items_synced": 0, "error": "No collections"}

        # Prepare export data for HuggingFace dataset format
        export_items = []

        for collection_name, collection_data in collections.items():
            winner = collection_data.get("winner", {})

            if winner:
                export_items.append(
                    {
                        "collection": collection_name,
                        "provider": winner.get("provider", "unknown"),
                        "total_score": winner.get("total_score", 0.0),
                        "verdict": winner.get("verdict", "UNKNOWN"),
                        "scene_spec": json.dumps(winner.get("scene_spec", {})),
                        "summary": _sanitize_text(winner.get("summary", "")),  # Safe truncation
                        "prompt_quality": winner.get("prompt_quality", 0.0),
                        "execution_quality": winner.get("execution_quality", 0.0),
                        "brand_dna_alignment": winner.get("brand_dna_alignment", 0.0),
                    }
                )

        # Save to local export directory
        export_path = EXPORTS_DIR / "round_table_hf_export.json"
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        export_data = {
            "dataset_name": "skyyrose-scene-specs",
            "exported_at": datetime.utcnow().isoformat(),
            "source": str(ROUND_TABLE_RESULTS_PATH),
            "format": "huggingface_dataset",
            "items": export_items,
        }

        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(export_items)} items to {export_path}")

        # Update sync state
        self._sync_state.setdefault("systems", {})
        self._sync_state["systems"]["round_table"] = {
            "last_sync": datetime.utcnow().isoformat(),
            "items_synced": len(export_items),
        }
        self._save_state()

        # TODO: Actually upload to HuggingFace using huggingface_hub
        # from huggingface_hub import HfApi
        # api = HfApi(token=HF_TOKEN)
        # api.upload_file(...)

        return {
            "items_synced": len(export_items),
            "export_path": str(export_path),
            "collections": list(collections.keys()),
        }

    async def sync_hf_to_devskyy(self) -> dict[str, Any]:
        """
        Download HuggingFace assets to local storage.

        Returns:
            Sync result with items count
        """
        logger.info("Starting HuggingFace → DevSkyy sync")

        if not HF_TOKEN:
            raise ValueError("HF_TOKEN not configured")

        # TODO: Implement HuggingFace download
        # This would download:
        # - Dataset updates
        # - Model checkpoints
        # - Enhanced images

        # For now, just check if HF Spaces are accessible
        items_synced = 0

        # Update sync state
        self._sync_state.setdefault("systems", {})
        self._sync_state["systems"]["huggingface"] = {
            "last_sync": datetime.utcnow().isoformat(),
            "items_synced": items_synced,
        }
        self._save_state()

        return {"items_synced": items_synced, "message": "HF sync placeholder"}

    async def sync_devskyy_to_wordpress(self) -> dict[str, Any]:
        """
        Upload local assets to WordPress media library.

        Returns:
            Sync result with items count
        """
        logger.info("Starting DevSkyy → WordPress sync")

        if not WP_URL or not WP_APP_PASSWORD:
            raise ValueError("WordPress credentials not configured")

        # TODO: Implement WordPress upload
        # This would upload:
        # - Enhanced product images
        # - 3D models (GLB/USDZ)
        # - Scene specifications

        items_synced = 0

        # Update sync state
        self._sync_state.setdefault("systems", {})
        self._sync_state["systems"]["wordpress"] = {
            "last_sync": datetime.utcnow().isoformat(),
            "items_synced": items_synced,
        }
        self._save_state()

        return {"items_synced": items_synced, "message": "WordPress sync placeholder"}

    async def _full_sync(self) -> dict[str, Any]:
        """
        Execute full sync: RT → HF → DevSkyy → WP.

        Returns:
            Combined sync results
        """
        logger.info("Starting full sync pipeline")

        results = {
            "rt_to_hf": {},
            "hf_to_devskyy": {},
            "devskyy_to_wp": {},
        }

        total_synced = 0
        errors = []

        # Step 1: Round Table → HuggingFace
        try:
            results["rt_to_hf"] = await self.sync_round_table_to_hf()
            total_synced += results["rt_to_hf"].get("items_synced", 0)
        except Exception as e:
            logger.error(f"RT → HF sync failed: {e}")
            errors.append(f"RT→HF: {str(e)}")
            results["rt_to_hf"] = {"error": str(e)}

        # Step 2: HuggingFace → DevSkyy
        try:
            results["hf_to_devskyy"] = await self.sync_hf_to_devskyy()
            total_synced += results["hf_to_devskyy"].get("items_synced", 0)
        except Exception as e:
            logger.error(f"HF → DevSkyy sync failed: {e}")
            errors.append(f"HF→DS: {str(e)}")
            results["hf_to_devskyy"] = {"error": str(e)}

        # Step 3: DevSkyy → WordPress
        try:
            results["devskyy_to_wp"] = await self.sync_devskyy_to_wordpress()
            total_synced += results["devskyy_to_wp"].get("items_synced", 0)
        except Exception as e:
            logger.error(f"DevSkyy → WP sync failed: {e}")
            errors.append(f"DS→WP: {str(e)}")
            results["devskyy_to_wp"] = {"error": str(e)}

        # Update full sync timestamp
        self._sync_state["last_full_sync"] = datetime.utcnow().isoformat()
        self._save_state()

        logger.info(f"Full sync completed: {total_synced} items, {len(errors)} errors")

        return {
            "items_synced": total_synced,
            "results": results,
            "errors": errors,
        }


# =============================================================================
# Singleton Instance
# =============================================================================

_pipeline_instance: AssetSyncPipeline | None = None


def get_sync_pipeline() -> AssetSyncPipeline:
    """Get or create sync pipeline singleton."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = AssetSyncPipeline()
    return _pipeline_instance


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "AssetSyncPipeline",
    "SyncDirection",
    "SyncStatus",
    "SyncPipelineStatus",
    "SyncTriggerResponse",
    "get_sync_pipeline",
]
