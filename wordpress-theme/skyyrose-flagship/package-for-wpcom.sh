#!/bin/bash
###############################################################################
# Package SkyyRose Flagship Theme for WordPress.com Upload
# Creates clean ZIP with only production files
###############################################################################

THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$HOME/Desktop/skyyrose-flagship-wpcom"
DIST_DIR="$HOME/Desktop"
VERSION="1.0.0"
THEME_NAME="skyyrose-flagship"

echo "=== Packaging SkyyRose Flagship for WordPress.com ==="
echo ""

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$THEME_NAME"

echo "Copying production files..."

# Copy theme files (exclude development files)
rsync -av "$THEME_DIR/" "$BUILD_DIR/$THEME_NAME/" \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='vendor' \
  --exclude='tests' \
  --exclude='.github' \
  --exclude='*.md' \
  --exclude='composer.json' \
  --exclude='composer.lock' \
  --exclude='package.json' \
  --exclude='package-lock.json' \
  --exclude='webpack.config.js' \
  --exclude='.gitignore' \
  --exclude='.DS_Store' \
  --exclude='*.py' \
  --exclude='*.sh' \
  --exclude='scripts' \
  --exclude='*.log' \
  --quiet

# Keep essential docs
cp "$THEME_DIR/README.md" "$BUILD_DIR/$THEME_NAME/" 2>/dev/null || true
cp "$THEME_DIR/readme.txt" "$BUILD_DIR/$THEME_NAME/"

echo "✓ Files copied"

# Verify required files
echo ""
echo "Verifying required files..."
required=("style.css" "index.php" "functions.php" "screenshot.png" "readme.txt")
all_present=true

for file in "${required[@]}"; do
    if [ -f "$BUILD_DIR/$THEME_NAME/$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
        all_present=false
    fi
done

if [ "$all_present" = false ]; then
    echo ""
    echo "ERROR: Required files missing. Aborting."
    exit 1
fi

# Create ZIP
echo ""
echo "Creating ZIP archive..."
cd "$BUILD_DIR"
zip -r "$DIST_DIR/${THEME_NAME}-${VERSION}-wpcom.zip" "$THEME_NAME/" -q

# Generate checksum
cd "$DIST_DIR"
shasum -a 256 "${THEME_NAME}-${VERSION}-wpcom.zip" > "${THEME_NAME}-${VERSION}-wpcom.zip.sha256"

# Get file size
FILE_SIZE=$(du -h "${THEME_NAME}-${VERSION}-wpcom.zip" | cut -f1)

echo "✓ ZIP created"
echo ""
echo "=== Package Complete ==="
echo ""
echo "📦 File: ${THEME_NAME}-${VERSION}-wpcom.zip"
echo "📊 Size: $FILE_SIZE"
echo "📍 Location: $DIST_DIR"
echo "🔐 Checksum: ${THEME_NAME}-${VERSION}-wpcom.zip.sha256"
echo ""
echo "=== WordPress.com Upload Instructions ==="
echo ""
echo "1. Go to your WordPress.com dashboard"
echo "2. Navigate to: Appearance > Themes"
echo "3. Click: Add New > Upload Theme"
echo "4. Select: ${THEME_NAME}-${VERSION}-wpcom.zip"
echo "5. Click: Install Now"
echo "6. Click: Activate"
echo ""
echo "✅ Ready for upload!"

# Cleanup
rm -rf "$BUILD_DIR"
