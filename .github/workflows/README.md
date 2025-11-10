# DevSkyy GitHub Actions Workflows

Comprehensive CI/CD automation following the **Truth Protocol** for DevSkyy's enterprise-grade multi-agent platform.

## 📋 Table of Contents

- [Overview](#overview)
- [Workflows](#workflows)
- [Truth Protocol Compliance](#truth-protocol-compliance)
- [Quick Start](#quick-start)
- [Workflow Details](#workflow-details)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

DevSkyy's CI/CD pipeline ensures **zero-defect deployment** through automated testing, security scanning, and performance validation. All workflows align with the Truth Protocol requirements:

- ✅ **90%+ test coverage** requirement
- ✅ **No HIGH/CRITICAL CVEs** allowed
- ✅ **P95 latency < 200ms** validation
- ✅ **Error rate < 0.5%** enforcement
- ✅ **SBOM generation** for compliance
- ✅ **Error ledger** for every run

## 🚀 Workflows

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| [CI/CD Pipeline](#cicd-pipeline) | Complete build, test, deploy | Push, PR | Required |
| [Security Scan](#security-scanning) | Vulnerability scanning | Push, PR, Weekly | Required |
| [Test Suite](#comprehensive-testing) | All test execution | Push, PR | Required |
| [Performance](#performance-testing) | Load & stress testing | Push to main, Daily | Required |
| [CodeQL](#codeql-analysis) | Advanced security analysis | Push, PR, Weekly | Required |
| [Dependabot](#dependabot) | Automated dependency updates | Weekly | Automated |

## 📜 Truth Protocol Compliance

Every workflow enforces DevSkyy's Truth Protocol:

### Pipeline Flow
```
Ingress → Validation → Auth → RBAC → Logic → Encryption → Output → Observability
```

### Quality Gates
1. **Lint & Type Check** - Ruff, Black, isort, mypy
2. **Security Scan** - Bandit, Safety, pip-audit, Trivy
3. **Test Coverage ≥90%** - Pytest with coverage enforcement
4. **Performance SLOs** - P95 < 200ms, error rate < 0.5%
5. **Container Security** - Trivy, Grype scanning
6. **Secret Scanning** - TruffleHog, detect-secrets
7. **SBOM Generation** - CycloneDX, SPDX formats
8. **Error Ledger** - JSON audit trail

## 🏁 Quick Start

### Enable Workflows

1. **Push code** to any branch:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin your-branch
   ```

2. **Create Pull Request** to `main` or `develop`:
   - All workflows run automatically
   - Checks must pass before merge
   - Review security findings

3. **Monitor Progress**:
   - Visit **Actions** tab in GitHub
   - View real-time logs
   - Download artifacts

### Required Secrets

Configure these in **Settings → Secrets and variables → Actions**:

```bash
# API Keys (if needed)
ANTHROPIC_API_KEY        # For Claude API
OPENAI_API_KEY          # For OpenAI API
CODECOV_TOKEN           # For coverage uploads

# Deployment (if needed)
DOCKER_USERNAME         # For Docker Hub
DOCKER_PASSWORD         # For Docker Hub
AWS_ACCESS_KEY_ID       # For AWS deployment
AWS_SECRET_ACCESS_KEY   # For AWS deployment
```

## 📖 Workflow Details

### CI/CD Pipeline

**File:** `ci-cd.yml`

Complete continuous integration and deployment pipeline.

#### Jobs

1. **Lint** (10 min)
   - Ruff linter
   - Black formatter check
   - isort import check
   - Generates linting report

2. **Type Check** (15 min)
   - mypy static type analysis
   - Validates type hints
   - Checks for type errors

3. **Security** (15 min)
   - Bandit security scanner
   - Safety vulnerability check
   - pip-audit dependency audit
   - **Fails on HIGH/CRITICAL CVEs**

4. **Tests** (30 min)
   - Pytest with coverage
   - PostgreSQL + Redis services
   - **Requires ≥90% coverage**
   - Uploads to Codecov

5. **Docker** (20 min)
   - Multi-stage build
   - Trivy vulnerability scan
   - Container health test
   - Saves image artifact

6. **Error Ledger** (10 min)
   - Generates JSON audit trail
   - Tracks all job statuses
   - Truth Protocol compliance

7. **OpenAPI** (10 min)
   - Generates API specification
   - Validates schema
   - Uploads artifact

8. **Summary** (5 min)
   - Generates build report
   - Posts to PR comments
   - Validates all gates passed

#### Usage

```yaml
# Runs on every push and PR
on:
  push:
    branches: ['**']
  pull_request:
    branches: [main, develop]
```

#### Artifacts

- Lint reports (30 days)
- Test coverage reports (30 days)
- Docker image (7 days)
- Error ledger (365 days)
- OpenAPI spec (30 days)

---

### Security Scanning

**File:** `security-scan.yml`

Comprehensive security scanning with SBOM generation.

#### Jobs

1. **Dependency Scan** (15 min)
   - Safety vulnerability database
   - pip-audit package audit
   - Package integrity checks

2. **Code Security** (15 min)
   - Bandit static analysis
   - **Blocks HIGH/CRITICAL issues**
   - SARIF upload to GitHub Security

3. **Secret Scan** (10 min)
   - TruffleHog secret detection
   - detect-secrets baseline
   - Scans full git history

4. **Container Scan** (20 min)
   - Trivy container scanning
   - Grype vulnerability detection
   - SARIF results to Security tab

5. **SBOM Generation** (15 min)
   - CycloneDX format
   - SPDX format
   - Uploads to dependency graph

6. **License Scan** (10 min)
   - pip-licenses analysis
   - Checks for prohibited licenses
   - Compliance validation

7. **Summary** (10 min)
   - Consolidated security report
   - Truth Protocol compliance check
   - GitHub Security integration

#### Schedule

```yaml
# Weekly scans every Sunday at 2 AM UTC
schedule:
  - cron: '0 2 * * 0'
```

#### Artifacts

- Security reports (90 days)
- SBOM files (365 days)
- License reports (90 days)
- Vulnerability scans (90 days)

---

### Comprehensive Testing

**File:** `test.yml`

Multi-tiered test suite with coverage enforcement.

#### Jobs

1. **Unit Tests** (20 min)
   - Tests by module: agents, api, security, ml, infrastructure
   - Matrix strategy for parallel execution
   - Individual coverage reports

2. **Integration Tests** (30 min)
   - PostgreSQL + Redis services
   - Database migrations
   - Cross-module testing

3. **API Tests** (20 min)
   - Endpoint validation
   - Authentication testing
   - Request/response validation

4. **Security Tests** (15 min)
   - Auth mechanism tests
   - Encryption validation
   - RBAC verification

5. **ML Tests** (25 min)
   - Model inference tests
   - Redis caching validation
   - AI/ML pipeline tests

6. **E2E Tests** (30 min)
   - Full application workflow
   - Real server testing
   - End-user scenarios

7. **Coverage Report** (15 min)
   - Combines all coverage
   - **Enforces ≥90% threshold**
   - Uploads to Codecov

8. **Summary** (10 min)
   - Test results dashboard
   - Coverage badge
   - Truth Protocol validation

#### Coverage Threshold

```python
# Fails if coverage < 90%
--cov-fail-under=90
```

#### Artifacts

- Unit test results (30 days)
- Integration test results (30 days)
- Combined coverage report (90 days)
- Coverage badge (90 days)

---

### Performance Testing

**File:** `performance.yml`

Load testing and performance benchmarking.

#### Jobs

1. **Baseline Performance** (15 min)
   - 1000 request baseline
   - Calculates P95/P99 latency
   - **Enforces P95 < 200ms**

2. **Load Test** (20 min)
   - Locust load testing
   - Configurable users/duration
   - Error rate validation

3. **Stress Test** (25 min)
   - Autocannon stress testing
   - 500 concurrent connections
   - System stability validation

4. **Database Performance** (15 min)
   - Query benchmarking
   - Insert/Select performance
   - Connection pool testing

5. **Summary** (10 min)
   - Performance metrics dashboard
   - SLO compliance check
   - Regression detection

#### Truth Protocol SLOs

```yaml
P95_LATENCY_THRESHOLD_MS: '200'
ERROR_RATE_THRESHOLD: '0.5'
TARGET_RPS: '1000'
```

#### Schedule

```yaml
# Daily at 3 AM UTC
schedule:
  - cron: '0 3 * * *'
```

#### Artifacts

- Baseline results (90 days)
- Load test reports (90 days)
- Stress test results (90 days)
- Database benchmarks (90 days)

---

### CodeQL Analysis

**File:** `codeql.yml`

Advanced security analysis with GitHub CodeQL.

#### Jobs

1. **CodeQL Analysis** (30 min)
   - Python code scanning
   - Security-extended queries
   - Quality checks
   - SARIF upload to Security tab

2. **SAST Analysis** (20 min)
   - Bandit static analysis
   - Semgrep security rules
   - Multi-tool validation

3. **Summary** (10 min)
   - Security findings dashboard
   - GitHub Security integration
   - Remediation guidance

#### Features

- **Path Filtering**: Excludes tests, node_modules, venv
- **Query Packs**: security-extended, security-and-quality
- **Auto-fix Suggestions**: For common issues
- **Weekly Scans**: Scheduled Monday 1 AM UTC

#### Schedule

```yaml
schedule:
  - cron: '0 1 * * 1'  # Every Monday
```

---

### Dependabot

**File:** `../dependabot.yml`

Automated dependency updates.

#### Configuration

**Python Dependencies:**
- **Schedule**: Weekly (Monday 3 AM UTC)
- **Limit**: 10 PRs max
- **Grouping**: FastAPI, Security, AI/ML, Database, Testing

**GitHub Actions:**
- **Schedule**: Weekly (Monday 3 AM UTC)
- **Limit**: 5 PRs max

**Docker:**
- **Schedule**: Weekly (Monday 3 AM UTC)
- **Limit**: 3 PRs max

#### Automatic Security Updates

- Critical CVEs: **Immediate PRs** (no limit)
- High severity: **Within 24 hours**
- Medium/Low: **Weekly schedule**

#### Review Process

All Dependabot PRs:
1. Auto-assigned to DevSkyy team
2. Labeled (dependencies, python/docker/actions, security)
3. CI/CD runs automatically
4. Conventional commit format
5. Grouped by ecosystem

---

## 🔧 Troubleshooting

### Common Issues

#### Tests Failing

**Coverage below 90%:**
```bash
# Run tests locally with coverage
pytest --cov=. --cov-report=html --cov-report=term
open htmlcov/index.html  # View coverage report
```

**Fix:** Add tests for uncovered code paths.

#### Security Scan Failures

**HIGH/CRITICAL CVEs found:**
```bash
# Run security scans locally
pip install bandit safety pip-audit
bandit -r . -f json
safety check
pip-audit
```

**Fix:** Update vulnerable dependencies or apply patches.

#### Performance Tests Failing

**P95 latency > 200ms:**
```bash
# Profile application locally
python -m cProfile -o profile.stats main.py
pip install snakeviz
snakeviz profile.stats
```

**Fix:** Optimize slow code paths, add caching, database indexing.

#### Docker Build Failing

**Build errors:**
```bash
# Build locally to debug
docker build -t devskyy:local .
docker run --rm devskyy:local
```

**Fix:** Check Dockerfile syntax, dependency conflicts.

### Workflow Debugging

**View detailed logs:**
1. Go to **Actions** tab
2. Click failing workflow run
3. Expand failed job
4. Review logs and artifacts

**Re-run workflows:**
```bash
# Via GitHub UI
Actions → Failed Run → Re-run failed jobs

# Or push empty commit
git commit --allow-empty -m "chore: trigger CI"
git push
```

**Download artifacts:**
```bash
# Via GitHub CLI
gh run list
gh run view <run-id>
gh run download <run-id>
```

### Getting Help

**Resources:**
- [GitHub Actions Docs](https://docs.github.com/actions)
- [Truth Protocol](../../CLAUDE.md)
- [DevSkyy Documentation](../../README.md)
- [Security Policy](../../SECURITY.md)

**Contact:**
- Create issue in GitHub
- Tag: `ci-cd`, `workflows`, `help-wanted`

---

## 📊 Workflow Status

Check workflow status:

[![CI/CD Pipeline](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/ci-cd.yml)

[![Security Scan](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/security-scan.yml/badge.svg)](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/security-scan.yml)

[![Tests](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/test.yml/badge.svg)](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/test.yml)

[![Performance](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/performance.yml/badge.svg)](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/performance.yml)

[![CodeQL](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/codeql.yml/badge.svg)](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/codeql.yml)

---

## 🎓 Best Practices

### For Developers

1. **Run tests locally** before pushing
2. **Check security scans** with local tools
3. **Review CI logs** if builds fail
4. **Keep dependencies updated** (review Dependabot PRs)
5. **Write tests** for new features
6. **Follow Truth Protocol** requirements

### For Reviewers

1. **Check CI status** before approving PRs
2. **Review security findings** in Security tab
3. **Validate coverage** doesn't decrease
4. **Test performance** impact of changes
5. **Approve Dependabot PRs** after CI passes

### For Maintainers

1. **Monitor workflow runs** weekly
2. **Review error ledgers** for patterns
3. **Update workflows** as needs change
4. **Optimize CI performance** regularly
5. **Keep secrets** up to date

---

## 📝 Changelog

### 2025-11-09 - Initial Implementation
- ✅ Created CI/CD pipeline workflow
- ✅ Added comprehensive security scanning
- ✅ Implemented test suite with 90% coverage
- ✅ Added performance testing (P95 < 200ms)
- ✅ Configured CodeQL security analysis
- ✅ Set up Dependabot automation
- ✅ Enabled SBOM generation
- ✅ Implemented error ledger system

---

**DevSkyy Workflows - Enterprise-Grade CI/CD Automation**

Built with ❤️ following the Truth Protocol for zero-defect deployment.
