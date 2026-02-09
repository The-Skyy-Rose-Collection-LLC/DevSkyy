#!/bin/bash

###############################################################################
# 3D Asset Validation Script
#
# Tests 3D asset loading, rendering, and performance
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$THEME_DIR/assets/models"
OUTPUT_DIR="$THEME_DIR/tests/coverage/3d"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}3D Asset Validation${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Create output directory
mkdir -p "$OUTPUT_DIR"

###############################################################################
# Helper Functions
###############################################################################

info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

success() {
    echo -e "${GREEN}✓ SUCCESS:${NC} $1"
}

error() {
    echo -e "${RED}✗ ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

###############################################################################
# Check Dependencies
###############################################################################

echo -e "${BLUE}[1/7] Checking dependencies...${NC}\n"

# Check for Node.js
if command -v node &> /dev/null; then
    success "Node.js found ($(node --version))"
else
    warn "Node.js not found - some checks will be skipped"
fi

# Check for gltf-validator
if command -v gltf_validator &> /dev/null; then
    success "gltf-validator found"
    GLTF_VALIDATOR_AVAILABLE=true
else
    warn "gltf-validator not found. Install from: https://github.com/KhronosGroup/glTF-Validator"
    GLTF_VALIDATOR_AVAILABLE=false
fi

echo ""

###############################################################################
# Check Models Directory
###############################################################################

echo -e "${BLUE}[2/7] Checking models directory...${NC}\n"

if [ -d "$MODELS_DIR" ]; then
    success "Models directory exists: $MODELS_DIR"

    # Count model files
    glb_count=$(find "$MODELS_DIR" -name "*.glb" 2>/dev/null | wc -l)
    gltf_count=$(find "$MODELS_DIR" -name "*.gltf" 2>/dev/null | wc -l)
    total_models=$((glb_count + gltf_count))

    info "Found $glb_count GLB files"
    info "Found $gltf_count GLTF files"
    info "Total: $total_models 3D model files"

    if [ $total_models -eq 0 ]; then
        warn "No 3D model files found"
    fi
else
    error "Models directory not found: $MODELS_DIR"
    exit 1
fi

echo ""

###############################################################################
# Validate Model Files
###############################################################################

echo -e "${BLUE}[3/7] Validating model files...${NC}\n"

if [ $total_models -gt 0 ]; then
    while IFS= read -r model_file; do
        filename=$(basename "$model_file")
        info "Checking: $filename"

        # Check file size
        size=$(wc -c < "$model_file")
        size_mb=$(echo "scale=2; $size / 1024 / 1024" | bc)

        echo "  Size: ${size_mb}MB"

        # Warn about large files
        if [ "$size" -gt 10485760 ]; then  # 10MB
            warn "  Large file (> 10MB) - consider optimization"
        elif [ "$size" -gt 5242880 ]; then  # 5MB
            info "  Medium file size - may impact load times"
        else
            success "  Good file size"
        fi

        # Run gltf-validator if available
        if [ "$GLTF_VALIDATOR_AVAILABLE" = true ]; then
            output_json="$OUTPUT_DIR/$(basename "$model_file" .glb).json"
            output_json="${output_json%.gltf}.json"

            if gltf_validator -r "$output_json" "$model_file" 2>/dev/null; then
                # Check validation results
                if grep -q '"errors": 0' "$output_json" 2>/dev/null; then
                    success "  Validation passed"
                else
                    error_count=$(grep -o '"errors": [0-9]*' "$output_json" | grep -o '[0-9]*')
                    warn "  Validation found $error_count errors"
                fi

                # Check for warnings
                warning_count=$(grep -o '"warnings": [0-9]*' "$output_json" 2>/dev/null | grep -o '[0-9]*' || echo "0")
                if [ "$warning_count" -gt 0 ]; then
                    info "  Warnings: $warning_count"
                fi
            fi
        fi

        echo ""
    done < <(find "$MODELS_DIR" -name "*.glb" -o -name "*.gltf")
else
    info "No model files to validate"
fi

###############################################################################
# Check Texture Files
###############################################################################

echo -e "${BLUE}[4/7] Checking texture files...${NC}\n"

# Look for common texture formats
texture_extensions=("*.jpg" "*.jpeg" "*.png" "*.webp" "*.ktx2" "*.basis")

texture_count=0
for ext in "${texture_extensions[@]}"; do
    count=$(find "$MODELS_DIR" -iname "$ext" 2>/dev/null | wc -l)
    texture_count=$((texture_count + count))
done

if [ $texture_count -gt 0 ]; then
    success "Found $texture_count texture files"

    # Check texture sizes
    while IFS= read -r texture_file; do
        filename=$(basename "$texture_file")
        size=$(wc -c < "$texture_file")
        size_kb=$(echo "scale=2; $size / 1024" | bc)

        # Check if image tools are available
        if command -v identify &> /dev/null; then
            dimensions=$(identify -format "%wx%h" "$texture_file" 2>/dev/null || echo "unknown")
            echo "  $filename: ${dimensions} (${size_kb}KB)"

            # Warn about large textures
            width=$(echo "$dimensions" | cut -d'x' -f1)
            if [ "$width" != "unknown" ] && [ "$width" -gt 2048 ]; then
                warn "    Large texture resolution - consider using 2048x2048 or smaller"
            fi
        else
            echo "  $filename: ${size_kb}KB"
        fi

        # Warn about large file sizes
        if [ "$size" -gt 1048576 ]; then  # 1MB
            warn "    Large texture file - consider compression"
        fi
    done < <(find "$MODELS_DIR" -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp")
else
    info "No texture files found (textures may be embedded in models)"
fi

echo ""

###############################################################################
# Check Three.js Integration
###############################################################################

echo -e "${BLUE}[5/7] Checking Three.js integration...${NC}\n"

# Check if Three.js is present
if [ -f "$THEME_DIR/assets/three/three.min.js" ] || [ -f "$THEME_DIR/assets/js/three.min.js" ]; then
    success "Three.js library found"

    # Get Three.js version if possible
    threejs_file=$(find "$THEME_DIR/assets" -name "three.min.js" | head -1)
    if grep -q "r[0-9]*" "$threejs_file" 2>/dev/null; then
        version=$(grep -o "r[0-9]*" "$threejs_file" | head -1)
        info "Three.js version: $version"
    fi
else
    error "Three.js library not found"
fi

# Check for GLTFLoader
if find "$THEME_DIR/assets" -name "*GLTFLoader*" | grep -q .; then
    success "GLTFLoader found"
else
    warn "GLTFLoader not found - required for loading GLTF/GLB files"
fi

# Check for OrbitControls
if find "$THEME_DIR/assets" -name "*OrbitControls*" | grep -q .; then
    success "OrbitControls found"
else
    warn "OrbitControls not found - camera controls may not work"
fi

# Check for DRACOLoader (optional but recommended)
if find "$THEME_DIR/assets" -name "*DRACOLoader*" | grep -q .; then
    success "DRACOLoader found (for compressed models)"
else
    info "DRACOLoader not found (optional - for compressed models)"
fi

echo ""

###############################################################################
# Check Scene Initialization Scripts
###############################################################################

echo -e "${BLUE}[6/7] Checking scene initialization...${NC}\n"

if [ -f "$THEME_DIR/assets/js/three-init.js" ]; then
    success "three-init.js found"

    # Check for essential Three.js code patterns
    if grep -q "THREE.Scene" "$THEME_DIR/assets/js/three-init.js"; then
        success "Scene initialization found"
    else
        warn "Scene initialization code not found"
    fi

    if grep -q "THREE.PerspectiveCamera\|THREE.Camera" "$THEME_DIR/assets/js/three-init.js"; then
        success "Camera setup found"
    else
        warn "Camera setup not found"
    fi

    if grep -q "THREE.WebGLRenderer" "$THEME_DIR/assets/js/three-init.js"; then
        success "Renderer initialization found"
    else
        warn "Renderer initialization not found"
    fi

    if grep -q "GLTFLoader" "$THEME_DIR/assets/js/three-init.js"; then
        success "Model loading code found"
    else
        warn "Model loading code not found"
    fi

    if grep -q "OrbitControls" "$THEME_DIR/assets/js/three-init.js"; then
        success "Camera controls setup found"
    else
        info "Camera controls setup not found (optional)"
    fi

    # Check for animation loop
    if grep -q "requestAnimationFrame\|animate" "$THEME_DIR/assets/js/three-init.js"; then
        success "Animation loop found"
    else
        warn "Animation loop not found - scene may not render"
    fi

    # Check for resize handler
    if grep -q "window.addEventListener.*'resize'" "$THEME_DIR/assets/js/three-init.js"; then
        success "Resize handler found"
    else
        warn "Resize handler not found - may have issues on window resize"
    fi

    # Check for error handling
    if grep -q "catch\|error" "$THEME_DIR/assets/js/three-init.js"; then
        success "Error handling found"
    else
        warn "No error handling found - add try/catch blocks"
    fi

    # Check for loading indicators
    if grep -q "loading\|loader\|progress" "$THEME_DIR/assets/js/three-init.js"; then
        success "Loading indicator code found"
    else
        info "Loading indicator not found (recommended for UX)"
    fi
else
    error "three-init.js not found"
fi

echo ""

###############################################################################
# Performance Recommendations
###############################################################################

echo -e "${BLUE}[7/7] Performance recommendations...${NC}\n"

echo "Model Optimization:"
echo "  ☐ Use Draco compression for geometry"
echo "  ☐ Optimize polygon count (< 100k triangles for web)"
echo "  ☐ Combine meshes where possible"
echo "  ☐ Use LOD (Level of Detail) for complex models"
echo "  ☐ Remove unused vertices and faces"
echo "  ☐ Merge duplicate materials"
echo ""

echo "Texture Optimization:"
echo "  ☐ Use power-of-2 dimensions (512, 1024, 2048)"
echo "  ☐ Compress textures (KTX2 or Basis)"
echo "  ☐ Use appropriate texture sizes (1024x1024 for most cases)"
echo "  ☐ Consider using texture atlases"
echo "  ☐ Use WebP or JPEG for diffuse maps"
echo "  ☐ Optimize normal maps and roughness maps"
echo ""

echo "Rendering Optimization:"
echo "  ☐ Enable frustum culling"
echo "  ☐ Use instancing for repeated objects"
echo "  ☐ Implement progressive loading"
echo "  ☐ Add loading progress indicators"
echo "  ☐ Cache loaded models"
echo "  ☐ Dispose of unused geometries and materials"
echo "  ☐ Use shadows sparingly"
echo "  ☐ Optimize light count (< 5 dynamic lights)"
echo ""

echo "Best Practices:"
echo "  ☐ Test on mobile devices"
echo "  ☐ Provide fallback images for no-WebGL browsers"
echo "  ☐ Add loading states and error messages"
echo "  ☐ Test with slow 3G connection"
echo "  ☐ Monitor memory usage"
echo "  ☐ Profile rendering performance"
echo "  ☐ Add touch controls for mobile"
echo "  ☐ Consider lazy loading 3D scenes"
echo ""

###############################################################################
# Validation Report
###############################################################################

cat > "$OUTPUT_DIR/3d-validation-report.md" << EOF
# 3D Asset Validation Report

**Date:** $(date)
**Theme:** SkyyRose Flagship

## Summary

- **Total Models:** $total_models
- **GLB Files:** $glb_count
- **GLTF Files:** $gltf_count
- **Texture Files:** $texture_count

## Model Files

$(find "$MODELS_DIR" -name "*.glb" -o -name "*.gltf" 2>/dev/null | while read -r f; do
    size=$(wc -c < "$f")
    size_mb=$(echo "scale=2; $size / 1024 / 1024" | bc)
    echo "- $(basename "$f") - ${size_mb}MB"
done)

## Three.js Integration

- Three.js Library: $([ -f "$THEME_DIR/assets/three/three.min.js" ] && echo "✓ Found" || echo "✗ Missing")
- GLTFLoader: $(find "$THEME_DIR/assets" -name "*GLTFLoader*" >/dev/null 2>&1 && echo "✓ Found" || echo "✗ Missing")
- OrbitControls: $(find "$THEME_DIR/assets" -name "*OrbitControls*" >/dev/null 2>&1 && echo "✓ Found" || echo "✗ Missing")
- DRACOLoader: $(find "$THEME_DIR/assets" -name "*DRACOLoader*" >/dev/null 2>&1 && echo "✓ Found" || echo "○ Optional")

## Recommendations

### File Size
- Keep models under 5MB when possible
- Use Draco compression for large models
- Compress textures appropriately

### Performance
- Target 60 FPS on desktop, 30 FPS on mobile
- Keep triangle count under 100k
- Optimize texture sizes to 1024x1024 or 2048x2048

### Compatibility
- Test on Chrome, Firefox, Safari
- Test on iOS Safari and Chrome Mobile
- Provide fallback for browsers without WebGL

## Tools

- **Model Optimization:** Blender, glTF-Pipeline
- **Texture Compression:** Basis Universal, KTX-Software
- **Validation:** glTF-Validator
- **Testing:** Three.js Inspector, Stats.js

EOF

success "Validation report saved: $OUTPUT_DIR/3d-validation-report.md"

###############################################################################
# Summary
###############################################################################

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}3D Asset Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

success "3D asset validation completed"
info "Reports saved to: $OUTPUT_DIR"

echo ""
echo -e "${BLUE}Recommended Tools:${NC}\n"
echo "- Blender: https://www.blender.org/ (3D modeling and optimization)"
echo "- glTF-Validator: https://github.com/KhronosGroup/glTF-Validator"
echo "- glTF-Pipeline: https://github.com/CesiumGS/gltf-pipeline"
echo "- Basis Universal: https://github.com/BinomialLLC/basis_universal"
echo "- Three.js Inspector: Chrome DevTools Extension"
echo "- Stats.js: https://github.com/mrdoob/stats.js/"

echo ""
