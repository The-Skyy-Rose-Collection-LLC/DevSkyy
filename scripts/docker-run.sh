#!/bin/bash
# Docker Run Script for DevSkyy
# Runs production Docker image locally for testing

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 DevSkyy Docker Run Script${NC}"
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
IMAGE_NAME=${IMAGE_NAME:-docker.io/skyyrosellc/devskyy}
CONTAINER_NAME=${CONTAINER_NAME:-devskyy-dev}
PORT=${PORT:-8000}

echo ""
echo -e "${BLUE}Run Configuration:${NC}"
echo "  Image:     ${IMAGE_NAME}:latest"
echo "  Container: ${CONTAINER_NAME}"
echo "  Port:      ${PORT}"
echo ""

# Stop and remove existing container
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo -e "${YELLOW}Stopping existing container...${NC}"
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
fi

# Run Docker container
echo -e "${BLUE}🚀 Starting Docker container...${NC}"
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${PORT}:8000" \
    --env-file .env \
    -e ENVIRONMENT=development \
    -v "$(pwd)/logs:/app/logs" \
    --restart unless-stopped \
    --health-cmd="curl -f http://localhost:8000/health || exit 1" \
    --health-interval=30s \
    --health-timeout=10s \
    --health-retries=3 \
    "${IMAGE_NAME}:latest"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
    echo ""
    echo "Container Details:"
    docker ps -f name="${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker logs -f ${CONTAINER_NAME}"
    echo "  Stop:         docker stop ${CONTAINER_NAME}"
    echo "  Restart:      docker restart ${CONTAINER_NAME}"
    echo "  Shell access: docker exec -it ${CONTAINER_NAME} bash"
    echo ""
    echo "API Documentation:"
    echo "  http://localhost:${PORT}/docs"
    echo "  http://localhost:${PORT}/redoc"
    echo ""
    echo "Health Check:"
    echo "  http://localhost:${PORT}/health"

    # Wait a moment for container to start
    sleep 3

    # Show initial logs
    echo ""
    echo -e "${BLUE}📋 Initial logs:${NC}"
    docker logs --tail 20 "${CONTAINER_NAME}"

else
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi
