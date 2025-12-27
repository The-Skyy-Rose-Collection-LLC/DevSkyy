#!/usr/bin/env python3
"""
SkyyRose Asset Extraction and Organization Script

Extracts assets from updev 4.zip and organizes them into:
- 3D models by collection (black-rose, love-hurts, signature, etc.)
- Logos and brand assets
- Press materials
- Reference templates and specifications

Usage:
    python3 scripts/extract_skyyrose_assets.py \
        --zip-path "/Users/coreyfoster/Desktop/updev 4.zip" \
        --output-dir "./assets"

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import argparse
import json
import logging
import shutil
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# File type mappings for organization
FILE_MAPPINGS = {
    "3d_models": {
        "extensions": [".obj", ".fbx", ".blend", ".glb", ".gltf", ".usdz", ".mtl"],
        "keywords": ["model", "mesh", "3d"],
    },
    "logos": {
        "extensions": [".svg", ".ai"],
        "keywords": ["logo", "mark", "icon"],
    },
    "images": {
        "extensions": [".jpg", ".jpeg", ".png", ".webp"],
        "keywords": ["hero", "lifestyle", "detail", "background"],
    },
    "configs": {
        "extensions": [".json", ".yaml", ".yml", ".xml"],
        "keywords": ["config", "spec", "specification"],
    },
    "templates": {
        "extensions": [".html", ".htm"],
        "keywords": ["template", "example"],
    },
    "docs": {
        "extensions": [".md", ".txt", ".pdf"],
        "keywords": ["readme", "guide", "spec"],
    },
}

COLLECTIONS = [
    "black-rose",
    "love-hurts",
    "signature",
    "showroom",
    "runway",
]


class AssetExtractor:
    """Extract and organize SkyyRose assets from ZIP file."""

    def __init__(self, zip_path: str, output_dir: str = "./assets"):
        """
        Initialize asset extractor.

        Args:
            zip_path: Path to ZIP file
            output_dir: Output directory for organized assets
        """
        self.zip_path = Path(zip_path)
        self.output_dir = Path(output_dir)
        self.temp_extract_dir = self.output_dir / "_extracted_temp"
        self.inventory = {
            "extracted_at": "",
            "total_files": 0,
            "by_type": {},
            "by_collection": {},
            "missing_files": [],
            "errors": [],
        }

    def extract_zip(self) -> bool:
        """Extract ZIP file to temp directory."""
        try:
            if not self.zip_path.exists():
                logger.error(f"ZIP file not found: {self.zip_path}")
                return False

            logger.info(f"Extracting {self.zip_path} to {self.temp_extract_dir}")

            with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
                zip_ref.extractall(self.temp_extract_dir)

            logger.info(f"✓ Extracted {len(list(self.temp_extract_dir.rglob('*')))} files")
            return True

        except Exception as e:
            logger.error(f"Failed to extract ZIP: {e}")
            self.inventory["errors"].append(f"ZIP extraction failed: {str(e)}")
            return False

    def create_directory_structure(self) -> None:
        """Create organized asset directories."""
        logger.info("Creating directory structure...")

        # Main directories
        (self.output_dir / "3d-models").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "logos").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "press").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images" / "hero").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images" / "lifestyle").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images" / "detail").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reference-templates").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "configs").mkdir(parents=True, exist_ok=True)

        # Collection-specific directories
        for collection in COLLECTIONS:
            (self.output_dir / "3d-models" / collection).mkdir(parents=True, exist_ok=True)

        logger.info("✓ Directory structure created")

    def categorize_file(self, file_path: Path) -> tuple[str, str | None]:
        """
        Categorize file by extension and keywords.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (category, subcategory)
        """
        extension = file_path.suffix.lower()
        filename = file_path.name.lower()

        # Check for collection-specific files
        for collection in COLLECTIONS:
            if collection in filename:
                return ("3d_models", collection)

        # Check file extensions and keywords
        for category, rules in FILE_MAPPINGS.items():
            if extension in rules["extensions"]:
                # Check for keywords
                for keyword in rules["keywords"]:
                    if keyword in filename:
                        return (category, None)

                return (category, None)

        return ("other", None)

    def organize_files(self) -> None:
        """Organize extracted files into categorized directories."""
        logger.info("Organizing files...")

        file_count = 0
        for file_path in self.temp_extract_dir.rglob("*"):
            if not file_path.is_file():
                continue

            category, subcategory = self.categorize_file(file_path)

            # Determine destination
            if category == "3d_models" and subcategory:
                dest_dir = self.output_dir / "3d-models" / subcategory
            elif category == "logos":
                dest_dir = self.output_dir / "logos"
            elif category == "images":
                dest_dir = self.output_dir / "images" / (subcategory or "misc")
            elif category == "configs":
                dest_dir = self.output_dir / "configs"
            elif category == "templates" or category == "docs":
                dest_dir = self.output_dir / "reference-templates"
            else:
                dest_dir = self.output_dir / "_other"

            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / file_path.name

            try:
                shutil.copy2(file_path, dest_path)
                file_count += 1

                # Track in inventory
                if category not in self.inventory["by_type"]:
                    self.inventory["by_type"][category] = 0
                self.inventory["by_type"][category] += 1

                if subcategory:
                    if subcategory not in self.inventory["by_collection"]:
                        self.inventory["by_collection"][subcategory] = 0
                    self.inventory["by_collection"][subcategory] += 1

            except Exception as e:
                logger.error(f"Failed to copy {file_path}: {e}")
                self.inventory["errors"].append(f"Failed to copy {file_path.name}: {str(e)}")

        logger.info(f"✓ Organized {file_count} files")

    def verify_collections(self) -> None:
        """Verify that all collections have assets."""
        logger.info("Verifying collections...")

        for collection in COLLECTIONS:
            collection_dir = self.output_dir / "3d-models" / collection
            files = list(collection_dir.glob("*"))

            if not files:
                message = f"WARNING: {collection} collection is empty"
                logger.warning(message)
                self.inventory["missing_files"].append(collection)
            else:
                logger.info(f"✓ {collection}: {len(files)} files")

    def generate_inventory(self) -> None:
        """Generate and save inventory report."""
        logger.info("Generating inventory...")

        inventory_path = self.output_dir / "INVENTORY.json"

        # Add timestamp
        from datetime import datetime

        self.inventory["extracted_at"] = datetime.now().isoformat()
        self.inventory["total_files"] = sum(self.inventory["by_type"].values())

        # Save inventory
        with open(inventory_path, "w") as f:
            json.dump(self.inventory, f, indent=2)

        logger.info(f"✓ Inventory saved to {inventory_path}")

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("ASSET EXTRACTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total files: {self.inventory['total_files']}")
        logger.info("\nBy type:")
        for ftype, count in self.inventory["by_type"].items():
            logger.info(f"  {ftype}: {count}")

        logger.info("\nBy collection:")
        for collection, count in self.inventory["by_collection"].items():
            logger.info(f"  {collection}: {count}")

        if self.inventory["missing_files"]:
            logger.warning("\nMissing collections:")
            for collection in self.inventory["missing_files"]:
                logger.warning(f"  - {collection}")

        if self.inventory["errors"]:
            logger.error("\nErrors encountered:")
            for error in self.inventory["errors"]:
                logger.error(f"  - {error}")

        logger.info("=" * 60 + "\n")

    def cleanup(self) -> None:
        """Clean up temporary extraction directory."""
        logger.info("Cleaning up temporary files...")

        try:
            shutil.rmtree(self.temp_extract_dir)
            logger.info("✓ Temporary files cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup temp directory: {e}")

    def run(self) -> bool:
        """
        Run full extraction and organization pipeline.

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting asset extraction from {self.zip_path}")

        if not self.extract_zip():
            return False

        self.create_directory_structure()
        self.organize_files()
        self.verify_collections()
        self.generate_inventory()
        self.cleanup()

        logger.info("✓ Asset extraction complete!")
        logger.info(f"Assets organized in: {self.output_dir}")

        return True


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract and organize SkyyRose assets from ZIP file"
    )
    parser.add_argument(
        "--zip-path",
        required=True,
        help="Path to updev 4.zip file",
    )
    parser.add_argument(
        "--output-dir",
        default="./assets",
        help="Output directory for organized assets (default: ./assets)",
    )

    args = parser.parse_args()

    extractor = AssetExtractor(
        zip_path=args.zip_path,
        output_dir=args.output_dir,
    )

    success = extractor.run()

    exit(0 if success else 1)


if __name__ == "__main__":
    main()
