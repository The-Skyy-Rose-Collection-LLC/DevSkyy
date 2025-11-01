#!/bin/bash

# DevSkyy Repository Cleanup Script
# Run this script periodically to keep your repository and system clean

set -e

echo "==================================="
echo "DevSkyy Repository Cleanup Script"
echo "==================================="
echo ""

# Function to print status messages
print_status() {
    echo "→ $1"
}

print_success() {
    echo "✓ $1"
}

# Store initial disk space
INITIAL_SPACE=$(df -h . | tail -1 | awk '{print $4}')
print_status "Initial free space: $INITIAL_SPACE"
echo ""

# 1. Clean Python cache files
print_status "Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
print_success "Python cache cleaned"

# 2. Clean pytest cache
print_status "Cleaning pytest cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name ".coverage" -delete 2>/dev/null || true
print_success "Pytest cache cleaned"

# 3. Clean other Python build artifacts
print_status "Cleaning Python build artifacts..."
rm -rf build/ dist/ *.egg-info .eggs/ 2>/dev/null || true
print_success "Build artifacts cleaned"

# 4. Clean log files
print_status "Cleaning log files..."
find . -type f -name "*.log" -delete 2>/dev/null || true
rm -rf logs/ 2>/dev/null || true
print_success "Log files cleaned"

# 5. Clean temporary files
print_status "Cleaning temporary files..."
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.temp" -delete 2>/dev/null || true
find . -type f -name "*.bak" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true
print_success "Temporary files cleaned"

# 6. Clean git repository
print_status "Optimizing git repository..."
git gc --quiet 2>/dev/null || true
git prune --quiet 2>/dev/null || true
print_success "Git repository optimized"

# 7. Clean stale git lock files
print_status "Cleaning stale git lock files..."
find .git -name "*.lock" -delete 2>/dev/null || true
print_success "Git lock files cleaned"

# 8. Clean node_modules if present
if [ -d "node_modules" ]; then
    print_status "Node modules detected - consider running 'npm prune' manually"
fi

# 9. Clean Docker artifacts (if Docker is running)
if command -v docker &> /dev/null && docker info &> /dev/null; then
    print_status "Docker detected - consider running 'docker system prune' manually"
fi

echo ""
echo "==================================="
FINAL_SPACE=$(df -h . | tail -1 | awk '{print $4}')
print_success "Cleanup complete!"
echo "Final free space: $FINAL_SPACE"
echo "==================================="
