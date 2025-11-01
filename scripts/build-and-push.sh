#!/bin/bash
# DevSkyy Enterprise - Docker Build and Push Script
# Builds AMD64 image and pushes to Docker Cloud: cloud://skyyrosellc/devskyy_linux-amd64

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DevSkyy Enterprise - Docker Build${NC}"
echo -e "${GREEN}========================================${NC}"

# Configuration
DOCKER_REGISTRY="${DOCKER_REGISTRY:-cloud://skyyrosellc}"
IMAGE_NAME="devskyy_linux-amd64"
VERSION="${VERSION:-5.1.0}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Full image names
FULL_IMAGE="${DOCKER_REGISTRY}/${IMAGE_NAME}"
TAGGED_IMAGE="${FULL_IMAGE}:${VERSION}"
LATEST_IMAGE="${FULL_IMAGE}:latest"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Registry: ${DOCKER_REGISTRY}"
echo "  Image: ${IMAGE_NAME}"
echo "  Version: ${VERSION}"
echo "  Git Commit: ${GIT_COMMIT}"
echo "  Build Date: ${BUILD_DATE}"
echo ""

# Check if Dockerfile exists
if [ ! -f "Dockerfile.production" ]; then
    echo -e "${RED}Error: Dockerfile.production not found${NC}"
    exit 1
fi

# Build the image
echo -e "${GREEN}Step 1: Building Docker image...${NC}"
docker build \
    --platform linux/amd64 \
    -f Dockerfile.production \
    -t "${TAGGED_IMAGE}" \
    -t "${LATEST_IMAGE}" \
    --build-arg VERSION="${VERSION}" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg GIT_COMMIT="${GIT_COMMIT}" \
    --no-cache \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

# Show image size
echo ""
echo -e "${YELLOW}Image Details:${NC}"
docker images "${FULL_IMAGE}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Tag for registry
echo ""
echo -e "${GREEN}Step 2: Tagging images...${NC}"
echo "  ${TAGGED_IMAGE}"
echo "  ${LATEST_IMAGE}"

# Push to registry
echo ""
echo -e "${GREEN}Step 3: Pushing to Docker Cloud...${NC}"

# Login to registry (if credentials provided)
if [ -n "${DOCKER_USERNAME}" ] && [ -n "${DOCKER_PASSWORD}" ]; then
    echo -e "${YELLOW}Logging in to Docker Cloud...${NC}"
    echo "${DOCKER_PASSWORD}" | docker login "${DOCKER_REGISTRY}" -u "${DOCKER_USERNAME}" --password-stdin
fi

# Push versioned tag
echo -e "${YELLOW}Pushing ${TAGGED_IMAGE}...${NC}"
docker push "${TAGGED_IMAGE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Pushed ${VERSION} tag${NC}"
else
    echo -e "${RED}✗ Failed to push ${VERSION} tag${NC}"
    exit 1
fi

# Push latest tag
echo -e "${YELLOW}Pushing ${LATEST_IMAGE}...${NC}"
docker push "${LATEST_IMAGE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Pushed latest tag${NC}"
else
    echo -e "${RED}✗ Failed to push latest tag${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build and Push Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Image available at:"
echo "  ${TAGGED_IMAGE}"
echo "  ${LATEST_IMAGE}"
echo ""
echo "Deploy with:"
echo "  docker pull ${TAGGED_IMAGE}"
echo "  docker run -d -p 8000:8000 ${TAGGED_IMAGE}"
echo ""
