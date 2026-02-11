#!/bin/bash
#
# HTML to WordPress Template Converter
# Converts SkyyRose standalone HTML files to WordPress PHP templates
#

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  HTML → WordPress Template Converter                        ║"
echo "║  SkyyRose Flagship Theme Build System                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

SOURCE_DIR="/Users/coreyfoster/Downloads/SKyyRose Flagship"
THEME_DIR="/Users/coreyfoster/Documents/GitHub/DevSkyy/skyyrose-flagship-theme"

# Convert signature-collection.html
echo "Converting: signature-collection.html"
echo "────────────────────────────────────────────────────────────────"

# Extract CSS
sed -n '/<style>/,/<\/style>/p' "$SOURCE_DIR/signature-collection.html" \
    | sed '1d;$d' \
    > "$THEME_DIR/assets/css/signature-collection-3d.css"
echo "✓ CSS extracted: assets/css/signature-collection-3d.css"

# Extract JavaScript
sed -n '/<script type="module">/,/<\/script>/p' "$SOURCE_DIR/signature-collection.html" \
    | sed '1d;$d' \
    > "$THEME_DIR/assets/js/signature-collection-3d.js"
echo "✓ JS extracted: assets/js/signature-collection-3d.js"

echo "✅ Conversion in progress..."
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Ready for manual template creation                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
