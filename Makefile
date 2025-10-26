# DevSkyy - Luxury Fashion AI Platform
# Enhanced Makefile with SkyyRoseLLC/transformers standards
.PHONY: help install dev-install clean test lint format docker-build docker-run setup quality style security

# Configuration (transformers-inspired)
PYTHON := python3
SRC_DIRS := agent api security infrastructure ml ai_orchestration database monitoring architecture
TEST_DIRS := tests

# Colors for better output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Default target with enhanced help
help:
	@echo "$(BLUE)DevSkyy Platform - Enhanced Make Commands$(RESET)"
	@echo "$(BLUE)===========================================$(RESET)"
	@echo "$(GREEN)Installation:$(RESET)"
	@echo "  install          - Install production dependencies"
	@echo "  dev-install      - Install development dependencies"
	@echo "  setup            - Complete setup (deps + frontend)"
	@echo ""
	@echo "$(GREEN)Code Quality:$(RESET)"
	@echo "  format           - Format code with Ruff (primary) and Black"
	@echo "  lint             - Run Ruff linting"
	@echo "  lint-fix         - Run linting with automatic fixes"
	@echo "  type-check       - Run MyPy type checking"
	@echo "  quality          - Run all quality checks"
	@echo "  style            - Format and fix linting issues"
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@echo "  test             - Run all tests"
	@echo "  test-unit        - Run unit tests only"
	@echo "  test-api         - Run API tests only"
	@echo "  test-security    - Run security tests only"
	@echo "  test-coverage    - Run tests with coverage report"
	@echo "  test-fast        - Run tests excluding slow tests"
	@echo ""
	@echo "$(GREEN)Security:$(RESET)"
	@echo "  security         - Run security checks (bandit, safety)"
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@echo "  run              - Run development server"
	@echo "  run-prod         - Run production server"
	@echo "  clean            - Remove build artifacts and caches"
	@echo ""
	@echo "$(GREEN)Docker:$(RESET)"
	@echo "  docker-build     - Build Docker image"
	@echo "  docker-run       - Run Docker container"
	@echo ""
	@echo "$(GREEN)Workflows:$(RESET)"
	@echo "  check            - Run all checks (quality + tests + security)"
	@echo "  pre-commit       - Quick pre-commit checks"

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing DevSkyy in production mode...$(RESET)"
	pip install --upgrade pip
	pip install -e .

dev-install: install ## Install development dependencies
	@echo "$(BLUE)Installing DevSkyy in development mode...$(RESET)"
	pip install -e ".[dev,test,docs,monitoring]"
	@echo "$(GREEN)Development installation complete!$(RESET)"

# ============================================================================
# CODE QUALITY & FORMATTING (Transformers-inspired)
# ============================================================================

format: ## Format code using Ruff (primary) and Black (backup)
	@echo "$(BLUE)Formatting code with Ruff...$(RESET)"
	ruff format $(SRC_DIRS) $(TEST_DIRS)
	@echo "$(GREEN)Code formatting complete!$(RESET)"

lint: ## Run linting with Ruff
	@echo "$(BLUE)Running Ruff linting...$(RESET)"
	ruff check $(SRC_DIRS) $(TEST_DIRS)

lint-fix: ## Run linting with automatic fixes
	@echo "$(BLUE)Running Ruff linting with fixes...$(RESET)"
	ruff check --fix $(SRC_DIRS) $(TEST_DIRS)

type-check: ## Run type checking with MyPy
	@echo "$(BLUE)Running MyPy type checking...$(RESET)"
	mypy $(SRC_DIRS)

quality: lint type-check ## Run all quality checks
	@echo "$(GREEN)All quality checks passed!$(RESET)"

style: format lint-fix ## Format code and fix linting issues
	@echo "$(GREEN)Code styling complete!$(RESET)"

# ============================================================================
# CLEANUP
# ============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist htmlcov .coverage
	@echo "$(GREEN)Cleanup complete!$(RESET)"

# ============================================================================
# TESTING (Enhanced with markers)
# ============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(RESET)"
	pytest $(TEST_DIRS) -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(RESET)"
	pytest $(TEST_DIRS) -v -m "unit"

test-api: ## Run API tests only
	@echo "$(BLUE)Running API tests...$(RESET)"
	pytest $(TEST_DIRS) -v -m "api"

test-security: ## Run security tests only
	@echo "$(BLUE)Running security tests...$(RESET)"
	pytest $(TEST_DIRS) -v -m "security"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(RESET)"
	pytest $(TEST_DIRS) -v -m "integration"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	pytest $(TEST_DIRS) --cov=. --cov-report=html --cov-report=term-missing

test-fast: ## Run tests excluding slow tests
	@echo "$(BLUE)Running fast tests...$(RESET)"
	pytest $(TEST_DIRS) -v -m "not slow"

# Code quality
lint:
	@echo "Running flake8..."
	flake8 . || true
	@echo "Checking code formatting..."
	black --check . || true
	@echo "Checking import order..."
	isort --check-only . || true

format:
	@echo "Formatting code with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

type-check:
	mypy . --ignore-missing-imports

# Docker
docker-build:
	docker build -t devskyy-platform:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# Frontend
frontend-install:
	cd frontend && npm install

frontend-build:
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm run dev

frontend-lint:
	cd frontend && npm run lint

frontend-format:
	cd frontend && npm run format

# Complete setup
setup: install frontend-install
	@echo "Setup complete!"
	@echo "Run 'make run' to start the development server"

# Run servers
run:
	python3 main.py

run-prod:
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Database
db-migrate:
	@echo "Running database migrations..."
	# Add migration commands here

db-seed:
	@echo "Seeding database..."
	# Add seed commands here

# ============================================================================
# SECURITY (Enhanced)
# ============================================================================

security: ## Run comprehensive security checks
	@echo "$(BLUE)Running security checks...$(RESET)"
	bandit -r $(SRC_DIRS) -f json -o security-report.json || true
	bandit -r $(SRC_DIRS)
	safety check
	pip-audit
	@echo "$(GREEN)Security checks complete!$(RESET)"

security-check: security ## Alias for security command

# ============================================================================
# COMPREHENSIVE WORKFLOWS
# ============================================================================

check: quality test security ## Run all checks (quality, tests, security)
	@echo "$(GREEN)All checks passed! Ready for deployment.$(RESET)"

pre-commit: format lint-fix test-fast ## Enhanced pre-commit checks
	@echo "$(GREEN)Pre-commit checks complete!$(RESET)"

prod-check: check ## Production readiness check
	@echo "$(BLUE)Running production readiness check...$(RESET)"
	python3 production_safety_check.py || true
	@echo "$(GREEN)Production check complete!$(RESET)"

# ============================================================================
# INFORMATION & UTILITIES
# ============================================================================

info: ## Show project information
	@echo "$(BLUE)DevSkyy Project Information$(RESET)"
	@echo "$(BLUE)============================$(RESET)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Tests: $$(find $(TEST_DIRS) -name 'test_*.py' | wc -l) test files"
	@echo "Source files: $$(find $(SRC_DIRS) -name '*.py' | wc -l) Python files"

health-check: ## Check application health
	@echo "$(BLUE)Checking application health...$(RESET)"
	curl -f http://localhost:8000/health || echo "$(RED)Application not responding$(RESET)"