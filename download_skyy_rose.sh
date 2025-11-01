#!/bin/bash
# Skyy Rose Collection Download Script
# Generated on 2025-10-26T16:36:20.788345

echo "🌹 Skyy Rose Collection Image Processor"
echo "======================================="

# Create download directory
mkdir -p skyy_rose_download
cd skyy_rose_download

echo "📁 Google Drive Folder ID: 1F19qdkeAxleX-t28OzZk0vN6xAv52Vkt"
echo "🔗 Folder URL: https://drive.google.com/drive/folders/1F19qdkeAxleX-t28OzZk0vN6xAv52Vkt?usp=drive_link"
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
