.PHONY: help install dev-install clean test lint format docker-build docker-run setup

# Default target
help:
	@echo "DevSkyy Platform - Make Commands"
	@echo "================================="
	@echo "install          - Install production dependencies"
	@echo "dev-install      - Install development dependencies"
	@echo "clean            - Remove build artifacts and caches"
	@echo "test             - Run test suite"
	@echo "test-coverage    - Run tests with coverage report"
	@echo "lint             - Run code linters (flake8, black check)"
	@echo "format           - Format code with black and isort"
	@echo "type-check       - Run mypy type checking"
	@echo "docker-build     - Build Docker image"
	@echo "docker-run       - Run Docker container"
	@echo "frontend-install - Install frontend dependencies"
	@echo "frontend-build   - Build frontend for production"
	@echo "frontend-dev     - Run frontend dev server"
	@echo "setup            - Complete setup (deps + frontend)"
	@echo "run              - Run development server"
	@echo "run-prod         - Run production server"

# Python dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

dev-install: install
	pip install -e ".[dev]"

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist
	@echo "Clean complete!"

# Testing
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=. --cov-report=html --cov-report=term

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

# Security
security-check:
	@echo "Running security checks..."
	pip-audit || true
	bandit -r . -x ./frontend,./tests || true

# Production safety
prod-check:
	python3 production_safety_check.py

# All checks before commit
pre-commit: format lint type-check test
	@echo "All checks passed! Ready to commit."