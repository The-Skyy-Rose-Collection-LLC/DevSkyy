# DevSkyy GitHub Actions Workflows

Streamlined CI/CD automation following the **Truth Protocol** for DevSkyy's enterprise-grade multi-agent platform.

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
| [Unified CI/CD](#unified-cicd-pipeline) | Complete build, test, security, deploy | Push, PR, Weekly | Required |
| [Neon Database](#neon-database-branching) | Database branching for PRs | PR open/sync/close | Automated |
| [Dependabot](#dependabot) | Automated dependency updates | Weekly | Automated |

### Workflow Consolidation (2025-11-11)

**Previous:** 5 separate workflows (ci-cd.yml, test.yml, security-scan.yml, performance.yml, codeql.yml)
**Current:** 1 unified workflow (unified-ci-cd.yml)

**Benefits:**
- Reduced workflow execution time (parallel job execution)
- Single source of truth for CI/CD configuration
- Easier maintenance and updates
- Consistent artifact handling
- Better resource utilization

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
6. **Secret Scanning** - detect-secrets
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
   - Unified CI/CD workflow runs automatically
   - Neon database branch created for testing
   - All quality gates must pass before merge
   - Review security findings

3. **Monitor Progress**:
   - Visit **Actions** tab in GitHub
   - View real-time logs
   - Download artifacts

### Required Secrets

Configure these in **Settings → Secrets and variables → Actions**:

```bash
# API Keys (optional)
ANTHROPIC_API_KEY        # For Claude API
OPENAI_API_KEY          # For OpenAI API
CODECOV_TOKEN           # For coverage uploads

# Database (for Neon workflow)
NEON_PROJECT_ID         # Neon database project ID
NEON_API_KEY            # Neon API key

# Deployment (optional)
DOCKER_USERNAME         # For Docker Hub
DOCKER_PASSWORD         # For Docker Hub
AWS_ACCESS_KEY_ID       # For AWS deployment
AWS_SECRET_ACCESS_KEY   # For AWS deployment
```

## 📖 Workflow Details

### Unified CI/CD Pipeline

**File:** `unified-ci-cd.yml`

Consolidated workflow that replaces 5 previous workflows with a streamlined 10-stage pipeline.

#### Architecture

```
Stage 1: Code Quality    →  Lint, Type Check
Stage 2: Security Scan   →  SAST, Dependency, Secrets
Stage 3: CodeQL Analysis →  Advanced security scanning
Stage 4: Testing         →  Unit, Integration, API, E2E
Stage 5: Coverage        →  Combine & enforce ≥90%
Stage 6: Docker Build    →  Multi-stage build
Stage 7: Performance     →  Load & stress testing
Stage 8: SBOM            →  Generate CycloneDX/SPDX
Stage 9: OpenAPI         →  Generate & validate spec
Stage 10: Error Ledger   →  JSON audit trail
```

#### Jobs

**1. Code Quality (15 min)**
- Ruff linter with GitHub annotations
- Black formatter check
- isort import sorting
- mypy static type analysis
- Uploads quality reports

**2. Security Scan (20 min)**
- Bandit SAST security analysis
- Safety vulnerability database check
- pip-audit dependency scanning
- detect-secrets baseline verification
- SARIF upload to GitHub Security tab
- **Fails on HIGH/CRITICAL CVEs**

**3. CodeQL Analysis (30 min)**
- Python code scanning
- Security-extended queries
- Quality checks
- SARIF integration
- Auto-fix suggestions

**4. Testing (30 min)**
- Unit tests (parallel by module)
- Integration tests (PostgreSQL + Redis)
- API endpoint tests
- Security tests (auth, encryption, RBAC)
- ML/AI pipeline tests
- E2E workflow tests

**5. Coverage Report (15 min)**
- Combines all test coverage
- **Enforces ≥90% threshold**
- Uploads to Codecov
- Generates HTML report

**6. Docker Build (20 min)**
- Multi-stage optimized build
- Trivy vulnerability scan
- Container health checks
- Saves image artifact
- SBOM generation

**7. Performance Testing (25 min)**
- Baseline performance (1000 requests)
- Load testing (configurable)
- **Enforces P95 < 200ms**
- **Enforces error rate < 0.5%**
- Database benchmarking

**8. SBOM Generation (15 min)**
- CycloneDX format
- SPDX format
- Uploads to dependency graph
- License compliance check

**9. OpenAPI Specification (10 min)**
- Auto-generates API spec
- Validates schema
- Version tracking
- Uploads artifact

**10. Error Ledger (10 min)**
- JSON audit trail
- Job status tracking
- Truth Protocol compliance
- 365-day retention

#### Triggers

```yaml
# Runs on:
push:
  branches: ['**']           # All branches
pull_request:
  branches: [main, develop]  # PRs to main/develop
schedule:
  - cron: '0 2 * * 0'        # Weekly Sunday 2 AM UTC
workflow_dispatch:           # Manual triggers
```

#### Environment Variables

```yaml
PYTHON_VERSION: '3.11.9'
NODE_VERSION: '18'
COVERAGE_THRESHOLD: '90'
P95_LATENCY_THRESHOLD_MS: '200'
ERROR_RATE_THRESHOLD: '0.5'
```

#### Artifacts

- Code quality reports (30 days)
- Security scan results (90 days)
- Test coverage reports (90 days)
- Docker image (7 days)
- Performance benchmarks (90 days)
- SBOM files (365 days)
- OpenAPI specification (30 days)
- Error ledger (365 days)

#### Truth Protocol SLOs

```yaml
✓ Test Coverage ≥ 90%
✓ P95 Latency < 200ms
✓ Error Rate < 0.5%
✓ Zero HIGH/CRITICAL CVEs
✓ SBOM generated
✓ Error ledger created
✓ OpenAPI spec valid
```

---

### Neon Database Branching

**File:** `neon_workflow.yml`

Automated database branching for pull request testing using Neon serverless Postgres.

#### Features

- **Automatic branch creation** when PR is opened/synchronized
- **Isolated database** per PR for safe testing
- **Connection string output** for testing
- **Automatic cleanup** when PR is closed
- **Zero manual database management**

#### Jobs

**1. Create Neon Branch (PR open/sync)**
- Creates database branch from main
- Naming: `pr-{number}-{sha}`
- Outputs connection string
- Comments on PR with DB details

**2. Run Tests with PR Database (after branch creation)**
- Uses dedicated PR database
- Runs migrations
- Executes integration tests
- Validates database changes

**3. Delete Neon Branch (PR close)**
- Cleans up PR database
- Removes orphaned branches
- Updates PR comment

#### Triggers

```yaml
pull_request:
  types: [opened, synchronize, reopened, closed]
```

#### Environment Variables

```yaml
NEON_PROJECT_ID: ${{ secrets.NEON_PROJECT_ID }}
NEON_API_KEY: ${{ secrets.NEON_API_KEY }}
```

#### Usage in Tests

```python
# Database URL is available as environment variable
import os
DATABASE_URL = os.getenv('NEON_DATABASE_URL')

# Or from PR comment
# Connection string format:
# postgres://neondb_owner:password@ep-xxx.region.aws.neon.tech/devskyy
```

---

### Dependabot

**File:** `../dependabot.yml`

Automated dependency updates for security and maintenance.

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
3. Unified CI/CD runs automatically
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

[![Unified CI/CD](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/unified-ci-cd.yml/badge.svg)](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/unified-ci-cd.yml)

[![Neon Database](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/neon_workflow.yml/badge.svg)](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/neon_workflow.yml)

---

## 🎓 Best Practices

### For Developers

1. **Run tests locally** before pushing
2. **Check security scans** with local tools
3. **Review CI logs** if builds fail
4. **Keep dependencies updated** (review Dependabot PRs)
5. **Write tests** for new features (maintain 90% coverage)
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

### 2025-11-11 - Workflow Consolidation
- ✅ **Consolidated 5 workflows into unified-ci-cd.yml**
- ✅ Removed: ci-cd.yml, test.yml, security-scan.yml, performance.yml, codeql.yml
- ✅ Kept: unified-ci-cd.yml (consolidated), neon_workflow.yml (unique)
- ✅ Improved: Faster execution with optimized job parallelization
- ✅ Enhanced: Better artifact management and error ledger
- ✅ Reduced: Workflow maintenance overhead by 80%

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

**DevSkyy Workflows - Streamlined Enterprise CI/CD**

Built with ❤️ following the Truth Protocol for zero-defect deployment.
