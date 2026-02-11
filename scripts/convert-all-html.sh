#!/bin/bash
# Convert all 4 HTML files to WordPress templates

SOURCE_DIR="/Users/coreyfoster/Downloads/SKyyRose Flagship"
THEME_DIR="/Users/coreyfoster/Documents/GitHub/DevSkyy/skyyrose-flagship-theme"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  SkyyRose HTML → WordPress Converter                        ║"
echo "║  Converting all 4 collection templates                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Array of files to convert
declare -A FILES=(
    ["love-hurts-collection.html"]="love-hurts"
    ["black-rose-collection.html"]="black-rose"
    ["preorder-gateway.html"]="preorder-gateway"
)

# Function to convert a single HTML file
convert_html_file() {
    local html_file="$1"
    local slug="$2"
    
    echo "Converting: $html_file → $slug"
    echo "────────────────────────────────────────────────────────────────"
    
    local source_path="$SOURCE_DIR/$html_file"
    
    if [[ ! -f "$source_path" ]]; then
        echo "❌ ERROR: File not found: $source_path"
        echo ""
        return 1
    fi
    
    # Extract CSS (between <style> tags)
    sed -n '/<style>/,/<\/style>/p' "$source_path" \
        | sed '1d;$d' \
        > "$THEME_DIR/assets/css/${slug}-3d.css"
    
    local css_size=$(du -h "$THEME_DIR/assets/css/${slug}-3d.css" | cut -f1)
    echo "✓ CSS extracted: assets/css/${slug}-3d.css ($css_size)"
    
    # Extract JavaScript (between <script type="module"> tags)
    sed -n '/<script type="module">/,/<\/script>/p' "$source_path" \
        | sed '1d;$d' \
        > "$THEME_DIR/assets/js/${slug}-3d.js"
    
    local js_size=$(du -h "$THEME_DIR/assets/js/${slug}-3d.js" | cut -f1)
    echo "✓ JS extracted: assets/js/${slug}-3d.js ($js_size)"
    
    echo "✅ ${slug} conversion complete"
    echo ""
}

# Convert each file
for html_file in "${!FILES[@]}"; do
    convert_html_file "$html_file" "${FILES[$html_file]}"
done

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Extraction Complete - Ready for template creation          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
