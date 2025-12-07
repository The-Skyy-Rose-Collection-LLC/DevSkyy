#!/bin/bash
# DevSkyy Quick Start Script
# Run this to start the application in development mode
# Usage: ./start.sh [--docker] [--port PORT]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=${PORT:-8000}
USE_DOCKER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "  DevSkyy Platform v5.3.0"
echo "  Enterprise AI Fashion Platform"
echo "=========================================="
echo ""

if [ "$USE_DOCKER" = true ]; then
    echo "[*] Starting with Docker Compose..."

    # Check for docker-compose
    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
        echo "[-] Docker not found. Please install Docker first."
        exit 1
    fi

    # Build and start
    docker-compose up --build -d

    echo ""
    echo "[+] Docker containers starting..."
    echo "    API:       http://localhost:8000"
    echo "    Dashboard: http://localhost:8000/dashboard"
    echo "    Docs:      http://localhost:8000/docs"
    echo ""
    echo "    Use 'docker-compose logs -f' to view logs"
    echo "    Use 'docker-compose down' to stop"

else
    echo "[*] Starting in development mode..."

    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l 2>/dev/null || echo "0") == "1" ]]; then
        echo "[-] Python 3.11+ required. Found: $PYTHON_VERSION"
        exit 1
    fi

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "[*] Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    echo "[*] Activating virtual environment..."
    source venv/bin/activate

    # Install dependencies
    echo "[*] Installing dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements-minimal.txt

    # Create .env if it doesn't exist
    if [ ! -f ".env" ]; then
        echo "[*] Creating .env file from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
        else
            cat > .env << 'EOF'
# DevSkyy Development Environment
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./devskyy.db
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
EOF
        fi
        echo "    Created .env file with development defaults"
    fi

    # Create required directories
    mkdir -p logs data artifacts uploads

    echo ""
    echo "[+] Starting server on port $PORT..."
    echo ""
    echo "    Dashboard: http://localhost:$PORT/dashboard"
    echo "    API Docs:  http://localhost:$PORT/docs"
    echo "    Health:    http://localhost:$PORT/health"
    echo ""
    echo "    Press Ctrl+C to stop"
    echo "=========================================="
    echo ""

    # Start the server
    python -m uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
fi
