#!/bin/bash
# Upload all SkyyRose collections from Google Drive to WooCommerce
# Only uploads clothing items (excludes accessories like hats, bags, etc.)

set -e  # Exit on error

echo "🚀 SkyyRose Batch Product Uploader"
echo "=================================="
echo ""

# Drive folder URLs
BLACK_ROSE_URL="https://drive.google.com/drive/folders/1WGzP0HfWejTGTtg1ZpA5rrA7rbqUvsKg?usp=sharing"
LOVE_HURTS_URL="https://drive.google.com/drive/folders/1y65BFdgDQRNJ167W5dQLGf7hMo79ekER?usp=drive_link"
SIGNATURE_URL="https://drive.google.com/drive/folders/1aVIyi3ThdYldZVrLKkjNYNX2bNkNfna4?usp=drive_link"

# Check for dry run mode
DRY_RUN_FLAG=""
if [ "$1" == "--dry-run" ]; then
    DRY_RUN_FLAG="--dry-run"
    echo "🔍 DRY RUN MODE - No uploads will be performed"
    echo ""
fi

# Collection 1: BLACK_ROSE
echo "📂 Processing BLACK_ROSE Collection..."
python3 scripts/upload_drive_to_woocommerce.py \
    --drive-url "$BLACK_ROSE_URL" \
    --collection BLACK_ROSE \
    $DRY_RUN_FLAG

echo ""
echo "✅ BLACK_ROSE complete!"
echo ""
echo "---"
echo ""

# Collection 2: LOVE_HURTS
echo "📂 Processing LOVE_HURTS Collection..."
python3 scripts/upload_drive_to_woocommerce.py \
    --drive-url "$LOVE_HURTS_URL" \
    --collection LOVE_HURTS \
    $DRY_RUN_FLAG

echo ""
echo "✅ LOVE_HURTS complete!"
echo ""
echo "---"
echo ""

# Collection 3: SIGNATURE
echo "📂 Processing SIGNATURE Collection..."
python3 scripts/upload_drive_to_woocommerce.py \
    --drive-url "$SIGNATURE_URL" \
    --collection SIGNATURE \
    $DRY_RUN_FLAG

echo ""
echo "✅ SIGNATURE complete!"
echo ""
echo "=================================="
echo "🎉 All collections processed!"
echo ""

if [ -z "$DRY_RUN_FLAG" ]; then
    echo "🔗 View products in WooCommerce:"
    echo "   https://skyyrose.co/wp-admin/edit.php?post_type=product"
else
    echo "💡 Run without --dry-run to perform actual uploads"
fi
