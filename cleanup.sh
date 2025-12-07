#!/bin/bash

# DevSkyy Repository Cleanup Script
# Run this script periodically to keep your repository and system clean

# Strict mode: Exit on error, undefined variables, and pipe failures
set -eEuo pipefail

# Trap for cleanup on error
trap 'echo "Error on line $LINENO. Cleanup failed."; exit 1' ERR

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
set +e  # Allow find to fail if no files found
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type f -name "*.pyd" -delete 2>/dev/null
set -e  # Re-enable strict error checking
print_success "Python cache cleaned"

# 2. Clean pytest cache
print_status "Cleaning pytest cache..."
set +e  # Allow find to fail if no files found
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null
find . -type f -name ".coverage" -delete 2>/dev/null
set -e  # Re-enable strict error checking
print_success "Pytest cache cleaned"

# 3. Clean other Python build artifacts
print_status "Cleaning Python build artifacts..."
set +e  # Allow rm to fail if directories don't exist
rm -rf build/ dist/ *.egg-info .eggs/ 2>/dev/null
set -e  # Re-enable strict error checking
print_success "Build artifacts cleaned"

# 4. Clean log files
print_status "Cleaning log files..."
set +e  # Allow cleanup operations to fail if no files exist
find . -type f -name "*.log" -delete 2>/dev/null
rm -rf logs/ 2>/dev/null
set -e  # Re-enable strict error checking
print_success "Log files cleaned"

# 5. Clean temporary files and backups
print_status "Cleaning temporary files and backups..."
set +e  # Allow cleanup operations to fail if no files exist
find . -type f \( -name "*.tmp" -o -name "*.temp" -o -name "*.bak" -o -name "*.backup" -o -name "*~" \) -delete 2>/dev/null
# Remove backup directories but preserve media
find . -type d \( -name "*backup*" -o -name "*emergency*" -o -name "*-EMERGENCY-*" \) ! -path "./wordpress-mastery/*" -exec rm -rf {} + 2>/dev/null
# Remove broken and duplicate main.py files
find . -type f -name "main.py.*" -not -name "main.py" -delete 2>/dev/null
find . -type f -name "*.broken*" -delete 2>/dev/null
set -e  # Re-enable strict error checking
print_success "Temporary files and backups cleaned"

# 6. Clean git repository
print_status "Optimizing git repository..."
set +e  # Git operations may fail in some environments
git gc --quiet 2>/dev/null
git prune --quiet 2>/dev/null
set -e  # Re-enable strict error checking
print_success "Git repository optimized"

# 7. Clean stale git lock files
print_status "Cleaning stale git lock files..."
set +e  # Lock files may not exist
find .git -name "*.lock" -delete 2>/dev/null
set -e  # Re-enable strict error checking
print_success "Git lock files cleaned"

# 8. Clean node_modules if present
if [ -d "node_modules" ]; then
    print_status "Node modules detected - consider running 'npm prune' manually"
fi

# 9. Clean Docker artifacts (if Docker is running)
if command -v docker &> /dev/null && docker info &> /dev/null; then
    print_status "Docker detected - consider running 'docker system prune' manually"
fi

# 10. Verifiable output summary
echo ""
print_status "Verifying cleanup results..."
set +e  # Allow verification commands to fail without stopping script
PYTHON_CACHES=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
BACKUP_FILES=$(find . -type f \( -name "*.backup*" -o -name "*.broken*" -o -name "main.py.*" \) 2>/dev/null | grep -v "./main.py" | wc -l | tr -d ' ')
TEMP_FILES=$(find . -type f \( -name "*.tmp" -o -name "*.temp" -o -name "*.bak" \) 2>/dev/null | wc -l | tr -d ' ')
set -e  # Re-enable strict error checking

if [ "$PYTHON_CACHES" = "0" ]; then
    print_success "✓ No Python cache directories found"
else
    print_status "⚠️  Found $PYTHON_CACHES Python cache directories (if -type d failed, these are gitignored)"
fi

if [ "$BACKUP_FILES" = "0" ]; then
    print_success "✓ No backup files found"
else
    print_status "⚠️  Found $BACKUP_FILES backup files remaining"
fi

if [ "$TEMP_FILES" = "0" ]; then
    print_success "✓ No temporary files found"
else
    print_status "⚠️  Found $TEMP_FILES temporary files remaining"
fi

echo ""
echo "==================================="
FINAL_SPACE=$(df -h . | tail -1 | awk '{print $4}')
print_success "Cleanup complete!"
echo "Final free space: $FINAL_SPACE"
echo "==================================="
