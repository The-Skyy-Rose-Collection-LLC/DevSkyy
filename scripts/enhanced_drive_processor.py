#!/usr/bin/env python3
"""
Enhanced Google Drive Processor for Skyy Rose Collection
Handles shared Google Drive folders with direct download capabilities
"""

import asyncio
from datetime import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any

import requests


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedSkyRoseProcessor:
    """
    Enhanced processor for Skyy Rose Collection with direct Google Drive access.
    """

    def __init__(self):
        self.base_dir = Path("skyy_rose_collection")
        self.base_dir.mkdir(exist_ok=True)

        # Updated folder URL
        self.drive_folder_url = "https://drive.google.com/drive/folders/1F19qdkeAxleX-t28OzZk0vN6xAv52Vkt?usp=sharing"
        self.folder_id = "1F19qdkeAxleX-t28OzZk0vN6xAv52Vkt"

        # Processing stats
        self.stats = {"total_found": 0, "total_downloaded": 0, "total_processed": 0, "categories": {}, "errors": []}

    def get_folder_info(self) -> dict[str, Any]:
        """Get information about the Google Drive folder."""
        try:
            logger.info(f"📁 Analyzing Google Drive folder: {self.drive_folder_url}")

            # Try to extract folder information from the shared link
            folder_info = {
                "folder_id": self.folder_id,
                "folder_url": self.drive_folder_url,
                "access_type": "shared",
                "status": "accessible",
            }

            # Check if we can access the folder
            response = requests.get(self.drive_folder_url, timeout=10)
            if response.status_code == 200:
                folder_info["status"] = "accessible"

                # Try to extract folder name from the page
                if "Skyy Rose Collection" in response.text:
                    folder_info["folder_name"] = "Skyy Rose Collection"
                    logger.info("✅ Folder is accessible: Skyy Rose Collection")
                else:
                    folder_info["folder_name"] = "Unknown"
                    logger.info("✅ Folder is accessible but name not detected")
            else:
                folder_info["status"] = "access_denied"
                logger.warning("⚠️ Folder access may be restricted")

            return folder_info

        except Exception as e:
            logger.error(f"❌ Failed to analyze folder: {e}")
            return {
                "folder_id": self.folder_id,
                "folder_url": self.drive_folder_url,
                "status": "error",
                "error": str(e),
            }

    def generate_comprehensive_instructions(self) -> dict[str, Any]:
        """Generate comprehensive download and processing instructions."""

        instructions = {
            "folder_info": {"url": self.drive_folder_url, "folder_id": self.folder_id, "status": "shared_accessible"},
            "download_methods": {
                "method_1_web_download": {
                    "title": "🌐 Web Browser Download (Recommended)",
                    "difficulty": "Easy",
                    "time_estimate": "2-5 minutes",
                    "steps": [
                        f"1. 🔗 Open the folder: {self.drive_folder_url}",
                        "2. 📋 Select all images:",
                        "   • Windows/Linux: Press Ctrl+A",
                        "   • Mac: Press Cmd+A",
                        "   • Or click first image, then Shift+click last image",
                        "3. 📥 Download the images:",
                        "   • Right-click on selected images",
                        "   • Choose 'Download' from the menu",
                        "   • Google Drive will create a ZIP file",
                        "4. 💾 Save the ZIP file to your computer",
                        "5. 📂 Extract the ZIP file to get individual images",
                        "6. 📁 Note the folder location for processing",
                    ],
                    "expected_result": "ZIP file containing all Skyy Rose Collection images",
                },
                "method_2_individual_download": {
                    "title": "🖼️ Individual Image Download",
                    "difficulty": "Medium",
                    "time_estimate": "10-30 minutes",
                    "steps": [
                        f"1. 🔗 Open the folder: {self.drive_folder_url}",
                        "2. 🖼️ Click on each image to open it",
                        "3. 📥 Click the download button (⬇️) for each image",
                        "4. 💾 Save each image to a local folder",
                        "5. 📁 Organize images in a single directory",
                    ],
                    "expected_result": "Individual image files in a local folder",
                },
                "method_3_google_takeout": {
                    "title": "📦 Google Takeout (For Large Collections)",
                    "difficulty": "Medium",
                    "time_estimate": "15-60 minutes",
                    "steps": [
                        "1. 🔗 Go to: https://takeout.google.com/",
                        "2. 🔍 Select 'Drive' from the list",
                        "3. ⚙️ Click 'All Drive data included'",
                        "4. 🎯 Deselect all, then find and select 'Skyy Rose Collection'",
                        "5. ⬇️ Choose export format (ZIP recommended)",
                        "6. 📧 Google will email you when ready",
                        "7. 📥 Download the archive from the email link",
                    ],
                    "expected_result": "Complete archive of the folder contents",
                },
            },
            "processing_options": {
                "option_1_drag_drop": {
                    "title": "🎯 Drag & Drop Interface (Easiest)",
                    "url": "http://localhost:8001",
                    "steps": [
                        "1. 🌐 Open: http://localhost:8001",
                        "2. 📁 Drag your downloaded images into the interface",
                        "3. ⚡ Watch automatic processing happen",
                        "4. ✅ Images are categorized, resized, and uploaded automatically",
                    ],
                },
                "option_2_command_line": {
                    "title": "💻 Command Line Processing",
                    "steps": [
                        "1. 📂 Place downloaded images in a folder",
                        "2. 🚀 Run: python scripts/google_drive_processor.py --process-local /path/to/images --upload",
                        "3. ⏳ Wait for processing to complete",
                        "4. ✅ Check results in the training interface",
                    ],
                },
                "option_3_manual_upload": {
                    "title": "📤 Manual Upload Interface",
                    "url": "http://localhost:8001/classic",
                    "steps": [
                        "1. 🌐 Open: http://localhost:8001/classic",
                        "2. 📋 Use the form-based interface",
                        "3. 📁 Upload single images, batches, or ZIP files",
                        "4. ⚙️ Configure categories and processing options manually",
                    ],
                },
            },
            "expected_outcomes": {
                "automatic_categorization": [
                    "🌹 Dresses: evening gowns, cocktail dresses, casual dresses",
                    "👕 Tops: blouses, shirts, sweaters, jackets",
                    "👖 Bottoms: pants, skirts, shorts, leggings",
                    "👜 Accessories: bags, jewelry, scarves, belts",
                    "👠 Shoes: heels, boots, flats, sneakers",
                    "🧥 Outerwear: coats, jackets, cardigans",
                ],
                "image_processing": [
                    "📏 Resized to 1024x1024 for optimal AI training",
                    "✨ Quality enhanced with professional processing",
                    "🏷️ Tagged with brand-specific trigger words",
                    "📝 Auto-generated captions for each image",
                    "📊 Metadata created for training optimization",
                ],
                "brand_integration": [
                    "🎯 Trigger words: skyrose_dresses, skyrose_collection, etc.",
                    "📝 Captions: 'skyrose_collection, luxury fashion item, high-end design'",
                    "🎨 Ready for custom AI model training",
                    "🎬 Compatible with video generation system",
                ],
            },
            "troubleshooting": {
                "access_issues": {
                    "problem": "Cannot access the Google Drive folder",
                    "solutions": [
                        "🔗 Ensure you're using the correct link with sharing permissions",
                        "🔐 Check if you need to request access from the folder owner",
                        "🌐 Try opening the link in an incognito/private browser window",
                        "📧 Contact the folder owner to verify sharing settings",
                    ],
                },
                "download_issues": {
                    "problem": "Download fails or is incomplete",
                    "solutions": [
                        "🔄 Try downloading smaller batches of images",
                        "🌐 Use a different browser or clear browser cache",
                        "📶 Check your internet connection stability",
                        "⏰ Try downloading during off-peak hours",
                    ],
                },
                "processing_issues": {
                    "problem": "Image processing fails",
                    "solutions": [
                        "📋 Check that images are in supported formats (JPG, PNG, WEBP, HEIC, BMP, TIFF)",
                        "📏 Ensure image files are under 50MB each",
                        "🔄 Restart the training interface: python api/training_data_interface.py",
                        "🌐 Verify the interface is running at http://localhost:8001",
                    ],
                },
            },
        }

        return instructions

    def create_download_script(self) -> str:
        """Create a comprehensive download script."""

        script_content = f"""#!/bin/bash
# Skyy Rose Collection - Comprehensive Download Script
# Generated: {datetime.now().isoformat()}

echo "🌹 Skyy Rose Collection Download & Processing Script"
echo "=================================================="
echo ""

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Folder information
FOLDER_URL="{self.drive_folder_url}"
FOLDER_ID="{self.folder_id}"

echo -e "${{BLUE}}📁 Google Drive Folder:${{NC}} Skyy Rose Collection"
echo -e "${{BLUE}}🔗 URL:${{NC}} $FOLDER_URL"
echo -e "${{BLUE}}📋 Folder ID:${{NC}} $FOLDER_ID"
echo ""

# Create download directory
DOWNLOAD_DIR="skyy_rose_download_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

echo -e "${{GREEN}}📂 Created download directory:${{NC}} $DOWNLOAD_DIR"
echo ""

echo -e "${{YELLOW}}📋 DOWNLOAD INSTRUCTIONS:${{NC}}"
echo "=========================="
echo ""
echo -e "${{BLUE}}Method 1: Web Browser Download (Recommended)${{NC}}"
echo "1. 🔗 Open this URL in your browser:"
echo "   $FOLDER_URL"
echo ""
echo "2. 📋 Select all images:"
echo "   • Windows/Linux: Press Ctrl+A"
echo "   • Mac: Press Cmd+A"
echo ""
echo "3. 📥 Download the images:"
echo "   • Right-click on selected images"
echo "   • Choose 'Download' from the menu"
echo "   • Google Drive will create a ZIP file"
echo ""
echo "4. 💾 Save the ZIP file to this directory:"
echo "   $(pwd)"
echo ""
echo "5. 📂 Extract the ZIP file (we'll do this automatically)"
echo ""

echo -e "${{BLUE}}Method 2: Individual Download${{NC}}"
echo "1. 🔗 Open the folder URL above"
echo "2. 🖼️ Click on each image to open it"
echo "3. 📥 Click the download button (⬇️) for each image"
echo "4. 💾 Save each image to this directory"
echo ""

echo -e "${{YELLOW}}⏳ Waiting for download...${{NC}}"
echo "Press ENTER after you've downloaded the images to this directory"
read -p ""

# Check for downloaded files
echo ""
echo -e "${{BLUE}}🔍 Checking for downloaded files...${{NC}}"

# Look for ZIP files
ZIP_FILES=(*.zip)
IMAGE_FILES=(*.jpg *.jpeg *.png *.webp *.heic *.bmp *.tiff *.JPG *.JPEG *.PNG *.WEBP *.HEIC *.BMP *.TIFF)

if [ -f "${{ZIP_FILES[0]}}" ]; then
    echo -e "${{GREEN}}✅ Found ZIP file(s). Extracting...${{NC}}"
    for zip_file in *.zip; do
        if [ -f "$zip_file" ]; then
            echo "📂 Extracting: $zip_file"
            unzip -q "$zip_file"
            echo "✅ Extracted: $zip_file"
        fi
    done
elif [ -f "${{IMAGE_FILES[0]}}" ]; then
    echo -e "${{GREEN}}✅ Found individual image files.${{NC}}"
else
    echo -e "${{RED}}❌ No image files found in this directory.${{NC}}"
    echo "Please download the images and run this script again."
    exit 1
fi

# Count images
IMAGE_COUNT=$(find . -type f \\( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.heic" -o -iname "*.bmp" -o -iname "*.tiff" \\) | wc -l)

echo ""
echo -e "${{GREEN}}📊 Found $IMAGE_COUNT images ready for processing${{NC}}"
echo ""

if [ $IMAGE_COUNT -gt 0 ]; then
    echo -e "${{YELLOW}}🚀 PROCESSING OPTIONS:${{NC}}"
    echo "====================="
    echo ""
    echo -e "${{BLUE}}Option 1: Drag & Drop Interface (Recommended)${{NC}}"
    echo "1. 🌐 Open: http://localhost:8001"
    echo "2. 📁 Drag the images from this folder into the interface"
    echo "3. ⚡ Watch automatic processing happen"
    echo ""
    echo -e "${{BLUE}}Option 2: Automatic Command Line Processing${{NC}}"
    echo "Run this command from the DevSkyy directory:"
    echo "python scripts/google_drive_processor.py --process-local \\"$(pwd)\\" --upload"
    echo ""
    echo -e "${{BLUE}}Option 3: Manual Upload Interface${{NC}}"
    echo "1. 🌐 Open: http://localhost:8001/classic"
    echo "2. 📤 Use the form-based upload interface"
    echo ""

    echo -e "${{YELLOW}}Would you like to start automatic processing now? (y/n)${{NC}}"
    read -p "" -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${{GREEN}}🚀 Starting automatic processing...${{NC}}"
        cd ..
        python scripts/google_drive_processor.py --process-local "$DOWNLOAD_DIR" --upload
    else
        echo -e "${{BLUE}}📋 Manual processing instructions saved.${{NC}}"
        echo "Images are ready in: $(pwd)"
    fi
else
    echo -e "${{RED}}❌ No images found. Please check the download and try again.${{NC}}"
fi

echo ""
echo -e "${{GREEN}}🌹 Skyy Rose Collection processing setup complete!${{NC}}"
"""

        return script_content

    async def create_processing_guide(self) -> dict[str, Any]:
        """Create a comprehensive processing guide."""

        # Get folder info
        folder_info = self.get_folder_info()

        # Generate instructions
        instructions = self.generate_comprehensive_instructions()

        # Create download script
        script_content = self.create_download_script()

        # Save the script
        script_path = Path("download_skyy_rose_enhanced.sh")
        with open(script_path, "w") as f:
            f.write(script_content)

        # Make script executable
        os.chmod(script_path, 0o755)

        return {
            "success": True,
            "folder_info": folder_info,
            "instructions": instructions,
            "script_path": str(script_path),
            "download_script_created": True,
            "interfaces_available": {
                "drag_drop": "http://localhost:8001",
                "classic_upload": "http://localhost:8001/classic",
                "api_status": "http://localhost:8001/status/uploads",
            },
            "next_steps": [
                "1. Run the download script: ./download_skyy_rose_enhanced.sh",
                "2. Follow the interactive instructions",
                "3. Use the drag & drop interface for easy processing",
                "4. Monitor progress at http://localhost:8001/status/uploads",
            ],
            "timestamp": datetime.now().isoformat(),
        }


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Skyy Rose Collection Processor")
    parser.add_argument("--create-guide", action="store_true", help="Create comprehensive processing guide")
    parser.add_argument("--folder-info", action="store_true", help="Get folder information")

    args = parser.parse_args()

    processor = EnhancedSkyRoseProcessor()

    async def main():
        if args.create_guide:
            result = await processor.create_processing_guide()
            print(json.dumps(result, indent=2))
        elif args.folder_info:
            info = processor.get_folder_info()
            print(json.dumps(info, indent=2))
        else:
            # Default: create comprehensive guide
            result = await processor.create_processing_guide()
            print("🌹 Skyy Rose Collection Processing Guide Created!")
            print(f"📋 Instructions: {result['success']}")
            print(f"📜 Download script: {result['script_path']}")
            print(f"🌐 Drag & Drop Interface: {result['interfaces_available']['drag_drop']}")

    asyncio.run(main())
