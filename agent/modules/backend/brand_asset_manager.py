from datetime import datetime
import json
import logging
import mimetypes
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class BrandAssetManager:
    """
    Brand Asset Management System for The Skyy Rose Collection.
    Handles upload, storage, and analysis of brand assets.
    """

    def __init__(self, storage_path: str = "brand_assets"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        # Create asset categories
        self.categories = {
            "logos": self.storage_path / "logos",
            "color_palettes": self.storage_path / "color_palettes",
            "typography": self.storage_path / "typography",
            "product_images": self.storage_path / "product_images",
            "marketing_materials": self.storage_path / "marketing_materials",
            "brand_guidelines": self.storage_path / "brand_guidelines",
            "seasonal_collections": self.storage_path / "seasonal_collections",
        }

        # Create category directories
        for category_path in self.categories.values():
            category_path.mkdir(exist_ok=True)

        self.metadata_file = self.storage_path / "asset_metadata.json"
        self._load_metadata()

        logger.info("🎨 Brand Asset Manager initialized")

    def _load_metadata(self):
        """Load asset metadata from storage."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "assets": {},
                "upload_history": [],
                "total_assets": 0,
                "last_updated": datetime.now().isoformat(),
            }

    def _save_metadata(self):
        """Save asset metadata to storage."""
        self.metadata["last_updated"] = datetime.now().isoformat()
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def upload_asset(
        self,
        file_data: bytes,
        filename: str,
        category: str,
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Upload a brand asset."""
        try:
            if category not in self.categories:
                return {"error": f"Invalid category. Available: {list(self.categories.keys())}"}

            # Generate unique asset ID
            asset_id = f"{category}_{len(self.metadata['assets'])}_{int(datetime.now().timestamp())}"

            # Determine file extension
            mime_type, _ = mimetypes.guess_type(filename)
            file_ext = Path(filename).suffix

            # Save file
            asset_path = self.categories[category] / f"{asset_id}{file_ext}"
            with open(asset_path, "wb") as f:
                f.write(file_data)

            # Create metadata entry
            asset_metadata = {
                "id": asset_id,
                "filename": filename,
                "category": category,
                "description": description,
                "tags": tags or [],
                "file_path": str(asset_path),
                "file_size": len(file_data),
                "mime_type": mime_type,
                "upload_date": datetime.now().isoformat(),
                "analysis_status": "pending",
            }

            # Store metadata
            self.metadata["assets"][asset_id] = asset_metadata
            self.metadata["total_assets"] += 1
            self.metadata["upload_history"].append(
                {
                    "asset_id": asset_id,
                    "timestamp": datetime.now().isoformat(),
                    "action": "upload",
                }
            )

            self._save_metadata()

            logger.info(f"✅ Brand asset uploaded: {filename} ({category})")
            return {
                "success": True,
                "asset_id": asset_id,
                "message": f"Asset '{filename}' uploaded successfully",
                "category": category,
                "file_path": str(asset_path),
            }

        except Exception as e:
            logger.error(f"Asset upload failed: {e!s}")
            return {"error": str(e)}

    def get_assets_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get all assets in a specific category."""
        return [asset for asset in self.metadata["assets"].values() if asset["category"] == category]

    def get_asset_info(self, asset_id: str) -> dict[str, Any] | None:
        """Get detailed information about a specific asset."""
        return self.metadata["assets"].get(asset_id)

    def analyze_brand_consistency(self) -> dict[str, Any]:
        """Analyze brand consistency across uploaded assets."""
        analysis = {
            "total_assets": self.metadata["total_assets"],
            "categories_used": {},
            "recent_uploads": [],
            "recommendations": [],
        }

        # Category analysis
        for asset in self.metadata["assets"].values():
            category = asset["category"]
            if category not in analysis["categories_used"]:
                analysis["categories_used"][category] = 0
            analysis["categories_used"][category] += 1

        # Recent uploads (last 7)
        analysis["recent_uploads"] = sorted(
            self.metadata["upload_history"], key=lambda x: x["timestamp"], reverse=True
        )[:7]

        # Generate recommendations
        if analysis["categories_used"].get("logos", 0) == 0:
            analysis["recommendations"].append("Upload logo variations for brand consistency analysis")

        if analysis["categories_used"].get("color_palettes", 0) == 0:
            analysis["recommendations"].append("Add color palette references for visual harmony checks")

        if analysis["total_assets"] < 5:
            analysis["recommendations"].append("Upload more assets for comprehensive brand analysis")

        return analysis

    def get_learning_data_for_brand_intelligence(self) -> dict[str, Any]:
        """Prepare asset data for Brand Intelligence Agent learning."""
        learning_data = {
            "visual_assets": {
                "logos": self.get_assets_by_category("logos"),
                "product_images": self.get_assets_by_category("product_images"),
                "marketing_materials": self.get_assets_by_category("marketing_materials"),
            },
            "brand_guidelines": self.get_assets_by_category("brand_guidelines"),
            "seasonal_collections": self.get_assets_by_category("seasonal_collections"),
            "asset_analysis": self.analyze_brand_consistency(),
            "total_learning_sources": self.metadata["total_assets"],
            "last_updated": self.metadata["last_updated"],
        }

        return learning_data


def initialize_brand_asset_manager() -> BrandAssetManager:
    """Initialize the brand asset management system."""
    return BrandAssetManager()
