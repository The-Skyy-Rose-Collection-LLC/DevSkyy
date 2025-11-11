#!/bin/bash
# Skyy Rose Collection - Comprehensive Download Script
# Generated: 2025-10-26T16:41:29.183885

echo "🌹 Skyy Rose Collection Download & Processing Script"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Folder information
FOLDER_URL="https://drive.google.com/drive/folders/1F19qdkeAxleX-t28OzZk0vN6xAv52Vkt?usp=sharing"
FOLDER_ID="1F19qdkeAxleX-t28OzZk0vN6xAv52Vkt"

echo -e "${BLUE}📁 Google Drive Folder:${NC} Skyy Rose Collection"
echo -e "${BLUE}🔗 URL:${NC} $FOLDER_URL"
echo -e "${BLUE}📋 Folder ID:${NC} $FOLDER_ID"
echo ""

# Create download directory
DOWNLOAD_DIR="skyy_rose_download_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

echo -e "${GREEN}📂 Created download directory:${NC} $DOWNLOAD_DIR"
echo ""

echo -e "${YELLOW}📋 DOWNLOAD INSTRUCTIONS:${NC}"
echo "=========================="
echo ""
echo -e "${BLUE}Method 1: Web Browser Download (Recommended)${NC}"
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

echo -e "${BLUE}Method 2: Individual Download${NC}"
echo "1. 🔗 Open the folder URL above"
echo "2. 🖼️ Click on each image to open it"
echo "3. 📥 Click the download button (⬇️) for each image"
echo "4. 💾 Save each image to this directory"
echo ""

echo -e "${YELLOW}⏳ Waiting for download...${NC}"
echo "Press ENTER after you've downloaded the images to this directory"
read -p ""

# Check for downloaded files
echo ""
echo -e "${BLUE}🔍 Checking for downloaded files...${NC}"

# Look for ZIP files
ZIP_FILES=(*.zip)
IMAGE_FILES=(*.jpg *.jpeg *.png *.webp *.heic *.bmp *.tiff *.JPG *.JPEG *.PNG *.WEBP *.HEIC *.BMP *.TIFF)

if [ -f "${ZIP_FILES[0]}" ]; then
    echo -e "${GREEN}✅ Found ZIP file(s). Extracting...${NC}"
    for zip_file in *.zip; do
        if [ -f "$zip_file" ]; then
            echo "📂 Extracting: $zip_file"
            unzip -q "$zip_file"
            echo "✅ Extracted: $zip_file"
        fi
    done
elif [ -f "${IMAGE_FILES[0]}" ]; then
    echo -e "${GREEN}✅ Found individual image files.${NC}"
else
    echo -e "${RED}❌ No image files found in this directory.${NC}"
    echo "Please download the images and run this script again."
    exit 1
fi

# Count images
IMAGE_COUNT=$(find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.heic" -o -iname "*.bmp" -o -iname "*.tiff" \) | wc -l)

echo ""
echo -e "${GREEN}📊 Found $IMAGE_COUNT images ready for processing${NC}"
echo ""

if [ $IMAGE_COUNT -gt 0 ]; then
    echo -e "${YELLOW}🚀 PROCESSING OPTIONS:${NC}"
    echo "====================="
    echo ""
    echo -e "${BLUE}Option 1: Drag & Drop Interface (Recommended)${NC}"
    echo "1. 🌐 Open: http://localhost:8001"
    echo "2. 📁 Drag the images from this folder into the interface"
    echo "3. ⚡ Watch automatic processing happen"
    echo ""
    echo -e "${BLUE}Option 2: Automatic Command Line Processing${NC}"
    echo "Run this command from the DevSkyy directory:"
    echo "python scripts/google_drive_processor.py --process-local \"$(pwd)\" --upload"
    echo ""
    echo -e "${BLUE}Option 3: Manual Upload Interface${NC}"
    echo "1. 🌐 Open: http://localhost:8001/classic"
    echo "2. 📤 Use the form-based upload interface"
    echo ""

    echo -e "${YELLOW}Would you like to start automatic processing now? (y/n)${NC}"
    read -p "" -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}🚀 Starting automatic processing...${NC}"
        cd ..
        python scripts/google_drive_processor.py --process-local "$DOWNLOAD_DIR" --upload
    else
        echo -e "${BLUE}📋 Manual processing instructions saved.${NC}"
        echo "Images are ready in: $(pwd)"
    fi
else
    echo -e "${RED}❌ No images found. Please check the download and try again.${NC}"
fi

echo ""
echo -e "${GREEN}🌹 Skyy Rose Collection processing setup complete!${NC}"
