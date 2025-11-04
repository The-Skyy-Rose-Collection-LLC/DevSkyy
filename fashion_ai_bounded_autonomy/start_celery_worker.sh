#!/bin/bash
# Celery Worker Startup Script for Bounded Autonomy System
#
# This script starts Celery workers and beat scheduler for async task processing.
# All tasks respect bounded autonomy principles and require proper approvals.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
CELERY_APP="fashion_ai_bounded_autonomy.celery_app:celery_app"
LOG_DIR="logs/celery"
PID_DIR="logs/celery/pids"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

echo -e "${GREEN}Starting Bounded Autonomy Celery Workers${NC}"
echo "========================================"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Redis is not running!${NC}"
    echo "Start Redis with: redis-server --daemonize yes"
    exit 1
fi

echo -e "${GREEN}✅ Redis is running${NC}"

# Function to start a worker
start_worker() {
    local queue=$1
    local concurrency=$2
    local worker_name="bounded_autonomy_${queue}"

    echo -e "${YELLOW}Starting worker for queue: ${queue}${NC}"

    celery -A "$CELERY_APP" worker \
        --queue="$queue" \
        --concurrency="$concurrency" \
        --loglevel=info \
        --logfile="$LOG_DIR/${worker_name}.log" \
        --pidfile="$PID_DIR/${worker_name}.pid" \
        --hostname="${worker_name}@%h" \
        --detach

    echo -e "${GREEN}✅ Worker started for queue: ${queue}${NC}"
}

# Start workers for different queues
echo ""
echo "Starting queue workers..."
echo "------------------------"

# High priority queue (approvals, notifications)
start_worker "bounded_autonomy_high_priority" 4

# Default queue (general tasks)
start_worker "bounded_autonomy_default" 2

# Reports queue (report generation)
start_worker "bounded_autonomy_reports" 2

# Monitoring queue (health checks, metrics)
start_worker "bounded_autonomy_monitoring" 2

# Data processing queue (data ingestion, validation)
start_worker "bounded_autonomy_data_processing" 2

echo ""
echo "Starting Celery Beat scheduler..."
echo "--------------------------------"

# Start Celery Beat for periodic tasks
celery -A "$CELERY_APP" beat \
    --loglevel=info \
    --logfile="$LOG_DIR/celery_beat.log" \
    --pidfile="$PID_DIR/celery_beat.pid" \
    --detach

echo -e "${GREEN}✅ Celery Beat scheduler started${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All Celery workers started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Logs directory: $LOG_DIR"
echo "PIDs directory: $PID_DIR"
echo ""
echo "To monitor workers:"
echo "  celery -A $CELERY_APP inspect active"
echo "  celery -A $CELERY_APP inspect stats"
echo ""
echo "To stop all workers:"
echo "  ./fashion_ai_bounded_autonomy/stop_celery_worker.sh"
echo ""
