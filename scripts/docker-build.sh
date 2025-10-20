#!/bin/bash
# Docker Build Script for DevSkyy
# Builds production Docker image with proper versioning

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 DevSkyy Docker Build Script${NC}"
echo "================================"

# Load environment variables
if [ -f .env ]; then
    source .env
    echo -e "${GREEN}✅ Loaded .env configuration${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Set defaults
REGISTRY=${REGISTRY:-docker.io}
IMAGE_NAME=${IMAGE_NAME:-docker.io/skyyrosellc/devskyy}
DOCKERFILE=${DOCKERFILE:-Dockerfile.production}

# Get version from main.py
VERSION=$(grep "version=" main.py | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')
if [ -z "$VERSION" ]; then
    VERSION="5.1.0"
fi

# Build tags
TAG_LATEST="${IMAGE_NAME}:latest"
TAG_VERSION="${IMAGE_NAME}:${VERSION}"
TAG_DATE="${IMAGE_NAME}:$(date +%Y%m%d)"

echo ""
echo -e "${BLUE}Build Configuration:${NC}"
echo "  Registry:   ${REGISTRY}"
echo "  Image:      ${IMAGE_NAME}"
echo "  Version:    ${VERSION}"
echo "  Dockerfile: ${DOCKERFILE}"
echo ""

# Check if Dockerfile exists
if [ ! -f "${DOCKERFILE}" ]; then
    echo -e "${RED}❌ Dockerfile not found: ${DOCKERFILE}${NC}"
    exit 1
fi

# Build Docker image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build \
    --platform linux/amd64 \
    -f "${DOCKERFILE}" \
    -t "${TAG_LATEST}" \
    -t "${TAG_VERSION}" \
    -t "${TAG_DATE}" \
    --build-arg VERSION="${VERSION}" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
    echo ""
    echo "Tags created:"
    echo "  - ${TAG_LATEST}"
    echo "  - ${TAG_VERSION}"
    echo "  - ${TAG_DATE}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Show image size
echo ""
echo -e "${BLUE}📊 Image Information:${NC}"
docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo -e "${GREEN}✅ Build complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Test image: ./scripts/docker-run.sh"
echo "  2. Push to registry: ./scripts/docker-push.sh"
