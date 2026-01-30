#!/bin/bash
# Stop WordPress Playground server by PID
# Usage: stop-server.sh <pid>

set -e

if [ -z "$1" ]; then
    echo "error: PID required" >&2
    echo "Usage: stop-server.sh <pid>" >&2
    exit 1
fi

PID="$1"

# Check if process exists
if ! kill -0 "$PID" 2>/dev/null; then
    echo "error: Process $PID not found" >&2
    exit 1
fi

# Send SIGTERM for graceful shutdown
kill "$PID" 2>/dev/null

# Wait briefly for process to exit
for i in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "stopped:$PID"
        exit 0
    fi
    sleep 0.5
done

# Force kill if still running
kill -9 "$PID" 2>/dev/null || true
echo "stopped:$PID"
exit 0
