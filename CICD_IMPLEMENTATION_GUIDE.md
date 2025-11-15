# CI/CD Pipeline Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the optimized CI/CD pipeline for DevSkyy, transitioning from the current fragmented workflows to a unified, Truth Protocol-compliant pipeline.

---

## Current State vs. Target State

### Current State (Fragmented)
- 6 separate workflows (2,865 lines of YAML)
- Duplicate jobs across workflows
- No actual deployment automation
- Docker images built but not pushed
- Performance testing not in release gates
- SBOM in separate workflow

### Target State (Unified)
- 1 primary release pipeline
- 2-3 specialized scheduled pipelines
- Fully automated deployment
- Docker images signed and pushed to registry
- Performance testing as release gate
- All deliverables in one pipeline

---

## Implementation Phases

### Phase 1: Preparation (Week 1)

#### 1.1 Set Up GitHub Container Registry

**Action:** Configure registry authentication

```bash
# Enable GitHub Container Registry (ghcr.io)
# This is automatic - just need to push images

# Test authentication locally
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Verify access
docker pull ghcr.io/your-org/your-repo/test:latest || echo "Repository ready"
```

**Required Secrets:**
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

#### 1.2 Configure Deployment Environments

**Action:** Create staging and production environments in GitHub

1. Go to repository **Settings → Environments**
2. Create **staging** environment:
   - No protection rules needed
   - Add environment secret: `STAGING_DATABASE_URL`
   - Add environment URL: `https://staging-api.devskyy.com`

3. Create **production** environment:
   - Enable **Required reviewers** (add team members)
   - Set **Wait timer**: 5 minutes
   - Add environment secret: `PRODUCTION_DATABASE_URL`
   - Add environment URL: `https://api.devskyy.com`

#### 1.3 Create Deployment Scripts

**Action:** Implement actual deployment logic

Create `/home/user/DevSkyy/scripts/deploy.sh`:

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}

echo "Deploying to $ENVIRONMENT with image tag $IMAGE_TAG"

case $ENVIRONMENT in
  staging)
    echo "Deploying to staging..."
    # Example: kubectl set image deployment/devskyy-staging devskyy=ghcr.io/org/repo:$IMAGE_TAG
    # Example: helm upgrade devskyy-staging ./charts/devskyy --set image.tag=$IMAGE_TAG
    ;;
  production)
    echo "Deploying to production (blue-green)..."
    # 1. Deploy to green environment
    # kubectl apply -f k8s/production/green/
    # 2. Wait for health checks
    # kubectl wait --for=condition=ready pod -l app=devskyy,env=green --timeout=300s
    # 3. Switch traffic
    # kubectl patch service devskyy -p '{"spec":{"selector":{"version":"green"}}}'
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "Deployment to $ENVIRONMENT completed successfully"
```

Make executable:
```bash
chmod +x scripts/deploy.sh
```

#### 1.4 Create Rollback Script

Create `/home/user/DevSkyy/scripts/rollback.sh`:

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-production}
PREVIOUS_VERSION=${2:-}

if [ -z "$PREVIOUS_VERSION" ]; then
  echo "Error: Previous version not specified"
  exit 1
fi

echo "Rolling back $ENVIRONMENT to version $PREVIOUS_VERSION"

case $ENVIRONMENT in
  production)
    # Switch traffic back to blue environment
    # kubectl patch service devskyy -p '{"spec":{"selector":{"version":"blue"}}}'
    echo "Rollback completed"
    ;;
  *)
    echo "Rollback not implemented for $ENVIRONMENT"
    exit 1
    ;;
esac
```

Make executable:
```bash
chmod +x scripts/rollback.sh
```

#### 1.5 Test the Optimized Pipeline (Dry Run)

**Action:** Enable the new pipeline on a test branch

```bash
# Create a test branch
git checkout -b test/optimized-pipeline

# Enable the workflow (it won't run on feature branches by default)
# Edit .github/workflows/ci-cd-optimized.yml to add test branch:
# on:
#   push:
#     branches: [main, develop, test/optimized-pipeline]

# Commit and push
git add .github/workflows/ci-cd-optimized.yml
git commit -m "test: Enable optimized pipeline for testing"
git push origin test/optimized-pipeline
```

**Expected Result:**
- Pipeline runs all stages
- Deployment stages are skipped (only run on main/develop)
- All artifacts generated
- Release gate validation passes

---

### Phase 2: Migration (Week 2)

#### 2.1 Rename Current Workflows (Backup)

**Action:** Disable current workflows temporarily

```bash
# Rename current workflows to .bak
cd .github/workflows/
mv ci-cd.yml ci-cd.yml.bak
mv test.yml test.yml.bak
# Keep performance.yml and security-scan.yml for now (will refactor later)
```

Commit:
```bash
git add .github/workflows/
git commit -m "ci: Backup current workflows before migration"
git push origin main
```

#### 2.2 Activate Optimized Pipeline

**Action:** Rename and activate the optimized workflow

```bash
mv ci-cd-optimized.yml ci-cd.yml

git add .github/workflows/ci-cd.yml
git commit -m "ci: Activate optimized unified CI/CD pipeline"
git push origin main
```

#### 2.3 Monitor First Production Run

**Action:** Monitor the first execution carefully

1. Watch the GitHub Actions tab
2. Verify each stage completes successfully
3. Check artifact uploads
4. Review error ledger
5. Validate release gate report

**Troubleshooting Checklist:**
- [ ] All jobs show green status
- [ ] Docker image pushed to ghcr.io
- [ ] Docker image signed with Cosign
- [ ] Performance tests pass (P95 < 200ms)
- [ ] Coverage >= 90%
- [ ] Error ledger generated
- [ ] OpenAPI spec valid
- [ ] SBOM generated (both formats)

#### 2.4 Test Deployment to Staging

**Action:** Verify staging deployment works

Once the pipeline completes:
1. Check staging environment URL: `https://staging-api.devskyy.com/health`
2. Verify Docker image is running
3. Check application logs
4. Run manual smoke tests

#### 2.5 Test Production Deployment

**Action:** Merge to main and deploy to production

```bash
git checkout main
git merge test/optimized-pipeline
git push origin main
```

**Manual Approval Required:**
1. Pipeline will pause at production deployment
2. Reviewer approves deployment in GitHub Actions UI
3. Deployment proceeds automatically
4. Monitor post-deployment health checks

---

### Phase 3: Optimization (Week 3)

#### 3.1 Consolidate Scheduled Workflows

**Action:** Refactor performance and security workflows

Create `.github/workflows/scheduled-performance.yml`:

```yaml
name: Scheduled Performance Regression Tests

on:
  schedule:
    - cron: '0 3 * * *'  # Daily at 3 AM UTC
  workflow_dispatch:

jobs:
  load-test:
    # Use jobs from performance.yml but add trend analysis

  stress-test:
    # Use jobs from performance.yml

  performance-regression:
    # Compare against historical baseline
    # Alert on >10% degradation
```

Create `.github/workflows/scheduled-security.yml`:

```yaml
name: Scheduled Security Deep Scan

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sundays at 2 AM UTC
  workflow_dispatch:

jobs:
  deep-security-scan:
    # Full security audit including license compliance

  dependency-review:
    # Check for new CVEs in dependencies
```

#### 3.2 Add CHANGELOG Automation

**Action:** Implement proper changelog generation

Install conventional changelog tools:

```bash
npm install -g conventional-changelog-cli
```

Update `.github/workflows/ci-cd.yml` to use:

```yaml
- name: Generate CHANGELOG
  run: |
    conventional-changelog -p angular -i CHANGELOG.md -s
```

**Enforce Conventional Commits:**

Add `.github/workflows/commit-lint.yml`:

```yaml
name: Commit Lint

on: [pull_request]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: wagoid/commitlint-github-action@v5
```

#### 3.3 Implement Performance Regression Detection

**Action:** Store and compare performance metrics

Create `scripts/check-performance-regression.py`:

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def load_baseline():
    """Load historical baseline from artifacts."""
    baseline_file = Path('artifacts/performance-baseline.json')
    if baseline_file.exists():
        with open(baseline_file) as f:
            return json.load(f)
    return None

def check_regression(current_p95, baseline_p95, threshold=0.10):
    """Check if current P95 is significantly worse than baseline."""
    if baseline_p95 is None:
        print("No baseline found, setting current as baseline")
        return False

    regression_percent = (current_p95 - baseline_p95) / baseline_p95

    if regression_percent > threshold:
        print(f"❌ Performance regression detected!")
        print(f"Current P95: {current_p95}ms")
        print(f"Baseline P95: {baseline_p95}ms")
        print(f"Regression: {regression_percent * 100:.1f}%")
        return True

    print(f"✅ No performance regression")
    print(f"Current P95: {current_p95}ms vs Baseline: {baseline_p95}ms")
    return False

if __name__ == '__main__':
    with open('performance-results.json') as f:
        current = json.load(f)

    baseline = load_baseline()
    baseline_p95 = baseline.get('p95_latency_ms') if baseline else None

    if check_regression(current['p95_latency_ms'], baseline_p95):
        sys.exit(1)

    # Update baseline
    with open('artifacts/performance-baseline.json', 'w') as f:
        json.dump(current, f, indent=2)
```

Make executable:
```bash
chmod +x scripts/check-performance-regression.py
```

#### 3.4 Add Deployment Notifications

**Action:** Set up Slack notifications

Add to deployment jobs:

```yaml
- name: Notify deployment success
  if: success()
  uses: 8398a7/action-slack@v3
  with:
    status: custom
    custom_payload: |
      {
        text: "🚀 DevSkyy deployed to ${{ env.ENVIRONMENT }}",
        attachments: [{
          color: 'good',
          text: `Commit: ${{ github.sha }}\nBy: ${{ github.actor }}\nURL: ${{ env.DEPLOYMENT_URL }}`
        }]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

- name: Notify deployment failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: custom
    custom_payload: |
      {
        text: "❌ DevSkyy deployment to ${{ env.ENVIRONMENT }} FAILED",
        attachments: [{
          color: 'danger',
          text: `Commit: ${{ github.sha }}\nBy: ${{ github.actor }}\nRun: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}`
        }]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

**Required Secret:**
- `SLACK_WEBHOOK` - Create webhook at: https://api.slack.com/messaging/webhooks

---

### Phase 4: Advanced Features (Week 4)

#### 4.1 Implement Canary Deployment

**Action:** Add progressive rollout capability

Create `scripts/canary-deploy.sh`:

```bash
#!/bin/bash
set -euo pipefail

IMAGE_TAG=$1
STAGES=(5 25 50 100)

for STAGE in "${STAGES[@]}"; do
  echo "Deploying canary at ${STAGE}%..."

  # Update canary deployment with traffic percentage
  # kubectl set image deployment/devskyy-canary devskyy=ghcr.io/org/repo:$IMAGE_TAG
  # kubectl patch virtualservice devskyy -p '{"spec":{"http":[{"route":[{"destination":{"host":"canary"},"weight":'$STAGE'}]}]}}'

  echo "Waiting 5 minutes for metrics..."
  sleep 300

  # Check error rate
  ERROR_RATE=$(curl -s https://api.devskyy.com/metrics | jq '.error_rate')

  if (( $(echo "$ERROR_RATE > 0.5" | bc -l) )); then
    echo "❌ Error rate too high at ${STAGE}%, rolling back!"
    ./scripts/rollback.sh production
    exit 1
  fi

  echo "✅ Canary at ${STAGE}% is healthy"
done

echo "🎉 Canary deployment completed successfully"
```

#### 4.2 Add Automated Rollback

**Action:** Implement health-check based rollback

Add to deployment jobs:

```yaml
- name: Monitor post-deployment
  id: monitor
  run: |
    for i in {1..12}; do  # Monitor for 2 minutes
      ERROR_RATE=$(curl -s https://api.devskyy.com/metrics | jq -r '.error_rate')
      P95_LATENCY=$(curl -s https://api.devskyy.com/metrics | jq -r '.p95_latency')

      echo "Iteration $i: Error Rate=$ERROR_RATE%, P95=$P95_LATENCY ms"

      if (( $(echo "$ERROR_RATE > 1.0" | bc -l) )); then
        echo "error_spike=true" >> $GITHUB_OUTPUT
        break
      fi

      if (( $(echo "$P95_LATENCY > 300" | bc -l) )); then
        echo "latency_spike=true" >> $GITHUB_OUTPUT
        break
      fi

      sleep 10
    done

- name: Automatic rollback on failure
  if: steps.monitor.outputs.error_spike == 'true' || steps.monitor.outputs.latency_spike == 'true'
  run: |
    echo "❌ Deployment failed health checks, initiating automatic rollback..."
    ./scripts/rollback.sh production ${{ env.PREVIOUS_VERSION }}
    exit 1
```

#### 4.3 Implement Feature Flags

**Action:** Add feature flag support for safer deployments

```python
# Add to application configuration
FEATURE_FLAGS = {
    'new_api_endpoint': os.getenv('FEATURE_NEW_API', 'false').lower() == 'true',
    'enhanced_ml_model': os.getenv('FEATURE_ML_V2', 'false').lower() == 'true',
}

# Use in deployment
# 1. Deploy with feature disabled
# 2. Enable for 10% of users
# 3. Monitor metrics
# 4. Gradually increase to 100%
```

#### 4.4 Add Release Tagging

**Action:** Automatic version tagging on successful deployments

```yaml
- name: Create release tag
  if: github.ref == 'refs/heads/main' && success()
  run: |
    # Generate version from commits
    VERSION=$(conventional-changelog-cli --preset angular --release-count 0 | grep "##" | head -1 | sed 's/## //')

    git tag -a "v${VERSION}" -m "Release v${VERSION}"
    git push origin "v${VERSION}"
```

---

## Maintenance & Monitoring

### Daily Checks
- [ ] Review scheduled pipeline results
- [ ] Check performance trends
- [ ] Review security scan reports

### Weekly Checks
- [ ] Review error ledger for patterns
- [ ] Update dependencies (security patches)
- [ ] Review and merge CodeQL findings

### Monthly Checks
- [ ] Review pipeline execution times (optimize if needed)
- [ ] Update tool versions (Ruff, Mypy, etc.)
- [ ] Review and update Truth Protocol compliance

---

## Rollback Plan

If the optimized pipeline causes issues:

```bash
# Emergency rollback to old workflows
cd .github/workflows/
mv ci-cd.yml ci-cd-optimized.yml.disabled
mv ci-cd.yml.bak ci-cd.yml
mv test.yml.bak test.yml

git add .
git commit -m "ci: Emergency rollback to previous workflows"
git push origin main
```

---

## Success Metrics

### Week 1 (After Implementation)
- [ ] Pipeline executes successfully on main branch
- [ ] All Truth Protocol gates pass
- [ ] Docker images pushed and signed
- [ ] Staging deployment works

### Week 2 (After Migration)
- [ ] Production deployment successful
- [ ] Zero manual intervention needed
- [ ] All artifacts generated correctly

### Month 1 (Ongoing)
- [ ] Pipeline execution time < 50 minutes
- [ ] Zero failed deployments
- [ ] 100% Truth Protocol compliance
- [ ] All scheduled scans running

---

## Troubleshooting

### Issue: Docker build fails

**Solution:**
```bash
# Check Dockerfile syntax
docker build -t test .

# Check buildx setup
docker buildx ls
```

### Issue: Cosign signing fails

**Solution:**
```bash
# Verify OIDC token available
echo $ACTIONS_ID_TOKEN_REQUEST_URL

# Check Cosign installation
cosign version
```

### Issue: Deployment fails

**Solution:**
```bash
# Check deployment script permissions
ls -la scripts/deploy.sh

# Test deployment script locally
./scripts/deploy.sh staging test-tag
```

### Issue: Performance tests fail

**Solution:**
```bash
# Check if application started
curl http://localhost:8000/health

# Check database connection
psql $DATABASE_URL -c "SELECT 1"
```

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Cosign Documentation](https://docs.sigstore.dev/cosign/overview/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Truth Protocol (CLAUDE.md)](/home/user/DevSkyy/CLAUDE.md)

---

## Support

For issues with CI/CD pipeline:
1. Check GitHub Actions logs
2. Review error ledger artifacts
3. Consult `.claude/agents/cicd-pipeline.md`
4. Create issue with `ci/cd` label

---

**Last Updated:** 2025-11-15
**Version:** 1.0.0
**Maintained by:** DevSkyy Platform Team
