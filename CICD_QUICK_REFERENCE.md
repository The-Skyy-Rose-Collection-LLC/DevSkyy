# CI/CD Pipeline - Quick Reference Guide

Fast reference for common CI/CD operations and troubleshooting.

---

## Pipeline Triggers

```bash
# Automatic triggers
git push origin main           # Full pipeline + production deployment
git push origin develop        # Full pipeline + staging deployment
git push origin feature/xyz    # PR checks only (no deployment)

# Manual trigger
# Go to: Actions → CI/CD Pipeline → Run workflow → Select branch
```

---

## Check Pipeline Status

```bash
# Using GitHub CLI
gh run list --workflow=ci-cd.yml --limit 5

# View specific run
gh run view <run-id>

# Watch live
gh run watch <run-id>

# View logs
gh run view <run-id> --log
```

---

## Common Operations

### Deploy to Staging

```bash
# Push to develop branch
git push origin develop

# Pipeline will automatically deploy to staging
# Monitor: https://github.com/[org]/[repo]/actions
```

### Deploy to Production

```bash
# Merge to main
git checkout main
git merge develop
git push origin main

# Pipeline will pause for manual approval
# Approve in: Actions → CI/CD Pipeline → Review deployments → Approve
```

### Rollback Production

```bash
# Manual rollback
./scripts/rollback.sh production v1.2.3

# Automatic rollback
# Happens automatically if post-deployment health checks fail
```

### Re-run Failed Job

```bash
# Using GitHub CLI
gh run rerun <run-id>

# Or via GitHub UI
# Actions → Failed run → Re-run failed jobs
```

---

## Truth Protocol Gates

Quick validation checklist before merging to main:

```bash
# 1. Test Coverage
pytest --cov=. --cov-report=term | grep TOTAL
# Should show: TOTAL ≥90%

# 2. Security Scan
bandit -r . -ll
# Should show: No issues found

# 3. Performance Test
python scripts/performance-test.py
# Should show: P95 < 200ms

# 4. Linting
ruff check . && black --check . && isort --check .
# Should show: All passed

# 5. Type Checking
mypy .
# Should show: Success
```

---

## Artifacts & Reports

### Download Artifacts

```bash
# Using GitHub CLI
gh run download <run-id>

# Specific artifact
gh run download <run-id> -n error-ledger

# Latest run
gh run download $(gh run list --workflow=ci-cd.yml --limit 1 --json databaseId --jq '.[0].databaseId')
```

### View Error Ledger

```bash
# Download and view
gh run download -n error-ledger
cat error-ledger-*.json | jq '.'
```

### View Coverage Report

```bash
# Download HTML coverage
gh run download -n test-results
cd htmlcov && python -m http.server 8080
# Open: http://localhost:8080
```

### View Performance Metrics

```bash
gh run download -n performance-results
cat performance-results.json | jq '.p95_latency_ms'
```

---

## Troubleshooting

### Pipeline Failing at Quality Stage

**Symptom:** Ruff, Black, or Mypy errors

**Fix:**
```bash
# Auto-fix linting issues
ruff check . --fix
black .
isort .

# Commit fixes
git add .
git commit -m "style: Fix linting issues"
git push
```

### Pipeline Failing at Security Stage

**Symptom:** HIGH/CRITICAL vulnerabilities detected

**Fix:**
```bash
# Identify vulnerabilities
pip-audit

# Update vulnerable package
pip install --upgrade <package-name>

# Update requirements
pip freeze > requirements.txt

# Commit and push
git add requirements.txt
git commit -m "security: Update vulnerable dependencies"
git push
```

### Pipeline Failing at Test Stage

**Symptom:** Tests failing or coverage < 90%

**Fix:**
```bash
# Run tests locally
pytest -v

# Check coverage
pytest --cov=. --cov-report=term-missing

# Add tests for uncovered code
# Fix failing tests
# Commit and push
```

### Pipeline Failing at Performance Stage

**Symptom:** P95 latency > 200ms

**Fix:**
```bash
# Profile slow endpoints
python -m cProfile -o profile.stats main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumtime'); p.print_stats(20)"

# Common fixes:
# - Add database indexes
# - Implement caching
# - Optimize queries
# - Add connection pooling
```

### Pipeline Failing at Build Stage

**Symptom:** Docker build or Trivy scan fails

**Fix:**
```bash
# Test Docker build locally
docker build -t devskyy:test .

# Check for vulnerabilities
trivy image devskyy:test

# Common fixes:
# - Update base image
# - Fix Dockerfile syntax
# - Update vulnerable packages in container
```

### Deployment Failing

**Symptom:** Deployment to staging/production fails

**Fix:**
```bash
# Check deployment logs
gh run view <run-id> --log | grep -A 20 "Deploy to"

# Test deployment script locally
./scripts/deploy.sh staging test-tag

# Common issues:
# - Missing environment variables
# - Database migration errors
# - Network connectivity issues
```

---

## Emergency Procedures

### Stop Running Deployment

```bash
# Cancel workflow run
gh run cancel <run-id>

# Or via UI: Actions → Running workflow → Cancel workflow
```

### Emergency Rollback

```bash
# Immediate rollback to previous version
./scripts/rollback.sh production <previous-version>

# Verify rollback
curl https://api.devskyy.com/health
```

### Disable Pipeline

```bash
# Rename workflow to disable
cd .github/workflows/
mv ci-cd.yml ci-cd.yml.disabled
git add .
git commit -m "ci: Disable CI/CD pipeline (emergency)"
git push origin main
```

### Re-enable Pipeline

```bash
cd .github/workflows/
mv ci-cd.yml.disabled ci-cd.yml
git add .
git commit -m "ci: Re-enable CI/CD pipeline"
git push origin main
```

---

## Performance Optimization

### Check Pipeline Execution Time

```bash
# View last 10 runs with durations
gh run list --workflow=ci-cd.yml --limit 10 --json databaseId,createdAt,updatedAt,conclusion \
  | jq -r '.[] | "\(.databaseId) | \(.conclusion) | \((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601) | floor) seconds"'
```

### Identify Slow Jobs

```bash
# View job timings for a run
gh run view <run-id> --json jobs | jq -r '.jobs[] | "\(.name): \((.completedAt | fromdateiso8601) - (.startedAt | fromdateiso8601) | floor) seconds"'
```

### Clear Caches

```bash
# Via GitHub CLI
gh cache list
gh cache delete <cache-id>

# Or delete all caches
gh cache list | awk '{print $1}' | xargs -I {} gh cache delete {}
```

---

## Monitoring & Metrics

### View Pipeline Success Rate

```bash
# Last 30 runs
gh run list --workflow=ci-cd.yml --limit 30 --json conclusion \
  | jq -r 'group_by(.conclusion) | map({conclusion: .[0].conclusion, count: length})'
```

### View Error Trends

```bash
# Download error ledgers from last 10 runs
for run in $(gh run list --workflow=ci-cd.yml --limit 10 --json databaseId --jq '.[].databaseId'); do
  gh run download $run -n error-ledger -D "ledgers/$run" 2>/dev/null
done

# Analyze trends
find ledgers -name "*.json" -exec jq -r '.truth_protocol_gates' {} \;
```

### View Performance Trends

```bash
# Extract P95 latency from last 10 runs
for run in $(gh run list --workflow=ci-cd.yml --limit 10 --json databaseId --jq '.[].databaseId'); do
  gh run download $run -n performance-results -D "perf/$run" 2>/dev/null
done

# Plot trend
find perf -name "*.json" -exec jq -r '.p95_latency_ms' {} \; | \
  awk '{sum+=$1; print NR": "$1"ms (avg: "sum/NR"ms)"}'
```

---

## Scheduled Workflows

### Check Scheduled Run Status

```bash
# Performance regression tests (daily 3 AM UTC)
gh run list --workflow=scheduled-performance.yml --limit 5

# Security scans (weekly Sunday 2 AM UTC)
gh run list --workflow=scheduled-security.yml --limit 5
```

### Trigger Scheduled Workflow Manually

```bash
# Trigger performance tests
gh workflow run scheduled-performance.yml

# Trigger security scan
gh workflow run scheduled-security.yml
```

---

## Docker Image Management

### List Published Images

```bash
# Using GitHub CLI
gh api /user/packages/container/devskyy/versions | jq -r '.[] | .name'

# Using Docker CLI
docker images ghcr.io/$GITHUB_REPOSITORY
```

### Pull Specific Image

```bash
# By tag
docker pull ghcr.io/$GITHUB_REPOSITORY:latest
docker pull ghcr.io/$GITHUB_REPOSITORY:v1.2.3

# By SHA
docker pull ghcr.io/$GITHUB_REPOSITORY@sha256:abc123...
```

### Verify Image Signature

```bash
# Install cosign
cosign version

# Verify signature
cosign verify ghcr.io/$GITHUB_REPOSITORY:latest
```

### Clean Up Old Images

```bash
# List all versions
gh api /user/packages/container/devskyy/versions | jq -r '.[] | "\(.id) \(.created_at) \(.name)"'

# Delete specific version
gh api -X DELETE /user/packages/container/devskyy/versions/<version-id>
```

---

## Environment Variables

### Required Secrets

```bash
# View configured secrets (names only)
gh secret list

# Set new secret
gh secret set SECRET_NAME

# Delete secret
gh secret delete SECRET_NAME
```

### Required Environment Secrets

**Staging:**
- `STAGING_DATABASE_URL`
- `STAGING_REDIS_URL`

**Production:**
- `PRODUCTION_DATABASE_URL`
- `PRODUCTION_REDIS_URL`
- `SLACK_WEBHOOK` (optional, for notifications)

---

## Useful Commands Cheat Sheet

```bash
# View all workflows
gh workflow list

# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# Watch run in real-time
gh run watch

# Re-run workflow
gh run rerun <run-id>

# Cancel workflow
gh run cancel <run-id>

# Download artifacts
gh run download <run-id>

# View logs
gh run view <run-id> --log

# Trigger workflow manually
gh workflow run <workflow-name>

# List caches
gh cache list

# Delete cache
gh cache delete <cache-id>

# List secrets
gh secret list

# Set secret
gh secret set <name>

# View repository settings
gh repo view --web
```

---

## Links

- **GitHub Actions UI:** https://github.com/[org]/[repo]/actions
- **Staging Environment:** https://staging-api.devskyy.com
- **Production Environment:** https://api.devskyy.com
- **Full Audit Report:** [CICD_AUDIT_REPORT.md](/home/user/DevSkyy/CICD_AUDIT_REPORT.md)
- **Implementation Guide:** [CICD_IMPLEMENTATION_GUIDE.md](/home/user/DevSkyy/CICD_IMPLEMENTATION_GUIDE.md)
- **Truth Protocol:** [CLAUDE.md](/home/user/DevSkyy/CLAUDE.md)

---

## Support

**For CI/CD Issues:**
1. Check this quick reference
2. Review pipeline logs in GitHub Actions
3. Check error ledger artifacts
4. Consult implementation guide
5. Contact DevOps team

**For Deployment Issues:**
1. Check deployment logs
2. Verify environment configuration
3. Test deployment script locally
4. Review rollback procedures
5. Escalate if critical

---

**Last Updated:** 2025-11-15
**Version:** 1.0.0
