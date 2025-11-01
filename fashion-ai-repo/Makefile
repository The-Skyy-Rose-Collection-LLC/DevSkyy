# Fashion AI Repository - Autonomous Commerce Platform
# Makefile for local development and CI/CD

.PHONY: help setup install test lint format security audit all clean dc-up dc-down

# Colors
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Configuration
PYTHON := python3
PIP := $(PYTHON) -m pip
SRC_DIRS := src
TEST_DIRS := tests

help:
	@echo "$(BLUE)Fashion AI Repository - Make Commands$(RESET)"
	@echo "$(BLUE)======================================$(RESET)"
	@echo "$(GREEN)Setup:$(RESET)"
	@echo "  setup            - Complete setup (install dependencies)"
	@echo "  install          - Install production dependencies"
	@echo "  install-dev      - Install development dependencies"
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@echo "  all              - Run audits, generate manifests, map functions, and tests"
	@echo "  run              - Start API server"
	@echo "  run-agents       - Start all agents"
	@echo ""
	@echo "$(GREEN)Code Quality:$(RESET)"
	@echo "  format           - Format code with Black"
	@echo "  lint             - Run Ruff linting"
	@echo "  type-check       - Run MyPy type checking"
	@echo "  audit            - Run code quality audits"
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@echo "  test             - Run all tests"
	@echo "  test-cov         - Run tests with coverage"
	@echo ""
	@echo "$(GREEN)Security:$(RESET)"
	@echo "  security         - Run security scans (bandit, safety, pip-audit)"
	@echo ""
	@echo "$(GREEN)Docker:$(RESET)"
	@echo "  dc-up            - Start Docker services (Redis, Postgres)"
	@echo "  dc-down          - Stop Docker services"
	@echo ""
	@echo "$(GREEN)Utilities:$(RESET)"
	@echo "  clean            - Remove build artifacts and caches"
	@echo "  health-check     - Run system health check"

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

setup: install
	@echo "$(GREEN)Setup complete!$(RESET)"
	@echo "Run 'make dc-up' to start services, then 'make run' to start the API"

install:
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .
	@echo "$(GREEN)Installation complete!$(RESET)"

install-dev: install
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	$(PIP) install -e ".[dev,test,security]"
	@echo "$(GREEN)Development installation complete!$(RESET)"

# ============================================================================
# COMPREHENSIVE WORKFLOW
# ============================================================================

all: audit generate-manifests map-functions test
	@echo "$(GREEN)All tasks complete!$(RESET)"

audit: lint type-check security
	@echo "$(GREEN)Code audit complete!$(RESET)"

generate-manifests:
	@echo "$(BLUE)Generating manifests...$(RESET)"
	@mkdir -p artifacts
	@echo "timestamp: $$(date -Iseconds)" > artifacts/build-manifest.yaml
	@echo "version: $$(grep '^version' pyproject.toml | cut -d '=' -f2 | tr -d ' \"')" >> artifacts/build-manifest.yaml
	@echo "python: $$($(PYTHON) --version)" >> artifacts/build-manifest.yaml
	@echo "$(GREEN)Manifests generated in artifacts/$(RESET)"

map-functions:
	@echo "$(BLUE)Mapping functions and endpoints...$(RESET)"
	@mkdir -p artifacts
	@find src -name "*.py" -type f | xargs grep -h "^def \|^async def " > artifacts/function-map.txt || true
	@find src -name "*.py" -type f | xargs grep -h "@app\.\|@router\." > artifacts/endpoint-map.txt || true
	@echo "$(GREEN)Function map generated in artifacts/$(RESET)"

# ============================================================================
# CODE QUALITY
# ============================================================================

format:
	@echo "$(BLUE)Formatting code with Black...$(RESET)"
	black $(SRC_DIRS) $(TEST_DIRS)
	@echo "$(GREEN)Code formatted!$(RESET)"

lint:
	@echo "$(BLUE)Running Ruff linting...$(RESET)"
	ruff check $(SRC_DIRS) $(TEST_DIRS) || true
	@echo "$(GREEN)Linting complete!$(RESET)"

type-check:
	@echo "$(BLUE)Running MyPy type checking...$(RESET)"
	mypy $(SRC_DIRS) --ignore-missing-imports || true
	@echo "$(GREEN)Type checking complete!$(RESET)"

# ============================================================================
# TESTING
# ============================================================================

test:
	@echo "$(BLUE)Running tests...$(RESET)"
	$(PYTHON) -m pytest $(TEST_DIRS) -v

test-cov:
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	$(PYTHON) -m pytest $(TEST_DIRS) --cov=$(SRC_DIRS) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"

# ============================================================================
# SECURITY
# ============================================================================

security:
	@echo "$(BLUE)Running security scans...$(RESET)"
	@mkdir -p artifacts
	@echo "$(YELLOW)Running Bandit...$(RESET)"
	bandit -r $(SRC_DIRS) -f json -o artifacts/bandit-report.json || true
	bandit -r $(SRC_DIRS) || true
	@echo "$(YELLOW)Running Safety...$(RESET)"
	safety check || true
	@echo "$(YELLOW)Running pip-audit...$(RESET)"
	pip-audit || true
	@echo "$(GREEN)Security scans complete!$(RESET)"

# ============================================================================
# DOCKER
# ============================================================================

dc-up:
	@echo "$(BLUE)Starting Docker services...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(RESET)"

dc-down:
	@echo "$(BLUE)Stopping Docker services...$(RESET)"
	docker-compose down
	@echo "$(GREEN)Services stopped!$(RESET)"

# ============================================================================
# DEVELOPMENT
# ============================================================================

run:
	@echo "$(BLUE)Starting API server...$(RESET)"
	$(PYTHON) -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

run-agents:
	@echo "$(BLUE)Starting all agents...$(RESET)"
	$(PYTHON) src/cli/__main__.py start-all

health-check:
	@echo "$(BLUE)Running health check...$(RESET)"
	$(PYTHON) scripts/run_health_check.py

# ============================================================================
# CLEANUP
# ============================================================================

clean:
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist htmlcov .coverage artifacts
	@echo "$(GREEN)Cleanup complete!$(RESET)"
