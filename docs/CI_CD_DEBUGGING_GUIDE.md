

# CI/CD Debugging Guide for DevSkyy
**Comprehensive Troubleshooting Reference**

---

## 📋 Quick Reference

| Problem | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Import errors | Python path | Check conftest.py sys.path |
| Database errors | Missing DB | Check PostgreSQL service |
| Test failures | Environment vars | Check .env setup |
| Slow tests | No mocking | Use fixtures |
| Coverage < 90% | Missing tests | Write more tests |
| Security scan fails | Vulnerabilities | Update dependencies |

---

## 🔍 Common Failure Patterns

### Pattern 1: ModuleNotFoundError

**Symptom:**
```python
ModuleNotFoundError: No module named 'agent'
```

**Why it happens:**
- Tests run from repository root
- Python doesn't know where to find your modules
- Import paths assume package is installed

**How to fix:**
```python
# tests/conftest.py (ALREADY FIXED!)
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now imports work:
from agent.orchestrator import AgentOrchestrator  # ✅
```

**Verification:**
```bash
# Test locally:
cd /path/to/DevSkyy
python -c "import sys; sys.path.insert(0, '.'); from agent.orchestrator import AgentOrchestrator; print('✅ Import works!')"
```

---

### Pattern 2: Database Connection Refused

**Symptom:**
```
asyncpg.exceptions.ConnectionRefusedError: Connection refused
```

**Why it happens:**
- PostgreSQL service not started in CI/CD
- Wrong connection string
- Database doesn't exist

**How to fix:**

**Check 1: Verify service configuration**
```yaml
# .github/workflows/test.yml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_USER: devskyy_test
      POSTGRES_PASSWORD: test_password
      POSTGRES_DB: devskyy_test  # ← Must match DATABASE_URL
    ports:
      - 5432:5432
```

**Check 2: Wait for service**
```yaml
- name: Wait for PostgreSQL
  run: |
    until pg_isready -h localhost -p 5432; do
      echo "Waiting for PostgreSQL..."
      sleep 2
    done
```

**Check 3: Test connection**
```yaml
- name: Test database connection
  run: |
    psql -h localhost -U devskyy_test -d devskyy_test -c "SELECT 1"
  env:
    PGPASSWORD: test_password
```

**Local testing:**
```bash
# Start PostgreSQL locally
docker run --name test-postgres \
  -e POSTGRES_USER=devskyy_test \
  -e POSTGRES_PASSWORD=test_password \
  -e POSTGRES_DB=devskyy_test \
  -p 5432:5432 \
  -d postgres:15-alpine

# Test connection
psql -h localhost -U devskyy_test -d devskyy_test -c "SELECT 1"
```

---

### Pattern 3: Environment Variable Missing

**Symptom:**
```python
KeyError: 'SECRET_KEY'
ValueError: SECRET_KEY environment variable not set
```

**Why it happens:**
- Application code requires env vars
- CI/CD doesn't have .env file
- Tests don't set defaults

**How to fix (ALREADY FIXED!):**
```python
# tests/conftest.py
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    os.environ.setdefault("DATABASE_URL", "postgresql://...")
    # ... etc
```

**Verification:**
```bash
# Run tests and check env vars
python -c "
import pytest
import sys
sys.path.insert(0, '.')
from tests.conftest import setup_test_environment
list(setup_test_environment())  # Triggers setup
import os
print('SECRET_KEY:', os.environ.get('SECRET_KEY', 'NOT SET'))
"
```

---

### Pattern 4: Test Coverage Below 90%

**Symptom:**
```
FAILED: Coverage was 73.2% but should be >= 90%
```

**Why it happens:**
- Not enough tests written
- Tests don't exercise all code paths
- Some files excluded from coverage

**How to find what's not covered:**
```bash
# Generate coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html  # View in browser

# Show missing lines in terminal
pytest --cov=. --cov-report=term-missing

# Example output:
# agent/orchestrator.py    75%   45-52, 78-82
#                               ↑ These lines not covered
```

**How to fix:**
1. **Find uncovered code:**
   ```bash
   pytest --cov=. --cov-report=term-missing | grep -A 5 "TOTAL"
   ```

2. **Write tests for uncovered lines:**
   ```python
   # If lines 45-52 are uncovered error handling:
   def test_orchestrator_handles_errors():
       with pytest.raises(ValueError):
           orchestrator.execute_task(invalid_task)  # ← Covers error path
   ```

3. **Focus on critical modules first:**
   - Security modules (auth, encryption)
   - Business logic (ecommerce, agents)
   - API endpoints

---

### Pattern 5: Security Scan Finds Vulnerabilities

**Symptom:**
```
Found 6 CRITICAL, 28 HIGH severity vulnerabilities
```

**Why it happens:**
- Dependencies have known CVEs
- Outdated packages
- Transitive dependencies (dependencies of dependencies)

**How to identify:**
```bash
# Run security scans locally
pip install pip-audit safety bandit

# Check for vulnerable dependencies
pip-audit

# Check against Safety database
safety check

# Check code for security issues
bandit -r . -f json
```

**How to fix:**

**Step 1: Identify vulnerable packages**
```bash
pip-audit --format json > vulnerabilities.json

# View critical ones
jq '.vulnerabilities[] | select(.severity == "CRITICAL" or .severity == "HIGH")' vulnerabilities.json
```

**Step 2: Update packages**
```bash
# Update specific package
pip install --upgrade cryptography

# Update all (risky - test first!)
pip install --upgrade -r requirements.txt
```

**Step 3: Handle packages without fixes**
```python
# If no fix available, add to known issues
# .github/workflows/security-scan.yml
- name: Check vulnerabilities
  run: |
    pip-audit --ignore-vuln CVE-2023-XXXXX  # Document why
```

---

### Pattern 6: Slow Tests (Timeout)

**Symptom:**
```
FAILED: Test exceeded 10 minute timeout
```

**Why it happens:**
- Tests hitting real APIs
- No mocking of external services
- Database queries not optimized
- Too many tests running serially

**How to fix:**

**Use mocks for external APIs:**
```python
# Before (SLOW - hits real API):
def test_ai_agent():
    response = anthropic_client.messages.create(...)  # Real API call!
    assert response.content

# After (FAST - uses mock):
def test_ai_agent(monkeypatch):
    mock_response = {"content": "test response"}
    monkeypatch.setattr("anthropic.Client.messages.create",
                       lambda *args, **kwargs: mock_response)
    response = anthropic_client.messages.create(...)  # Mocked!
    assert response.content
```

**Use fixtures for database:**
```python
# Before (SLOW - creates DB every test):
def test_user_query():
    db = await asyncpg.connect(...)  # Real connection!
    result = await db.fetchrow(...)

# After (FAST - uses fixture):
def test_user_query(mock_database):
    mock_database.fetchrow.return_value = {"id": 1}
    result = await db.fetchrow(...)  # Mocked!
```

**Run tests in parallel:**
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4

# Or in CI/CD:
pytest -n auto  # Automatically use all CPUs
```

---

### Pattern 7: Docker Build Fails

**Symptom:**
```
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

**Why it happens:**
- Dependency conflicts
- Missing system libraries
- Wrong Python version
- Build context too large

**How to debug:**

**Step 1: Build locally**
```bash
# Build and see full output
docker build -t devskyy:debug .

# Build without cache (fresh install)
docker build --no-cache -t devskyy:debug .
```

**Step 2: Debug interactively**
```bash
# Build up to failing step
docker build -t devskyy:debug --target builder .

# Run interactive shell
docker run -it devskyy:debug /bin/bash

# Test commands manually
pip install -r requirements.txt
```

**Step 3: Check system dependencies**
```dockerfile
# Add missing system libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
```

---

### Pattern 8: Performance Test Fails (P95 > 200ms)

**Symptom:**
```
AssertionError: P95 latency 345.2ms exceeds threshold 200ms
```

**Why it happens:**
- Inefficient code
- N+1 query problem
- No caching
- Synchronous I/O

**How to identify:**

**Profile the code:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run slow operation
result = await slow_operation()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 slow functions
```

**Find N+1 queries:**
```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Run operation and watch logs
result = await get_users_with_posts()

# If you see:
# SELECT * FROM users;        # 1 query
# SELECT * FROM posts WHERE user_id=1;  # N queries
# SELECT * FROM posts WHERE user_id=2;
# ...
# ← This is N+1 problem!
```

**How to fix:**

**Add caching:**
```python
# Before (SLOW - queries DB every time):
async def get_user(user_id):
    return await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

# After (FAST - caches result):
from functools import lru_cache

@lru_cache(maxsize=1000)
async def get_user(user_id):
    return await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
```

**Fix N+1 with eager loading:**
```python
# Before (N+1 - separate queries):
users = await session.execute(select(User))
for user in users:
    posts = await session.execute(select(Post).where(Post.user_id == user.id))

# After (1 query - eager load):
from sqlalchemy.orm import selectinload

users = await session.execute(
    select(User).options(selectinload(User.posts))
)
```

---

## 🛠️ Debugging Tools

### Tool 1: pytest verbose mode

```bash
# Show which test failed
pytest -v

# Show print statements
pytest -s

# Show very verbose output
pytest -vv

# Stop at first failure
pytest -x

# Show why test was skipped
pytest -rs
```

### Tool 2: pytest debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on error
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb

# Trace execution
pytest --trace
```

### Tool 3: Coverage analysis

```bash
# Show coverage of specific module
pytest --cov=agent --cov-report=term

# Show missing lines
pytest --cov=agent --cov-report=term-missing

# Generate HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Export to XML (for CI/CD)
pytest --cov=. --cov-report=xml
```

### Tool 4: Log analysis

```bash
# Show logs during test
pytest --log-cli-level=DEBUG

# Capture and show logs
pytest --log-file=test.log --log-file-level=DEBUG

# Show specific logger
pytest --log-cli-level=DEBUG --log-cli-logger=agent.orchestrator
```

---

## 📊 CI/CD Workflow Debugging

### Step 1: View workflow logs

1. Go to **Actions** tab in GitHub
2. Click on failed workflow run
3. Click on failed job
4. Expand failed step
5. Review error message and logs

### Step 2: Download artifacts

```bash
# Using GitHub CLI
gh run list
gh run view <run-id>
gh run download <run-id>

# Manually
# 1. Go to workflow run
# 2. Scroll to "Artifacts" section
# 3. Download relevant artifact
# 4. Unzip and inspect
```

### Step 3: Reproduce locally

```bash
# Simulate CI/CD environment locally
docker run -it --rm \
  -v $(pwd):/app \
  -w /app \
  python:3.11.9 \
  bash -c "
    pip install -r requirements.txt
    pip install -r requirements-test.txt
    pytest --cov=. --cov-fail-under=90
  "
```

### Step 4: Check environment

```yaml
# Add debug step to workflow
- name: Debug environment
  run: |
    echo "Python version: $(python --version)"
    echo "Pip version: $(pip --version)"
    echo "Working directory: $(pwd)"
    echo "Files: $(ls -la)"
    echo "Environment variables:"
    env | grep -v SECRET | grep -v PASSWORD
```

---

## 🔐 Security Debugging

### Finding secrets in code

```bash
# Use detect-secrets
pip install detect-secrets
detect-secrets scan > .secrets.baseline

# Use TruffleHog
docker run --rm -it -v "$PWD:/pwd" trufflesecurity/trufflehog:latest \
  filesystem /pwd --only-verified
```

### Checking for hardcoded credentials

```bash
# Search for common patterns
grep -r "api_key\|password\|secret" . \
  --exclude-dir={.git,node_modules,venv} \
  | grep -v "***"  # Exclude redacted

# Check for base64 encoded secrets
grep -r "['\"][A-Za-z0-9+/]{40,}['\"]" . \
  --exclude-dir={.git,node_modules,venv}
```

---

## 📈 Performance Debugging

### Measuring P95 latency

```python
import time
import statistics

latencies = []
for i in range(100):
    start = time.time()
    await operation()
    elapsed = (time.time() - start) * 1000
    latencies.append(elapsed)

sorted_latencies = sorted(latencies)
p95_index = int(len(sorted_latencies) * 0.95)
p95_latency = sorted_latencies[p95_index]

print(f"P95 latency: {p95_latency:.2f}ms")
print(f"Mean: {statistics.mean(latencies):.2f}ms")
print(f"Median: {statistics.median(latencies):.2f}ms")
```

### Finding memory leaks

```python
import tracemalloc

# Start tracking
tracemalloc.start()

# Run operation
await leaky_operation()

# Get snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

# Show top 10 memory consumers
for stat in top_stats[:10]:
    print(stat)
```

---

## 🆘 Getting Help

### Checklist before asking for help:

- [ ] Read error message carefully
- [ ] Check this guide for similar issue
- [ ] Tried reproducing locally
- [ ] Checked recent changes (git diff)
- [ ] Reviewed workflow logs
- [ ] Searched existing GitHub issues

### Creating a good bug report:

```markdown
## Description
[Clear description of the problem]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [etc.]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- Branch: `develop`
- Commit: `abc123`
- Workflow: `ci-cd.yml`
- Job: `test`

## Logs
\```
[Paste relevant logs here]
\```

## Screenshots
[If applicable]

## What I've tried
- [Thing 1]
- [Thing 2]
```

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Truth Protocol](../CLAUDE.md)
- [Strategic Implementation Roadmap](./STRATEGIC_IMPLEMENTATION_ROADMAP.md)
- [Workflows README](../.github/workflows/README.md)

---

**Last Updated:** 2025-11-10
**Maintained by:** PyAssist - Python Programming Expert
