# CI/CD Test Configuration Examples

## GitHub Actions Example

### Option 1: Fast Feedback (Recommended)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  smoke-tests:
    name: Smoke Tests (Fast Fail)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run smoke tests
        run: pytest tests/smoke/ -v -x
        # -x: exit on first failure for fast feedback
  
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: smoke-tests  # Only run if smoke tests pass
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run unit tests with coverage
        run: pytest tests/unit/ -v --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
  
  integration-tests:
    name: Integration & API Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run integration tests
        run: pytest tests/integration/ tests/api/ -v
  
  security-tests:
    name: Security Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run security tests
        run: pytest tests/security/ -v
```

### Option 2: All Tests in One Job

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run smoke tests (fail fast)
        run: pytest tests/smoke/ -v -x
      
      - name: Run all tests with coverage
        run: pytest tests/ -v --cov=. --cov-report=xml --cov-report=html
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
      
      - name: Upload coverage HTML
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: htmlcov/
```

## GitLab CI Example

```yaml
# .gitlab-ci.yml

stages:
  - smoke
  - test
  - coverage

variables:
  ENVIRONMENT: test

smoke_tests:
  stage: smoke
  image: python:3.11
  script:
    - pip install -r requirements.txt -r requirements-test.txt
    - pytest tests/smoke/ -v -x
  only:
    - merge_requests
    - main

unit_tests:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt -r requirements-test.txt
    - pytest tests/unit/ -v --cov=. --cov-report=xml
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  only:
    - merge_requests
    - main

integration_tests:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt -r requirements-test.txt
    - pytest tests/integration/ tests/api/ -v
  only:
    - merge_requests
    - main

security_tests:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt -r requirements-test.txt
    - pytest tests/security/ -v
  only:
    - merge_requests
    - main

full_coverage:
  stage: coverage
  image: python:3.11
  script:
    - pip install -r requirements.txt -r requirements-test.txt
    - pytest tests/ -v --cov=. --cov-report=html --cov-report=term
  artifacts:
    paths:
      - htmlcov/
    expire_in: 30 days
  only:
    - main
```

## CircleCI Example

```yaml
# .circleci/config.yml

version: 2.1

orbs:
  python: circleci/python@2.1.1

jobs:
  smoke-tests:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - python/install-packages:
          pkg-manager: pip
          pip-dependency-file: requirements.txt
      - python/install-packages:
          pkg-manager: pip
          pip-dependency-file: requirements-test.txt
      - run:
          name: Run smoke tests
          command: pytest tests/smoke/ -v -x
  
  unit-tests:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - python/install-packages:
          pkg-manager: pip
          pip-dependency-file: requirements.txt
      - python/install-packages:
          pkg-manager: pip
          pip-dependency-file: requirements-test.txt
      - run:
          name: Run unit tests
          command: pytest tests/unit/ -v --cov=. --cov-report=xml
      - store_artifacts:
          path: coverage.xml
  
  integration-tests:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - python/install-packages:
          pkg-manager: pip
          pip-dependency-file: requirements.txt
      - python/install-packages:
          pkg-manager: pip
          pip-dependency-file: requirements-test.txt
      - run:
          name: Run integration tests
          command: pytest tests/integration/ tests/api/ -v

workflows:
  test:
    jobs:
      - smoke-tests
      - unit-tests:
          requires:
            - smoke-tests
      - integration-tests:
          requires:
            - unit-tests
```

## Jenkins Pipeline Example

```groovy
// Jenkinsfile

pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install -r requirements-test.txt'
            }
        }
        
        stage('Smoke Tests') {
            steps {
                sh 'pytest tests/smoke/ -v -x --junitxml=smoke-results.xml'
            }
            post {
                always {
                    junit 'smoke-results.xml'
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh 'pytest tests/unit/ -v --cov=. --cov-report=xml --junitxml=unit-results.xml'
            }
            post {
                always {
                    junit 'unit-results.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh 'pytest tests/integration/ tests/api/ -v --junitxml=integration-results.xml'
            }
            post {
                always {
                    junit 'integration-results.xml'
                }
            }
        }
        
        stage('Security Tests') {
            steps {
                sh 'pytest tests/security/ -v --junitxml=security-results.xml'
            }
            post {
                always {
                    junit 'security-results.xml'
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
```

## Docker-based Testing

```yaml
# docker-compose.test.yml

version: '3.8'

services:
  test:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=test
      - DATABASE_URL=postgresql://test:test@db:5432/testdb
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
    command: |
      sh -c "
        pip install -r requirements-test.txt &&
        pytest tests/smoke/ -v -x &&
        pytest tests/ -v --cov=. --cov-report=html
      "
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: testdb
  
  redis:
    image: redis:7-alpine
```

## Local Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit

echo "Running smoke tests before commit..."
pytest tests/smoke/ -v -x

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed! Commit aborted."
    exit 1
fi

echo "✅ Smoke tests passed!"
exit 0
```

## Makefile Commands

```makefile
# Makefile

.PHONY: test test-smoke test-unit test-integration test-all coverage

test-smoke:
	pytest tests/smoke/ -v -x

test-unit:
	pytest tests/unit/ -v --cov

test-integration:
	pytest tests/integration/ tests/api/ -v

test-security:
	pytest tests/security/ -v

test-all:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=. --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

test-fast:
	pytest tests/smoke/ tests/unit/ -v -x

test-ci:
	pytest tests/smoke/ -v -x && \
	pytest tests/unit/ -v --cov=. --cov-report=xml && \
	pytest tests/integration/ tests/api/ -v && \
	pytest tests/security/ -v
```

## Usage

Choose the configuration that matches your CI/CD platform and adjust as needed.

**Key principles:**
1. Run smoke tests first (fail fast)
2. Run unit tests with coverage
3. Run integration/API tests
4. Run security tests
5. Generate and upload coverage reports

---

**For more information:**
- See `tests/README.md` for test documentation
- See `tests/QUICK_REFERENCE.md` for test commands
- See `pytest.ini` for pytest configuration
