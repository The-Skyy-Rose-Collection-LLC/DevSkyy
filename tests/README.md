# DevSkyy Test Suite

This directory contains the comprehensive test suite for DevSkyy, organized by test type and purpose.

## Directory Structure

```
tests/
├── smoke/                      # Fast smoke tests for CI/CD quick validation
│   ├── test_imports.py        # Import verification tests
│   ├── test_file_structure.py # File structure validation
│   └── test_health_checks.py  # Basic health checks
├── unit/                       # Unit tests for individual components
│   ├── agents/                # Agent-specific unit tests
│   ├── api/                   # API utility unit tests
│   ├── infrastructure/        # Infrastructure component tests
│   ├── ml/                    # ML model unit tests
│   └── security/              # Security module unit tests
├── integration/                # Integration tests for multiple components
│   └── test_api_endpoints.py # API integration tests
├── api/                        # API endpoint tests
│   ├── test_agents_endpoints.py
│   ├── test_dashboard_endpoints.py
│   ├── test_gdpr.py
│   ├── test_main_endpoints.py
│   ├── test_mcp_endpoints.py
│   └── test_rag.py
├── security/                   # Security-focused tests
│   ├── test_encryption.py
│   ├── test_input_validation.py
│   ├── test_jwt_auth.py
│   ├── test_security_fixes.py
│   └── test_security_integration.py
├── ml/                         # Machine learning tests
│   ├── test_ml_infrastructure.py
│   └── test_model_validation.py
├── e2e/                        # End-to-end tests
├── performance/                # Performance and benchmark tests
│   └── test_api_performance.py
├── agents/                     # Agent system tests
│   └── test_orchestrator.py
├── api_integration/            # API integration workflow tests
│   ├── test_enums.py
│   └── test_workflow_integration.py
├── fashion_ai_bounded_autonomy/ # Fashion AI bounded autonomy tests
│   ├── test_approval_system.py
│   ├── test_bounded_autonomy_wrapper.py
│   ├── test_bounded_orchestrator.py
│   ├── test_data_pipeline.py
│   ├── test_performance_tracker.py
│   ├── test_report_generator.py
│   └── test_watchdog.py
├── infrastructure/             # Infrastructure tests
│   ├── test_database.py
│   └── test_redis.py
├── conftest.py                 # Shared pytest fixtures and configuration
└── README.md                   # This file
```

## Test Categories

### Smoke Tests (`smoke/`)
Fast-running tests designed to catch critical failures early. These run first in CI/CD pipelines.

**Purpose:** Quick validation that the system can start and basic functionality works.

**Run with:** `pytest tests/smoke/ -v`

**Tests include:**
- Import verification (all modules can be imported)
- File structure validation (required files and directories exist)
- Basic health checks (app can start, endpoints exist)

### Unit Tests (`unit/`)
Tests for individual components in isolation, using mocks for dependencies.

**Purpose:** Validate individual functions and classes work correctly.

**Run with:** `pytest tests/unit/ -v`

**Coverage:** Should cover >90% of individual modules.

### Integration Tests (`integration/`)
Tests that verify multiple components work together correctly.

**Purpose:** Validate component interactions and data flow.

**Run with:** `pytest tests/integration/ -v`

**Tests include:**
- API endpoint integration
- Database and cache integration
- Multi-agent workflows

### API Tests (`api/`)
Tests for FastAPI HTTP endpoints and REST API functionality.

**Purpose:** Validate API contracts, request/response handling, and HTTP behavior.

**Run with:** `pytest tests/api/ -v`

**Tests include:**
- Endpoint availability
- Request validation
- Response formats
- Error handling

### Security Tests (`security/`)
Tests for authentication, authorization, encryption, and security features.

**Purpose:** Ensure security mechanisms work correctly and detect vulnerabilities.

**Run with:** `pytest tests/security/ -v`

**Tests include:**
- JWT authentication
- Encryption/decryption
- Input validation and sanitization
- Security fixes verification

### Machine Learning Tests (`ml/`)
Tests for ML models, training, prediction, and model infrastructure.

**Purpose:** Validate ML models perform correctly and meet accuracy requirements.

**Run with:** `pytest tests/ml/ -v`

**Tests include:**
- Model training and inference
- Data pipeline validation
- Model performance metrics

### End-to-End Tests (`e2e/`)
Complete user workflow tests that span the entire system.

**Purpose:** Validate real-world user scenarios work end-to-end.

**Run with:** `pytest tests/e2e/ -v`

**Note:** May be slower and require more setup.

### Performance Tests (`performance/`)
Benchmark and performance tests to measure response times and throughput.

**Purpose:** Ensure system meets performance requirements.

**Run with:** `pytest tests/performance/ -v --benchmark-only`

**Tests include:**
- API response time benchmarks
- Concurrent request handling
- Resource usage monitoring

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Category
```bash
pytest tests/smoke/        # Smoke tests only
pytest tests/unit/         # Unit tests only
pytest tests/integration/  # Integration tests only
pytest tests/api/          # API tests only
pytest tests/security/     # Security tests only
pytest tests/ml/           # ML tests only
pytest tests/e2e/          # E2E tests only
pytest tests/performance/  # Performance tests only
```

### Run by Marker
```bash
pytest -m smoke           # Smoke tests
pytest -m unit            # Unit tests
pytest -m integration     # Integration tests
pytest -m api             # API tests
pytest -m security        # Security tests
pytest -m ml              # ML tests
pytest -m e2e             # E2E tests
pytest -m performance     # Performance tests
pytest -m slow            # Tests that take >1s
pytest -m "not slow"      # Skip slow tests
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

### Fast Fail (Smoke Tests Only)
```bash
pytest tests/smoke/ -x  # Stop on first failure
```

## Test Naming Conventions

All test files must follow these conventions:
- **File names:** `test_*.py` (e.g., `test_authentication.py`)
- **Test functions:** `test_*` (e.g., `def test_user_login():`)
- **Test classes:** `Test*` (e.g., `class TestUserAuth:`)

## Pytest Markers

Tests can be marked with the following markers (defined in `pytest.ini`):

- `@pytest.mark.smoke` - Fast smoke tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.ml` - ML tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow tests (>1s)
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.benchmark` - Benchmark tests
- `@pytest.mark.database` - Tests requiring database
- `@pytest.mark.redis` - Tests requiring Redis
- `@pytest.mark.external` - Tests calling external APIs

## Shared Fixtures

Common test fixtures are defined in `conftest.py`:

- `test_client` - FastAPI test client
- `async_test_client` - Async FastAPI test client
- `test_db_engine` - In-memory SQLite database
- `test_db_session` - Database session
- `test_user_data` - Sample user data
- `test_access_token` - JWT access token
- `test_refresh_token` - JWT refresh token
- `auth_headers` - Authorization headers
- `mock_ai_response` - Mock AI API response
- `performance_timer` - Timer for performance tests
- `setup_test_environment` - Test environment variables (autouse)

## CI/CD Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
- name: Run smoke tests
  run: pytest tests/smoke/ -v
  
- name: Run unit tests
  run: pytest tests/unit/ -v --cov
  
- name: Run integration tests
  run: pytest tests/integration/ -v
  
- name: Run security tests
  run: pytest tests/security/ -v
```

## Adding New Tests

When adding new tests:

1. **Choose the right directory** based on test type
2. **Follow naming conventions** (`test_*.py`)
3. **Add appropriate markers** (`@pytest.mark.unit`, etc.)
4. **Use shared fixtures** from `conftest.py`
5. **Add docstrings** explaining what the test validates
6. **Keep tests focused** - one concept per test
7. **Make tests independent** - no dependencies between tests

## Test Development Best Practices

1. **Test one thing per test** - Each test should validate one behavior
2. **Use descriptive names** - Test names should explain what they test
3. **Arrange-Act-Assert** - Structure tests with clear setup, execution, verification
4. **Mock external dependencies** - Don't call real external APIs in tests
5. **Clean up after tests** - Use fixtures and teardown for cleanup
6. **Avoid test interdependencies** - Tests should run in any order
7. **Keep tests fast** - Unit tests should run in milliseconds
8. **Use parameterized tests** - Test multiple cases with `@pytest.mark.parametrize`

## Troubleshooting

### Import Errors
If you get import errors, ensure:
- You're running tests from the project root
- Virtual environment is activated
- Dependencies are installed: `pip install -r requirements-test.txt`

### Database Errors
Database tests use in-memory SQLite by default. If you need PostgreSQL:
```bash
export DATABASE_URL="postgresql://test:test@localhost/test_db"
pytest tests/integration/
```

### Slow Tests
To skip slow tests:
```bash
pytest -m "not slow"
```

### Debug Mode
Run with verbose output and debugging:
```bash
pytest tests/ -vv --tb=long --pdb
```

## Coverage Goals

- **Overall:** >90% code coverage
- **Unit tests:** >95% coverage of individual modules
- **Integration tests:** Cover critical user workflows
- **API tests:** 100% endpoint coverage
- **Security tests:** 100% security feature coverage

## Questions?

For questions about tests or to report test failures:
- Check GitHub Issues
- Review test documentation in source files
- Contact DevSkyy team

---

**Last Updated:** 2025-11-12
**Maintained by:** DevSkyy Team
