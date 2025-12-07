#!/bin/bash
# DevSkyy Docker Security Verification Script
# Builds all Docker images and verifies security package versions
# Per SECURITY_SCAN_REPORT_20251118.md

set -e

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║         DevSkyy Docker Security Verification                             ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Required versions
REQUIRED_PIP="25.3"
REQUIRED_CRYPTO="46.0.3"
REQUIRED_SETUPTOOLS="78.1.1"

# Function to verify package version
verify_package() {
    local image=$1
    local package=$2
    local required_version=$3
    
    echo -n "  Checking ${package} in ${image}... "
    
    # Get installed version
    version=$(docker run --rm ${image} pip list 2>/dev/null | grep "^${package}" | awk '{print $2}')
    
    if [ -z "$version" ]; then
        echo -e "${RED}NOT FOUND${NC}"
        return 1
    fi
    
    # Compare versions (simple comparison, works for most cases)
    if [ "$(printf '%s\n' "$required_version" "$version" | sort -V | head -n1)" = "$required_version" ]; then
        echo -e "${GREEN}✓ ${version}${NC} (required: ≥${required_version})"
        return 0
    else
        echo -e "${RED}✗ ${version}${NC} (required: ≥${required_version})"
        return 1
    fi
}

# Build images
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "BUILDING DOCKER IMAGES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

IMAGES=(
    "Dockerfile:devskyy:latest"
    "Dockerfile.production:devskyy:production"
    "Dockerfile.mcp:devskyy:mcp"
    "Dockerfile.multimodel:devskyy:multimodel"
)

for image_def in "${IMAGES[@]}"; do
    IFS=':' read -r dockerfile tag <<< "$image_def"
    echo "Building ${tag} from ${dockerfile}..."
    
    if docker build -f ${dockerfile} -t ${tag} . > /tmp/build_${tag//:/_}.log 2>&1; then
        echo -e "${GREEN}✓ Build successful${NC}"
    else
        echo -e "${RED}✗ Build failed - see /tmp/build_${tag//:/_}.log${NC}"
        exit 1
    fi
    echo ""
done

# Verify security packages
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "VERIFYING SECURITY PACKAGES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

all_passed=0

for image_def in "${IMAGES[@]}"; do
    IFS=':' read -r dockerfile tag <<< "$image_def"
    echo "Verifying ${tag}:"
    
    passed=0
    verify_package "$tag" "pip" "$REQUIRED_PIP" && ((passed++)) || true
    verify_package "$tag" "cryptography" "$REQUIRED_CRYPTO" && ((passed++)) || true
    verify_package "$tag" "setuptools" "$REQUIRED_SETUPTOOLS" && ((passed++)) || true
    
    if [ $passed -eq 3 ]; then
        echo -e "${GREEN}✓ All security packages verified${NC}"
        ((all_passed++))
    else
        echo -e "${RED}✗ Some packages failed verification${NC}"
    fi
    echo ""
done

# Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $all_passed -eq 4 ]; then
    echo -e "${GREEN}✓ ALL IMAGES VERIFIED SUCCESSFULLY${NC}"
    echo ""
    echo "Security Status:"
    echo "  • CVE-2025-8869 (pip):              FIXED ✓"
    echo "  • CVE-2024-26130 (cryptography):    FIXED ✓"
    echo "  • CVE-2023-50782 (cryptography):    FIXED ✓"
    echo "  • CVE-2024-0727 (cryptography):     FIXED ✓"
    echo "  • GHSA-h4gh-qq45-vh27 (cryptography): FIXED ✓"
    echo "  • CVE-2025-47273 (setuptools):      FIXED ✓"
    echo "  • CVE-2024-6345 (setuptools):       FIXED ✓"
    echo ""
    echo -e "${GREEN}CRITICAL CVE COUNT: 0${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Tag images for production:"
    echo "     docker tag devskyy:production devskyy:v5.1.0"
    echo ""
    echo "  2. Push to registry:"
    echo "     docker push devskyy:production"
    echo ""
    echo "  3. Deploy to production:"
    echo "     kubectl rollout restart deployment/devskyy-production"
    exit 0
else
    echo -e "${RED}✗ VERIFICATION FAILED${NC}"
    echo ""
    echo "Some images failed security package verification."
    echo "Please review the output above and rebuild affected images."
    exit 1
fi
