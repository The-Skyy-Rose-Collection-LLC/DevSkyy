# DevSkyy Testing Documentation

Testing documentation and procedures for the DevSkyy Enterprise Platform.

## 📋 Testing Overview

The DevSkyy platform implements comprehensive testing across multiple levels to ensure reliability, performance, and security.

## 🧪 Testing Strategy

### Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Few, high-value
                    │   (Slow)        │
                ┌───┴─────────────────┴───┐
                │   Integration Tests     │  ← Some, key workflows
                │   (Medium)              │
            ┌───┴─────────────────────────┴───┐
            │      Unit Tests                 │  ← Many, fast feedback
            │      (Fast)                     │
            └─────────────────────────────────┘
```

### Test Categories

#### 1. Unit Tests

- **Purpose**: Test individual components in isolation
- **Location**: `tests/` directory
- **Framework**: pytest
- **Coverage**: >80% required
- **Speed**: <1 second per test

#### 2. Integration Tests

- **Purpose**: Test component interactions
- **Scope**: API endpoints, database operations, external services
- **Framework**: pytest with fixtures
- **Coverage**: Critical workflows
- **Speed**: <10 seconds per test

#### 3. End-to-End Tests

- **Purpose**: Test complete user workflows
- **Scope**: Full application stack
- **Framework**: pytest + Selenium/Playwright
- **Coverage**: Key user journeys
- **Speed**: <60 seconds per test

## 📁 Test Structure

### Current Test Files

- **[test_adk.py](../../tests/test_adk.py)** - Agent Development Kit tests
- **[test_agents.py](../../tests/test_agents.py)** - AI agent functionality tests
- **[test_gdpr.py](../../tests/test_gdpr.py)** - GDPR compliance tests
- **[test_security.py](../../tests/test_security.py)** - Security module tests
- **[conftest.py](../../tests/conftest.py)** - Shared test configuration

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_adk.py         # ADK component tests
│   ├── test_agents.py      # Agent tests
│   ├── test_security.py    # Security tests
│   └── test_gdpr.py        # GDPR tests
├── integration/             # Integration tests
│   ├── test_api.py         # API endpoint tests
│   ├── test_database.py    # Database integration tests
│   └── test_wordpress.py   # WordPress integration tests
└── e2e/                     # End-to-end tests
    ├── test_user_flows.py  # Complete user workflows
    └── test_admin_flows.py # Admin functionality tests
```

## 🚀 Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_agents.py

# Run specific test function
pytest tests/test_agents.py::test_agent_creation

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Advanced Test Commands

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only failed tests from last run
pytest --lf

# Run tests with specific markers
pytest -m "not slow"

# Generate HTML coverage report
pytest --cov --cov-report=html
```

## 🔧 Test Configuration

### pytest Configuration

**File**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short -ra"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "security: Security tests",
    "slow: Slow tests (>5s)",
]
```

### Test Fixtures

**File**: `tests/conftest.py`

- **Database fixtures** - Test database setup/teardown
- **Client fixtures** - Test client configuration
- **Mock fixtures** - External service mocking
- **Data fixtures** - Test data generation

## 📊 Test Coverage

### Coverage Requirements

- **Minimum**: 80% overall coverage
- **Target**: 90% for new code
- **Critical paths**: 95% coverage required
- **Exclusions**: Test files, migrations, legacy code

### Coverage Reports

```bash
# Terminal coverage report
pytest --cov --cov-report=term-missing

# HTML coverage report
pytest --cov --cov-report=html
open htmlcov/index.html

# XML coverage report (for CI)
pytest --cov --cov-report=xml
```

## 🔒 Security Testing

### Security Test Categories

1. **Authentication tests** - Login, logout, token validation
2. **Authorization tests** - Permission checking, role validation
3. **Input validation tests** - SQL injection, XSS prevention
4. **Encryption tests** - Data encryption/decryption
5. **GDPR compliance tests** - Privacy controls, data deletion

### Security Test Examples

```python
def test_sql_injection_prevention():
    """Test that SQL injection attempts are blocked"""
    malicious_input = "'; DROP TABLE users; --"
    response = client.post("/api/search", json={"query": malicious_input})
    assert response.status_code == 400

def test_xss_prevention():
    """Test that XSS attempts are sanitized"""
    xss_payload = "<script>alert('xss')</script>"
    response = client.post("/api/content", json={"content": xss_payload})
    assert "<script>" not in response.json()["content"]
```

## 🚀 Performance Testing

### Performance Test Types

1. **Load testing** - Normal expected load
2. **Stress testing** - Beyond normal capacity
3. **Spike testing** - Sudden load increases
4. **Volume testing** - Large amounts of data
5. **Endurance testing** - Extended periods

### Performance Metrics

- **Response time** - <200ms for API endpoints
- **Throughput** - >1000 requests/second
- **Concurrent users** - >100 simultaneous users
- **Memory usage** - <512MB per process
- **CPU usage** - <80% under normal load

## 🔄 Continuous Testing

### Pre-commit Testing

- **Fast unit tests** - Run on every commit
- **Linting and formatting** - Code quality checks
- **Security scanning** - Credential and vulnerability detection

### CI/CD Testing

- **Full test suite** - All tests on push/PR
- **Multiple environments** - Python 3.11 and 3.12
- **Coverage reporting** - Codecov integration
- **Performance regression** - Automated performance checks

### Scheduled Testing

- **Nightly tests** - Full regression testing
- **Weekly security scans** - Comprehensive security testing
- **Monthly performance tests** - Load and stress testing

## 🐛 Test Debugging

### Common Issues

1. **Flaky tests** - Tests that pass/fail inconsistently
2. **Slow tests** - Tests taking too long to run
3. **Environment issues** - Tests failing in CI but not locally
4. **Data dependencies** - Tests depending on specific data

### Debugging Commands

```bash
# Run single test with full output
pytest tests/test_agents.py::test_specific -v -s

# Run with debugger
pytest tests/test_agents.py::test_specific --pdb

# Run with profiling
pytest tests/test_agents.py --profile

# Show test execution order
pytest --collect-only
```

## 📈 Test Metrics

### Quality Metrics

- **Test coverage percentage** - Code covered by tests
- **Test pass rate** - Percentage of passing tests
- **Test execution time** - Time to run test suite
- **Flaky test rate** - Tests with inconsistent results

### Tracking Tools

- **Coverage.py** - Code coverage measurement
- **pytest-benchmark** - Performance benchmarking
- **pytest-xdist** - Parallel test execution
- **pytest-html** - HTML test reports

---

For specific test implementations and examples, see the test files in the `tests/` directory.
