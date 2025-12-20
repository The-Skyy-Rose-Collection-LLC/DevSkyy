#!/bin/bash
# Local DAST Testing Script for DevSkyy
# This script simulates the CI/CD DAST workflow locally

set -e

echo "========================================="
echo "DevSkyy DAST Local Test Script"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "main_enterprise.py" ]; then
    echo -e "${RED}Error: Please run this script from the DevSkyy project root${NC}"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${YELLOW}Warning: docker-compose not found, trying docker compose${NC}"
    if ! docker compose version >/dev/null 2>&1; then
        echo -e "${RED}Error: Neither docker-compose nor 'docker compose' is available${NC}"
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}All prerequisites met${NC}"
echo ""

# Start services
echo "Starting PostgreSQL and Redis services..."
$DOCKER_COMPOSE up -d postgres redis

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
until docker exec $(docker ps -qf "name=postgres") pg_isready -U devskyy 2>/dev/null; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}PostgreSQL is ready${NC}"

# Check Redis
until docker exec $(docker ps -qf "name=redis") redis-cli ping 2>/dev/null; do
    echo "Waiting for Redis..."
    sleep 2
done
echo -e "${GREEN}Redis is ready${NC}"
echo ""

# Set environment variables
export DATABASE_URL="postgresql://devskyy:devskyy@localhost:5432/devskyy"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET_KEY="test-secret-key-for-dast-scanning"
export ENCRYPTION_MASTER_KEY=""
export DEBUG="false"
export ENVIRONMENT="testing"

# Install Python dependencies if needed
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment and installing dependencies..."
source .venv/bin/activate
pip install -q -e ".[dev]"

# Start the application
echo "Starting DevSkyy application..."
uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --log-level info > uvicorn.log 2>&1 &
APP_PID=$!
echo "Application PID: $APP_PID"

# Wait for application to be ready
echo "Waiting for application to start..."
MAX_ATTEMPTS=30
for i in $(seq 1 $MAX_ATTEMPTS); do
    if curl -f http://localhost:8000/health 2>/dev/null; then
        echo -e "${GREEN}Application is ready!${NC}"
        break
    fi
    echo "Attempt $i/$MAX_ATTEMPTS: Application not ready yet..."
    sleep 2

    if [ $i -eq $MAX_ATTEMPTS ]; then
        echo -e "${RED}Application failed to start. Logs:${NC}"
        cat uvicorn.log
        kill $APP_PID 2>/dev/null || true
        $DOCKER_COMPOSE down
        exit 1
    fi
done
echo ""

# Run ZAP scan
echo "========================================="
echo "Running OWASP ZAP Scan"
echo "========================================="

if docker pull zaproxy/zap-stable; then
    echo "Running ZAP full scan..."
    docker run --network=host -v $(pwd):/zap/wrk/:rw \
        -t zaproxy/zap-stable zap-full-scan.py \
        -t http://localhost:8000 \
        -r /zap/wrk/zap-report.html \
        -J /zap/wrk/zap-report.json \
        -w /zap/wrk/zap-report.md \
        -c /zap/wrk/.zap/rules.tsv \
        -d || echo -e "${YELLOW}ZAP scan completed with warnings${NC}"

    echo -e "${GREEN}ZAP scan complete. Reports generated:${NC}"
    echo "  - zap-report.html"
    echo "  - zap-report.json"
    echo "  - zap-report.md"
else
    echo -e "${YELLOW}Failed to pull ZAP image, skipping ZAP scan${NC}"
fi
echo ""

# Run Nuclei scan
echo "========================================="
echo "Running Nuclei Scan"
echo "========================================="

if command_exists nuclei; then
    echo "Updating Nuclei templates..."
    nuclei -update-templates -silent

    echo "Running Nuclei scan..."
    nuclei -u http://localhost:8000 \
        -severity critical,high,medium \
        -tags cve,exposure,misconfig,vulnerability \
        -stats \
        -json -o nuclei-report.json \
        -markdown-export nuclei-report.md \
        -silent || echo -e "${YELLOW}Nuclei scan completed with findings${NC}"

    echo -e "${GREEN}Nuclei scan complete. Reports generated:${NC}"
    echo "  - nuclei-report.json"
    echo "  - nuclei-report.md"
else
    echo -e "${YELLOW}Nuclei not installed. Install from: https://github.com/projectdiscovery/nuclei${NC}"
fi
echo ""

# Cleanup
echo "========================================="
echo "Cleaning up"
echo "========================================="

echo "Stopping application..."
kill $APP_PID 2>/dev/null || true

echo "Stopping services..."
$DOCKER_COMPOSE down

echo -e "${GREEN}Cleanup complete${NC}"
echo ""

# Summary
echo "========================================="
echo "DAST Scan Summary"
echo "========================================="
echo ""
echo "Reports generated:"
echo ""
if [ -f "zap-report.html" ]; then
    echo -e "${GREEN}ZAP Reports:${NC}"
    echo "  HTML: zap-report.html"
    echo "  JSON: zap-report.json"
    echo "  MD:   zap-report.md"
    echo ""
    echo "View HTML report with:"
    echo "  open zap-report.html    # macOS"
    echo "  xdg-open zap-report.html # Linux"
    echo ""
fi

if [ -f "nuclei-report.json" ]; then
    echo -e "${GREEN}Nuclei Reports:${NC}"
    echo "  JSON: nuclei-report.json"
    echo "  MD:   nuclei-report.md"
    echo ""
    echo "View Markdown report with:"
    echo "  cat nuclei-report.md"
    echo ""
fi

echo -e "${GREEN}DAST testing complete!${NC}"
echo ""
echo "Application logs available in: uvicorn.log"
