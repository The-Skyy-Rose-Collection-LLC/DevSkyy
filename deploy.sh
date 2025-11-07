#!/bin/bash
# DevSkyy Production Deployment Script
# This script automates the Docker build, test, and deployment process
# Usage: ./deploy.sh [environment]
# Environment: production (default), staging, development

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
IMAGE_NAME="devskyy-enterprise"
IMAGE_TAG="${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
CONTAINER_NAME="devskyy-${ENVIRONMENT}"
HEALTH_CHECK_URL="http://localhost:8000/health"
MAX_HEALTH_CHECK_ATTEMPTS=30
HEALTH_CHECK_INTERVAL=2

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DevSkyy Production Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${ENVIRONMENT}"
echo -e "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo -e "Container: ${CONTAINER_NAME}"
echo ""

# Step 1: Validate environment file
echo -e "${YELLOW}[1/8] Validating environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ ERROR: .env file not found${NC}"
    echo "Please create .env from .env.production.example and fill in all required values"
    exit 1
fi

# Check required variables
REQUIRED_VARS=("SECRET_KEY" "DATABASE_URL" "REDIS_URL")
for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=$" .env; then
        echo -e "${RED}❌ ERROR: ${var} is not set in .env${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ Environment configuration valid${NC}"

# Step 2: Verify Python syntax
echo -e "${YELLOW}[2/8] Verifying Python syntax...${NC}"
SYNTAX_ERRORS=0
for file in $(find . -name "*.py" -path "./agent/*" -o -name "*.py" -path "./api/*" -o -name "*.py" -path "./core/*" -o -name "*.py" -path "./config/*" | head -50); do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}❌ Syntax error in: $file${NC}"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done

if [ $SYNTAX_ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Found ${SYNTAX_ERRORS} syntax errors${NC}"
    exit 1
fi
echo -e "${GREEN}✅ All Python files compile successfully${NC}"

# Step 3: Build Docker image
echo -e "${YELLOW}[3/8] Building Docker image...${NC}"
if [ -f "Dockerfile" ]; then
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest . || {
        echo -e "${RED}❌ Docker build failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Dockerfile not found${NC}"
    exit 1
fi

# Step 4: Stop existing container
echo -e "${YELLOW}[4/8] Stopping existing container...${NC}"
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker stop ${CONTAINER_NAME} || true
    docker rm ${CONTAINER_NAME} || true
    echo -e "${GREEN}✅ Existing container stopped${NC}"
else
    echo -e "${GREEN}✅ No existing container to stop${NC}"
fi

# Step 5: Start new container
echo -e "${YELLOW}[5/8] Starting new container...${NC}"
docker run -d \
    --name ${CONTAINER_NAME} \
    -p 8000:8000 \
    --env-file .env \
    --restart unless-stopped \
    ${IMAGE_NAME}:${IMAGE_TAG} || {
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
}
echo -e "${GREEN}✅ Container started${NC}"

# Step 6: Wait for container to be healthy
echo -e "${YELLOW}[6/8] Waiting for application to be healthy...${NC}"
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_HEALTH_CHECK_ATTEMPTS ]; do
    if curl -f -s ${HEALTH_CHECK_URL} > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is healthy${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep ${HEALTH_CHECK_INTERVAL}
done

if [ $ATTEMPT -eq $MAX_HEALTH_CHECK_ATTEMPTS ]; then
    echo -e "${RED}❌ Health check failed after ${MAX_HEALTH_CHECK_ATTEMPTS} attempts${NC}"
    echo "Container logs:"
    docker logs ${CONTAINER_NAME}
    exit 1
fi

# Step 7: Run health checks
echo -e "${YELLOW}[7/8] Running comprehensive health checks...${NC}"
if [ -f "./health_check.sh" ]; then
    bash ./health_check.sh || {
        echo -e "${RED}❌ Health checks failed${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}⚠️  health_check.sh not found, skipping detailed checks${NC}"
fi

# Step 8: Display deployment info
echo -e "${YELLOW}[8/8] Deployment complete${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Successful!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Container: ${CONTAINER_NAME}"
echo -e "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo -e "Health Check: ${HEALTH_CHECK_URL}"
echo -e ""
echo -e "API Documentation: http://localhost:8000/docs"
echo -e "OpenAPI Spec: http://localhost:8000/openapi.json"
echo -e ""
echo -e "Useful commands:"
echo -e "  View logs:    docker logs -f ${CONTAINER_NAME}"
echo -e "  Stop:         docker stop ${CONTAINER_NAME}"
echo -e "  Restart:      docker restart ${CONTAINER_NAME}"
echo -e "  Shell access: docker exec -it ${CONTAINER_NAME} /bin/bash"
echo ""
