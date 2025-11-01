# GitHub Actions Workflows - Enterprise CI/CD

Enterprise-grade workflows following Truth Protocol standards with pinned versions, multi-stage gates, and comprehensive security scanning.

## Workflows Overview

### 1. CI Pipeline (`ci.yml`)

**Trigger:** Push to main/develop, PRs, claude/** branches

**Stages:**
1. **Quality** - Ruff lint + format + MyPy type checking
2. **Security** - Bandit SAST + Safety dependency scan
3. **Test** - Unit tests with ≥90% coverage requirement
4. **Integration** - Full integration test suite
5. **Build** - Package build and verification
6. **Gate** - All stages must pass

**Requirements:**
- Python 3.11.9 (pinned)
- Coverage ≥90% (enforced)
- Zero linting errors
- Zero type errors
- No HIGH/CRITICAL security issues

**Artifacts:**
- Test coverage reports (XML)
- Security scan results (JSON)
- Build packages (wheel/sdist)

### 2. Security Scanning (`security.yml`)

**Trigger:** Push, PRs, Daily at 02:00 UTC

**Scans:**
- **Trivy** - Filesystem vulnerability scan (CRITICAL/HIGH)
- **pip-audit** - Python dependency vulnerabilities
- **Bandit** - SAST code analysis
- **TruffleHog** - Secret detection
- **CodeQL** - Semantic code analysis

**Outputs:**
- SARIF reports uploaded to GitHub Security
- JSON audit reports (90-day retention)
- Security gate status

**Standards:**
- Zero secrets in codebase
- No unpatched CRITICAL vulnerabilities
- SAST findings reviewed and addressed

### 3. Docker Build (`docker.yml`)

**Trigger:** Push to main, version tags

**Features:**
- **Multi-arch** - linux/amd64 + linux/arm64
- **Layer caching** - GitHub Actions cache
- **SBOM** - SPDX format generation
- **Signing** - Cosign keyless signing
- **Scanning** - Trivy image scan
- **Provenance** - Attestation generation

**Registry:** ghcr.io
**Tags:** latest, semver, branch, sha

**Verification:**
```bash
# Verify signature
cosign verify ghcr.io/org/fashion-ai-repo:latest

# Check SBOM
cosign verify-attestation --type spdx ghcr.io/org/fashion-ai-repo:latest
```

### 4. Release Automation (`release.yml`)

**Trigger:** Version tags (v*.*.*)

**Process:**
1. Validate semver format
2. Build Python packages
3. Generate changelog (structured)
4. Create GitHub release
5. Publish to PyPI

**Changelog Sections:**
- ✨ Features
- 🐛 Fixes
- 🔒 Security
- 📊 Commit count

**Artifacts:**
- Python packages (wheel + sdist)
- SHA256 checksums
- Changelog markdown

### 5. Dependency Management (`dependencies.yml`)

**Trigger:** Weekly (Mon 03:00 UTC), Manual

**Jobs:**
- **Audit** - pip-audit + safety scans
- **Outdated** - Track available updates
- **Update** - Auto-create PR with updates
- **License** - Compliance check

**License Policy:**
- ✅ MIT, Apache, BSD compatible
- ⚠️  GPL/AGPL require review
- ❌ Unknown licenses blocked

## Truth Protocol Compliance

| Requirement | Implementation | Verification |
|-------------|----------------|--------------|
| Pin versions | All tools versioned (pip==24.0, ruff==0.1.7) | CI enforces exact versions |
| Test coverage ≥90% | `--cov-fail-under=90` | CI fails if below threshold |
| No HIGH/CRITICAL CVEs | Trivy + pip-audit gates | Security workflow blocks |
| Docker signed | Cosign keyless signing | Signature verified in workflow |
| SBOM generation | SPDX format | Uploaded as artifact |
| Error ledger | Artifacts always uploaded | 30-90 day retention |
| No placeholders | All code executes | Tested in CI |
| Security baseline | Bandit + Safety + Trivy + CodeQL | Multi-layer scanning |

## Workflow Dependencies

```
ci.yml
├── quality (Stage 1)
│   ├── Ruff lint
│   ├── Ruff format
│   └── MyPy type
├── security (Stage 2)
│   ├── Bandit
│   └── Safety
├── test (Stage 3)
│   └── Pytest (≥90% coverage)
├── integration (Stage 4)
│   └── Integration tests
├── build (Stage 5)
│   └── Package build
└── ci-success (Gate)

security.yml
├── trivy-scan
├── dependency-audit
├── bandit-sast
├── secrets-scan
├── codeql
└── security-gate

docker.yml
├── build-push
│   ├── Multi-arch build
│   ├── SBOM generation
│   ├── Trivy scan
│   ├── Cosign sign
│   └── Verify signature
└── docker-gate

release.yml
├── validate-tag
├── build-release
├── generate-changelog
├── create-release
└── publish-pypi

dependencies.yml
├── dependency-audit
├── check-outdated
├── update-dependencies (manual)
├── license-compliance
└── dependency-gate
```

## Usage Examples

### Trigger Manual Dependency Update
```bash
# Via GitHub CLI
gh workflow run dependencies.yml

# Via UI
Actions → Dependency Management → Run workflow
```

### Create Release
```bash
# Tag with semver
git tag v1.2.3
git push origin v1.2.3

# Workflow auto-triggers
# - Builds packages
# - Generates changelog
# - Creates GitHub release
# - Publishes to PyPI
```

### View Security Reports
```bash
# Download latest security artifacts
gh run download --name security-reports

# View Bandit report
cat bandit-report.json | jq '.results'

# View Trivy findings
gh api repos/:owner/:repo/code-scanning/alerts
```

## Required Secrets

| Secret | Purpose | Scope |
|--------|---------|-------|
| `GITHUB_TOKEN` | Auto-provided | All workflows |
| `PYPI_API_TOKEN` | PyPI publishing | release.yml |

## Branch Protection Rules

Recommended settings for `main`:

```yaml
required_status_checks:
  strict: true
  contexts:
    - "CI Pipeline Success"
    - "Security Gate"
    - "Docker Build Gate"

required_pull_request_reviews:
  required_approving_review_count: 1

enforce_admins: true
```

## Monitoring

**Workflow Run History:** Actions tab
**Security Alerts:** Security → Code scanning
**Dependency Alerts:** Security → Dependabot
**Artifact Storage:** ~2GB for 90-day retention

## Troubleshooting

### Coverage Below 90%
```bash
# Local check
pytest --cov=src --cov-report=term-missing --cov-fail-under=90

# Identify uncovered lines
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Security Scan Failures
```bash
# Run Bandit locally
bandit -r src -ll

# Run Trivy locally
trivy fs .
```

### Docker Build Issues
```bash
# Test build locally
docker build -t test .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 .
```

## Performance

**Typical run times:**
- CI Pipeline: 8-12 minutes
- Security Scans: 5-7 minutes
- Docker Build: 10-15 minutes
- Release: 6-8 minutes
- Dependencies: 3-5 minutes

**Optimization:**
- Pip caching enabled
- Docker layer caching (GitHub Actions)
- Parallel job execution
- Fail-fast disabled for test matrix

## Maintenance

**Monthly:**
- Review outdated dependencies report
- Update workflow action versions
- Audit security findings

**Quarterly:**
- Review and update tool versions
- Benchmark workflow performance
- Update documentation

---

**Truth Protocol Verified:** All workflows pinned, tested, and production-ready.
**Last Updated:** 2025-11-01
**Compliance:** DevSkyy Enterprise Standards
