# Quick Test Reference Guide

## Quick Start

```bash
# Run all smoke tests (fastest - use for quick validation)
pytest tests/smoke/ -v

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html
```

## Run Tests by Category

```bash
# Smoke tests (5 seconds, fast validation)
pytest tests/smoke/ -v

# Unit tests (component isolation)
pytest tests/unit/ -v

# Integration tests (multi-component)
pytest tests/integration/ -v

# API tests (HTTP endpoints)
pytest tests/api/ -v

# Security tests
pytest tests/security/ -v

# ML tests
pytest tests/ml/ -v

# E2E tests
pytest tests/e2e/ -v

# Performance tests
pytest tests/performance/ -v
```

## Run Tests by Marker

```bash
pytest -m smoke          # Fast smoke tests
pytest -m unit           # Unit tests
pytest -m integration    # Integration tests
pytest -m api            # API tests
pytest -m security       # Security tests
pytest -m ml             # ML tests
pytest -m e2e            # End-to-end tests
pytest -m performance    # Performance tests
pytest -m "not slow"     # Skip slow tests
```

## Common Test Scenarios

### Before Commit
```bash
# Quick validation
pytest tests/smoke/ -x

# If smoke tests pass, run unit tests
pytest tests/unit/ -v
```

### CI/CD Pipeline
```bash
# Stage 1: Smoke (fail fast)
pytest tests/smoke/ -x -v

# Stage 2: Unit + Integration
pytest tests/unit/ tests/integration/ -v --cov

# Stage 3: API + Security
pytest tests/api/ tests/security/ -v

# Stage 4: ML + E2E (optional, can be nightly)
pytest tests/ml/ tests/e2e/ -v
```

### Debug Failing Test
```bash
# Run with verbose output and stop on first failure
pytest tests/api/test_agents_endpoints.py -vv --tb=long -x

# Run with debugger
pytest tests/api/test_agents_endpoints.py --pdb

# Run specific test function
pytest tests/api/test_agents_endpoints.py::test_specific_function -v
```

### Coverage Analysis
```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Markers Available

- `smoke` - Fast smoke tests for CI/CD
- `unit` - Unit tests for individual components
- `integration` - Integration tests for multiple components
- `api` - API endpoint tests
- `security` - Security-related tests
- `ml` - Machine learning model tests
- `e2e` - End-to-end tests
- `slow` - Tests that take >1s to run
- `performance` - Performance and load tests
- `benchmark` - Performance benchmark tests
- `database` - Tests requiring database
- `redis` - Tests requiring Redis
- `external` - Tests that call external APIs

## Environment Setup for Tests

```bash
# Set test environment variables (optional, conftest.py sets defaults)
export ENVIRONMENT=test
export DATABASE_URL=sqlite:///:memory:
export JWT_SECRET_KEY=test_secret
export ENCRYPTION_MASTER_KEY=test_encryption_key_32_bytes_!!

# Run tests
pytest tests/ -v
```

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/DevSkyy

# Ensure dependencies are installed
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run tests
pytest tests/ -v
```

### Database Errors
```bash
# Tests use in-memory SQLite by default
# If you need PostgreSQL for specific tests:
export DATABASE_URL=postgresql://user:pass@localhost/test_db
pytest tests/infrastructure/ -v
```

### Slow Tests
```bash
# Skip slow tests
pytest tests/ -m "not slow" -v

# See test execution times
pytest tests/ --durations=10
```

## Performance

- **Smoke tests**: ~5 seconds (48 tests)
- **Unit tests**: ~10-30 seconds
- **Integration tests**: ~30-60 seconds
- **All tests**: ~2-5 minutes (depending on system)

## File Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_*()`
- Test classes: `Test*`

All tests must follow these conventions for pytest to discover them.

## Adding New Tests

1. Choose the right directory based on test type
2. Create file: `test_<feature_name>.py`
3. Add appropriate markers: `@pytest.mark.unit`, etc.
4. Use shared fixtures from `conftest.py`
5. Run tests: `pytest tests/<category>/test_<feature_name>.py -v`

## CI/CD Integration Example

```yaml
# .github/workflows/test.yml
- name: Smoke Tests
  run: pytest tests/smoke/ -v -x

- name: Unit Tests
  run: pytest tests/unit/ -v --cov

- name: Integration Tests
  run: pytest tests/integration/ tests/api/ -v

- name: Security Tests
  run: pytest tests/security/ -v
```

---

**For more details, see:**
- `tests/README.md` - Comprehensive test documentation
- `tests/TEST_STRUCTURE.md` - Visual structure and organization
- `pytest.ini` - Pytest configuration
