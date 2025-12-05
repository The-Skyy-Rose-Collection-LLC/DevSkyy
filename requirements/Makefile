# =============================================================================
# DEVSKYY - Dependency Management with pip-tools
# Reference: https://pip-tools.readthedocs.io/en/latest/
# =============================================================================
# Usage:
#   make compile      - Compile all .in files to .txt lock files
#   make upgrade      - Upgrade all dependencies to latest versions
#   make sync-dev     - Install development environment
#   make sync-test    - Install test environment
#   make sync-prod    - Install production environment
# =============================================================================

.PHONY: compile upgrade sync-dev sync-test sync-prod clean

# Python and pip-tools configuration
PYTHON := python3
PIP_COMPILE := pip-compile --strip-extras --generate-hashes --allow-unsafe
PIP_SYNC := pip-sync

# Compile all requirements files (order matters due to constraints)
compile: base.txt dev.txt test.txt
	@echo "✅ All requirements compiled successfully"

# Base production dependencies (must be compiled first)
base.txt: base.in
	@echo "📦 Compiling base.in -> base.txt..."
	$(PIP_COMPILE) base.in -o base.txt

# Development dependencies (depends on base.txt for constraints)
dev.txt: dev.in base.txt
	@echo "📦 Compiling dev.in -> dev.txt..."
	$(PIP_COMPILE) dev.in -o dev.txt

# Test dependencies (depends on base.txt for constraints)
test.txt: test.in base.txt
	@echo "📦 Compiling test.in -> test.txt..."
	$(PIP_COMPILE) test.in -o test.txt

# Upgrade all dependencies to latest compatible versions
upgrade:
	@echo "⬆️ Upgrading all dependencies..."
	$(PIP_COMPILE) --upgrade base.in -o base.txt
	$(PIP_COMPILE) --upgrade dev.in -o dev.txt
	$(PIP_COMPILE) --upgrade test.in -o test.txt
	@echo "✅ All dependencies upgraded"

# Sync development environment
sync-dev: compile
	@echo "🔄 Syncing development environment..."
	$(PIP_SYNC) base.txt dev.txt test.txt

# Sync test environment (CI/CD)
sync-test: compile
	@echo "🔄 Syncing test environment..."
	$(PIP_SYNC) base.txt test.txt

# Sync production environment
sync-prod: base.txt
	@echo "🔄 Syncing production environment..."
	$(PIP_SYNC) base.txt

# Clean compiled files
clean:
	@echo "🧹 Cleaning compiled requirements..."
	rm -f base.txt dev.txt test.txt
	@echo "✅ Cleaned"

# Verify lock files are up to date
verify:
	@echo "🔍 Verifying lock files are up to date..."
	$(PIP_COMPILE) --dry-run base.in -o base.txt
	$(PIP_COMPILE) --dry-run dev.in -o dev.txt
	$(PIP_COMPILE) --dry-run test.in -o test.txt
	@echo "✅ Lock files are up to date"
