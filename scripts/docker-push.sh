#!/bin/bash
# Docker Push Script for DevSkyy
# Pushes production Docker image to registry

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 DevSkyy Docker Push Script${NC}"
echo "================================"

# Load environment variables
if [ -f .env ]; then
    source .env
    echo -e "${GREEN}✅ Loaded .env configuration${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Check required variables
if [ -z "$REGISTRY_USERNAME" ] || [ -z "$REGISTRY_TOKEN" ]; then
    echo -e "${RED}❌ Missing registry credentials${NC}"
    echo "Required: REGISTRY_USERNAME and REGISTRY_TOKEN in .env"
    exit 1
fi

# Set defaults
REGISTRY=${REGISTRY:-docker.io}
IMAGE_NAME=${IMAGE_NAME:-docker.io/skyyrosellc/devskyy}

# Get version
VERSION=$(grep "version=" main.py | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')
if [ -z "$VERSION" ]; then
    VERSION="5.1.0"
fi

echo ""
echo -e "${BLUE}Push Configuration:${NC}"
echo "  Registry: ${REGISTRY}"
echo "  Image:    ${IMAGE_NAME}"
echo "  Version:  ${VERSION}"
echo ""

# Login to Docker registry
echo -e "${BLUE}🔐 Logging in to Docker registry...${NC}"
echo "${REGISTRY_TOKEN}" | docker login "${REGISTRY}" -u "${REGISTRY_USERNAME}" --password-stdin

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker login failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker login successful${NC}"

# Push images
echo ""
echo -e "${BLUE}📤 Pushing images to registry...${NC}"

# Push latest
echo -e "${YELLOW}Pushing ${IMAGE_NAME}:latest...${NC}"
docker push "${IMAGE_NAME}:latest"

# Push version
echo -e "${YELLOW}Pushing ${IMAGE_NAME}:${VERSION}...${NC}"
docker push "${IMAGE_NAME}:${VERSION}"

# Push date tag
DATE_TAG="$(date +%Y%m%d)"
echo -e "${YELLOW}Pushing ${IMAGE_NAME}:${DATE_TAG}...${NC}"
docker push "${IMAGE_NAME}:${DATE_TAG}"

echo ""
echo -e "${GREEN}✅ All images pushed successfully!${NC}"
echo ""
echo "Published tags:"
echo "  - ${IMAGE_NAME}:latest"
echo "  - ${IMAGE_NAME}:${VERSION}"
echo "  - ${IMAGE_NAME}:${DATE_TAG}"
echo ""
echo "Next steps:"
echo "  Pull and run: docker pull ${IMAGE_NAME}:latest"
echo "  Deploy: ./scripts/deploy.sh"
