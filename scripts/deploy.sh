#!/bin/bash
# Deployment Script for DevSkyy
# Complete deployment pipeline: build -> push -> deploy

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 DevSkyy Complete Deployment Pipeline${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# Load environment variables
if [ -f .env ]; then
    source .env
    echo -e "${GREEN}✅ Loaded .env configuration${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Get version
VERSION=$(grep "version=" main.py | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')
if [ -z "$VERSION" ]; then
    VERSION="5.1.0"
fi

echo ""
echo -e "${BLUE}Deployment Configuration:${NC}"
echo "  Version:      ${VERSION}"
echo "  Registry:     ${REGISTRY}"
echo "  Image:        ${IMAGE_NAME}"
echo "  Deploy Mode:  ${DEPLOY_MODE}"
echo ""

# Confirmation
read -p "$(echo -e ${YELLOW}Continue with deployment? [y/N]: ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

# Step 1: Run deployment verification
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1/5: Deployment Verification${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

python deployment_verification.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment verification failed${NC}"
    echo "Fix issues before deploying"
    exit 1
fi

echo -e "${GREEN}✅ Verification passed${NC}"

# Step 2: Build Docker image
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 2/5: Building Docker Image${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

./scripts/docker-build.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Step 3: Test Docker image locally
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 3/5: Testing Docker Image${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# Start test container
TEST_CONTAINER="devskyy-test"
docker run -d \
    --name "${TEST_CONTAINER}" \
    -p 9000:8000 \
    --env-file .env \
    -e ENVIRONMENT=testing \
    "${IMAGE_NAME}:latest" >/dev/null 2>&1

echo "Waiting for container to start..."
sleep 5

# Test health endpoint
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/health)

if [ "${HEALTH_CHECK}" == "200" ]; then
    echo -e "${GREEN}✅ Container health check passed${NC}"
else
    echo -e "${RED}❌ Container health check failed (HTTP ${HEALTH_CHECK})${NC}"
    docker logs "${TEST_CONTAINER}"
    docker stop "${TEST_CONTAINER}" >/dev/null 2>&1
    docker rm "${TEST_CONTAINER}" >/dev/null 2>&1
    exit 1
fi

# Cleanup test container
docker stop "${TEST_CONTAINER}" >/dev/null 2>&1
docker rm "${TEST_CONTAINER}" >/dev/null 2>&1

# Step 4: Push to registry
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 4/5: Pushing to Registry${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

./scripts/docker-push.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker push failed${NC}"
    exit 1
fi

# Step 5: Deploy based on mode
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 5/5: Deploying Application${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

case "${DEPLOY_MODE}" in
    docker)
        echo -e "${BLUE}Deploying via Docker...${NC}"
        echo ""
        echo "Deployment complete! Image available at:"
        echo "  ${IMAGE_NAME}:${VERSION}"
        echo "  ${IMAGE_NAME}:latest"
        echo ""
        echo "To deploy on server, run:"
        echo "  docker pull ${IMAGE_NAME}:latest"
        echo "  docker run -d -p 8000:8000 --env-file .env ${IMAGE_NAME}:latest"
        ;;

    kubernetes)
        echo -e "${BLUE}Deploying to Kubernetes...${NC}"
        if [ -f "k8s/deployment.yaml" ]; then
            kubectl apply -f k8s/
            echo -e "${GREEN}✅ Kubernetes deployment updated${NC}"
        else
            echo -e "${YELLOW}⚠️  Kubernetes manifests not found${NC}"
        fi
        ;;

    cloud)
        echo -e "${BLUE}Deploying to cloud...${NC}"
        echo "Image available in registry, ready for cloud deployment"
        ;;

    *)
        echo -e "${YELLOW}Unknown deploy mode: ${DEPLOY_MODE}${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "Deployment Summary:"
echo "  Version:  ${VERSION}"
echo "  Image:    ${IMAGE_NAME}"
echo "  Registry: ${REGISTRY}"
echo "  Status:   Deployed ✅"
echo ""
echo "Next steps:"
echo "  Monitor logs:    docker logs -f <container_name>"
echo "  Health check:    curl http://your-server:8000/health"
echo "  API docs:        http://your-server:8000/docs"
