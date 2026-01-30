#!/bin/bash
# Start WordPress Playground server and wait for it to be ready
# Usage: start-server.sh [options]
# Options are passed directly to @wp-playground/cli server
# Example: start-server.sh --login --port 9400 --auto-mount /path/to/plugin

set -e

# Default timeout in seconds
TIMEOUT=${WP_PLAYGROUND_TIMEOUT:-60}

# Create a temp file for output
OUTPUT_FILE=$(mktemp)
trap "rm -f '$OUTPUT_FILE'" EXIT

# Start the server in background
# Use the experimental multi-worker support by default
# because possible data corruption is not a concern for ephemeral playgrounds.
npx --yes @wp-playground/cli server --experimental-multi-worker "$@" > "$OUTPUT_FILE" 2>&1 &
SERVER_PID=$!

# Wait for ready message or error
START_TIME=$(date +%s)
while true; do
    # Check if process is still running
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "error: Server process exited unexpectedly" >&2
        cat "$OUTPUT_FILE" >&2
        exit 1
    fi

    # Check for ready message
    if grep -q "WordPress is running on" "$OUTPUT_FILE" 2>/dev/null; then
        URL=$(grep "WordPress is running on" "$OUTPUT_FILE" | sed 's/.*WordPress is running on //' | awk '{print $1}')
        echo "pid:$SERVER_PID"
        echo "url:$URL"
        exit 0
    fi

    # Check for common errors
    if grep -q "EADDRINUSE" "$OUTPUT_FILE" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        echo "error: Port already in use" >&2
        exit 1
    fi

    # Check timeout
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
        echo "error: Timeout waiting for server to start" >&2
        cat "$OUTPUT_FILE" >&2
        exit 1
    fi

    sleep 0.5
done
