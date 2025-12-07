#!/usr/bin/env python3
"""
Google Drive Image Processor for Skyy Rose Collection
Downloads, categorizes, and processes images from Google Drive for AI training
"""

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import re
from typing import Any

from PIL import Image, ImageOps
import requests


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkyRoseGoogleDriveProcessor:
    """
    Processes Skyy Rose Collection images from Google Drive for AI training.
    """

    def __init__(self):
        self.base_dir = Path("skyy_rose_training_data")
        self.base_dir.mkdir(exist_ok=True)

        # Category mapping based on filename patterns
        self.category_patterns = {
            "dresses": [
                r"dress",
                r"gown",
                r"evening",
                r"cocktail",
                r"maxi",
                r"midi",
                r"mini",
                r"sundress",
                r"bodycon",
                r"a-line",
                r"wrap",
                r"shift",
                r"slip",
            ],
            "tops": [
                r"top",
                r"blouse",
                r"shirt",
                r"tee",
                r"tank",
                r"camisole",
                r"crop",
                r"tunic",
                r"sweater",
                r"cardigan",
                r"blazer",
                r"jacket",
            ],
            "bottoms": [
                r"pants",
                r"jeans",
                r"trousers",
                r"leggings",
                r"shorts",
                r"skirt",
                r"palazzo",
                r"wide.leg",
                r"skinny",
                r"straight",
                r"bootcut",
            ],
            "accessories": [
                r"bag",
                r"purse",
                r"clutch",
                r"belt",
                r"scarf",
                r"hat",
                r"jewelry",
                r"necklace",
                r"earrings",
                r"bracelet",
                r"ring",
                r"watch",
                r"sunglasses",
            ],
            "shoes": [
                r"shoes",
                r"heels",
                r"boots",
                r"sandals",
                r"flats",
                r"sneakers",
                r"pumps",
                r"stiletto",
                r"wedge",
                r"ankle.boot",
                r"knee.boot",
            ],
            "outerwear": [
                r"coat",
                r"jacket",
                r"blazer",
                r"cardigan",
                r"vest",
                r"poncho",
                r"cape",
                r"trench",
                r"puffer",
                r"bomber",
                r"denim.jacket",
            ],
        }

        # Supported image formats
        self.supported_formats = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tiff"}

        # Processing stats
        self.stats = {"total_downloaded": 0, "total_processed": 0, "categories": {}, "errors": []}

    def extract_folder_id(self, drive_url: str) -> str | None:
        """Extract folder ID from Google Drive URL."""
        patterns = [r"/folders/([a-zA-Z0-9-_]+)", r"id=([a-zA-Z0-9-_]+)", r"folders/([a-zA-Z0-9-_]+)"]

        for pattern in patterns:
            match = re.search(pattern, drive_url)
            if match:
                return match.group(1)

        return None

    def categorize_image(self, filename: str) -> str:
        """
        Categorize image based on filename patterns.

        Args:
            filename: Image filename

        Returns:
            Category name
        """
        filename_lower = filename.lower()

        # Check each category pattern
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return category

        # Default category
        return "general"

    async def download_from_google_drive(self, drive_url: str) -> dict[str, Any]:
        """
        Download images from Google Drive folder.

        Args:
            drive_url: Google Drive folder URL

        Returns:
            Download results
        """
        try:
            logger.info(f"🔗 Processing Google Drive URL: {drive_url}")

            folder_id = self.extract_folder_id(drive_url)
            if not folder_id:
                return {"error": "Could not extract folder ID from URL", "status": "failed"}

            logger.info(f"📁 Extracted folder ID: {folder_id}")

            # Since the folder requires authentication, provide instructions for manual download
            instructions = self._generate_download_instructions(drive_url, folder_id)

            return {
                "success": True,
                "folder_id": folder_id,
                "instructions": instructions,
                "message": "Manual download required - see instructions",
            }

        except Exception as e:
            logger.error(f"❌ Failed to process Google Drive URL: {e}")
            return {"error": str(e), "status": "failed"}

    def _generate_download_instructions(self, drive_url: str, folder_id: str) -> dict[str, Any]:
        """Generate step-by-step download instructions."""
        return {
            "method_1_web_interface": {
                "title": "Download via Google Drive Web Interface",
                "steps": [
                    f"1. Open the Google Drive folder: {drive_url}",
                    "2. Select all images (Ctrl+A or Cmd+A)",
                    "3. Right-click and select 'Download'",
                    "4. Google Drive will create a ZIP file for download",
                    "5. Save the ZIP file to your computer",
                    "6. Extract the ZIP file to get individual images",
                ],
            },
            "method_2_google_drive_api": {
                "title": "Download via Google Drive API (Advanced)",
                "steps": [
                    "1. Enable Google Drive API in Google Cloud Console",
                    "2. Create service account credentials",
                    "3. Share the folder with the service account email",
                    "4. Use the credentials to download programmatically",
                ],
            },
            "method_3_rclone": {
                "title": "Download via rclone (Command Line)",
                "steps": [
                    "1. Install rclone: https://rclone.org/downloads/",
                    "2. Configure Google Drive: rclone config",
                    "3. Download folder: rclone copy 'gdrive:folder_name' ./local_folder",
                    "4. Replace 'folder_name' with the actual folder name",
                ],
            },
            "recommended_approach": "method_1_web_interface",
        }

    async def process_local_images(self, source_directory: str) -> dict[str, Any]:
        """
        Process images from a local directory.

        Args:
            source_directory: Path to directory containing images

        Returns:
            Processing results
        """
        try:
            source_path = Path(source_directory)
            if not source_path.exists():
                return {"error": f"Source directory not found: {source_directory}", "status": "failed"}

            logger.info(f"📁 Processing images from: {source_directory}")

            # Find all image files
            image_files = []
            for ext in self.supported_formats:
                image_files.extend(source_path.glob(f"*{ext}"))
                image_files.extend(source_path.glob(f"*{ext.upper()}"))

            if not image_files:
                return {"error": "No supported image files found", "status": "failed"}

            logger.info(f"📸 Found {len(image_files)} images to process")

            # Process each image
            processed_images = []
            for image_file in image_files:
                try:
                    result = await self._process_single_image(image_file)
                    if result["success"]:
                        processed_images.append(result)
                        self.stats["total_processed"] += 1

                        # Update category stats
                        category = result["category"]
                        if category not in self.stats["categories"]:
                            self.stats["categories"][category] = 0
                        self.stats["categories"][category] += 1

                except Exception as e:
                    error_msg = f"Failed to process {image_file}: {e}"
                    logger.warning(error_msg)
                    self.stats["errors"].append(error_msg)

            # Generate summary
            summary = self._generate_processing_summary(processed_images)

            return {
                "success": True,
                "total_processed": len(processed_images),
                "processed_images": processed_images,
                "stats": self.stats,
                "summary": summary,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to process local images: {e}")
            return {"error": str(e), "status": "failed"}

    async def _process_single_image(self, image_path: Path) -> dict[str, Any]:
        """Process a single image file."""
        try:
            # Categorize based on filename
            category = self.categorize_image(image_path.name)

            # Create category directory
            category_dir = self.base_dir / category
            category_dir.mkdir(exist_ok=True)

            # Load and process image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize to 1024x1024 for training
                img_resized = img.resize((1024, 1024), Image.Resampling.LANCZOS)

                # Enhance image quality
                img_enhanced = ImageOps.autocontrast(img_resized)
                img_enhanced = ImageOps.equalize(img_enhanced)

                # Generate output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                output_filename = f"skyrose_{category}_{timestamp}.jpg"
                output_path = category_dir / output_filename

                # Save processed image
                img_enhanced.save(output_path, "JPEG", quality=95, optimize=True)

                # Generate metadata
                metadata = {
                    "original_filename": image_path.name,
                    "processed_filename": output_filename,
                    "category": category,
                    "original_size": img.size,
                    "processed_size": (1024, 1024),
                    "file_size": output_path.stat().st_size,
                    "processing_timestamp": datetime.now().isoformat(),
                    "trigger_word": f"skyrose_{category}",
                    "caption": f"skyrose_{category}, luxury fashion item, high-end design",
                }

                # Save metadata
                metadata_file = category_dir / f"{output_filename}.json"
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                return {
                    "success": True,
                    "original_path": str(image_path),
                    "processed_path": str(output_path),
                    "category": category,
                    "metadata": metadata,
                }

        except Exception as e:
            return {"success": False, "error": str(e), "original_path": str(image_path)}

    def _generate_processing_summary(self, processed_images: list[dict]) -> dict[str, Any]:
        """Generate processing summary."""
        categories = {}
        total_size = 0

        for img in processed_images:
            if img["success"]:
                category = img["category"]
                if category not in categories:
                    categories[category] = {"count": 0, "size": 0}

                categories[category]["count"] += 1
                categories[category]["size"] += img["metadata"]["file_size"]
                total_size += img["metadata"]["file_size"]

        return {
            "total_images": len(processed_images),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "categories": categories,
            "processing_date": datetime.now().isoformat(),
            "ready_for_training": True,
        }

    async def upload_to_training_interface(self, processed_data_dir: str) -> dict[str, Any]:
        """
        Upload processed images to the training data interface.

        Args:
            processed_data_dir: Directory containing processed images

        Returns:
            Upload results
        """
        try:
            logger.info("📤 Uploading processed images to training interface")

            upload_results = []
            processed_path = Path(processed_data_dir)

            # Upload each category
            for category_dir in processed_path.iterdir():
                if not category_dir.is_dir():
                    continue

                category_name = category_dir.name
                image_files = list(category_dir.glob("*.jpg"))

                if not image_files:
                    continue

                logger.info(f"📁 Uploading {len(image_files)} images from category: {category_name}")

                # Upload images in batches
                batch_size = 10
                for i in range(0, len(image_files), batch_size):
                    batch = image_files[i : i + batch_size]

                    # Prepare files for upload
                    files = []
                    for img_file in batch:
                        files.append(("files", (img_file.name, open(img_file, "rb"), "image/jpeg")))

                    # Upload batch
                    try:
                        response = requests.post(
                            "http://localhost:8001/upload/batch-images",
                            files=files,
                            data={"category": category_name, "auto_process": "true"},
                        )

                        # Close file handles
                        for _, (_, file_handle, _) in files:
                            file_handle.close()

                        if response.status_code == 200:
                            result = response.json()
                            upload_results.append(
                                {
                                    "category": category_name,
                                    "batch": i // batch_size + 1,
                                    "uploaded": result.get("uploaded_count", 0),
                                    "failed": result.get("failed_count", 0),
                                }
                            )
                        else:
                            logger.warning(f"Upload failed for {category_name} batch {i // batch_size + 1}")

                    except Exception as e:
                        logger.error(f"Failed to upload batch: {e}")

            return {
                "success": True,
                "upload_results": upload_results,
                "total_batches": len(upload_results),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to upload to training interface: {e}")
            return {"error": str(e), "status": "failed"}

    def generate_download_script(self, drive_url: str) -> str:
        """Generate a download script for the user."""
        folder_id = self.extract_folder_id(drive_url)

        script = f"""#!/bin/bash
# Skyy Rose Collection Download Script
# Generated on {datetime.now().isoformat()}

echo "🌹 Skyy Rose Collection Image Processor"
echo "======================================="

# Create download directory
mkdir -p skyy_rose_download
cd skyy_rose_download

echo "📁 Google Drive Folder ID: {folder_id}"
echo "🔗 Folder URL: {drive_url}"
echo ""
echo "📋 Download Instructions:"
echo "1. Open the Google Drive folder in your browser"
echo "2. Select all images (Ctrl+A or Cmd+A)"
echo "3. Right-click and select 'Download'"
echo "4. Save the downloaded ZIP file to this directory"
echo "5. Extract the ZIP file"
echo "6. Run the processing script"
echo ""
echo "💡 Alternative: Use rclone for automated download"
echo "   1. Install rclone: https://rclone.org/"
echo "   2. Configure: rclone config"
echo "   3. Download: rclone copy 'gdrive:Skyy Rose Collection' ./"
echo ""
echo "🚀 After download, run: python ../scripts/google_drive_processor.py --process-local ./extracted_images"
"""

        return script


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process Skyy Rose Collection images from Google Drive")
    parser.add_argument("--drive-url", help="Google Drive folder URL")
    parser.add_argument("--process-local", help="Process images from local directory")
    parser.add_argument("--upload", help="Upload processed images to training interface")
    parser.add_argument("--generate-script", action="store_true", help="Generate download script")

    args = parser.parse_args()

    processor = SkyRoseGoogleDriveProcessor()

    async def main():
        if args.drive_url:
            if args.generate_script:
                script = processor.generate_download_script(args.drive_url)
                with open("download_skyy_rose.sh", "w") as f:
                    f.write(script)
                print("📝 Download script generated: download_skyy_rose.sh")
            else:
                result = await processor.download_from_google_drive(args.drive_url)
                print(json.dumps(result, indent=2))

        elif args.process_local:
            result = await processor.process_local_images(args.process_local)
            print(json.dumps(result, indent=2))

            if result.get("success") and args.upload:
                upload_result = await processor.upload_to_training_interface(args.process_local)
                print("Upload result:", json.dumps(upload_result, indent=2))

        else:
            parser.print_help()

    asyncio.run(main())
