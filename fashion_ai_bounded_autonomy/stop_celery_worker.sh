#!/bin/bash
# Celery Worker Stop Script for Bounded Autonomy System
#
# This script gracefully stops all Celery workers and the beat scheduler.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
CELERY_APP="fashion_ai_bounded_autonomy.celery_app:celery_app"
PID_DIR="logs/celery/pids"

echo -e "${YELLOW}Stopping Bounded Autonomy Celery Workers${NC}"
echo "========================================"

# Check if PID directory exists
if [ ! -d "$PID_DIR" ]; then
    echo -e "${RED}No PID directory found. Workers may not be running.${NC}"
    exit 1
fi

# stop_worker stops the Celery worker identified by the given PID file, attempts a graceful shutdown (waiting up to 10 seconds) and forces termination if necessary, then removes the PID file.
# Arguments: pid_file — path to the worker's `.pid` file.
stop_worker() {
    local pid_file=$1
    local worker_name=$(basename "$pid_file" .pid)

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping ${worker_name}...${NC}"
            kill -TERM "$pid"
            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${RED}Force stopping ${worker_name}${NC}"
                kill -KILL "$pid"
            fi
            rm -f "$pid_file"
            echo -e "${GREEN}✅ Stopped ${worker_name}${NC}"
        else
            echo -e "${YELLOW}⚠️  ${worker_name} not running (stale PID)${NC}"
            rm -f "$pid_file"
        fi
    fi
}

# Stop all workers
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        stop_worker "$pid_file"
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All Celery workers stopped successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""