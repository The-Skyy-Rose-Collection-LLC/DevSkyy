# DevSkyy CI/CD Workflows

Modern, clean GitHub Actions workflows for continuous integration and deployment.

## 📋 Workflows Overview

### 🔄 CI Pipeline (`ci.yml`)

**Trigger:** Push/PR to `main` or `develop` branches

**Jobs:**
- **Backend CI** - Python 3.11 & 3.12 testing
  - Dependency installation
  - Backend load verification
  - Code formatting (black, isort)
  - Linting (flake8)
  - Type checking (mypy)
  - Unit tests with coverage

- **Frontend CI** - Node.js 20 testing
  - NPM dependency installation
  - Linting
  - TypeScript compilation
  - Production build
  - Build artifact upload

- **Production Safety Check**
  - Runs comprehensive safety validation
  - Uploads safety report

- **Security Scan**
  - pip-audit for Python vulnerabilities
  - npm audit for frontend vulnerabilities
  - Trivy filesystem scanning
  - SARIF upload to GitHub Security

### 🐳 Docker Build (`docker.yml`)

**Trigger:** Push to `main`, tags, or manual

**Features:**
- Multi-platform builds (amd64, arm64)
- GitHub Container Registry (ghcr.io)
- Docker layer caching
- Trivy security scanning
- Automatic versioning from tags

**Image Tags:**
- `main` - Latest main branch
- `v1.2.3` - Semantic version tags
- `sha-abc123` - Git commit SHA

### 🚀 Deployment (`deploy.yml`)

**Trigger:** After successful CI, or manual dispatch

**Environments:**
- **Staging** - Automatic deployment after CI passes
- **Production** - Manual approval required

**Features:**
- Pre-deployment validation
- Post-deployment verification
- Deployment notifications

### 🔒 Security Scanning (`security-scan.yml`)

**Trigger:** Daily at midnight, or manual

**Scans:**
- Python dependencies (pip-audit, safety)
- Frontend dependencies (npm audit)
- Dependabot integration
- Automated security updates

### 🔍 CodeQL Analysis (`codeql.yml`)

**Trigger:** Push to `main`, PRs, weekly schedule

**Languages:** Python, JavaScript/TypeScript

**Features:**
- Advanced code scanning
- Security vulnerability detection
- Automated alerts

### 📦 Release Automation (`release.yml`)

**Trigger:** Version tags (`v*.*.*`)

**Actions:**
- Create GitHub release
- Generate release notes
- Upload release artifacts

### 🧹 Stale Issues (`stale.yml`)

**Trigger:** Daily

**Features:**
- Mark stale issues (60 days)
- Close stale issues (7 days)
- Configurable labels

## 🎯 Usage

### Running Workflows Manually

All workflows support manual triggering:

```bash
# Via GitHub CLI
gh workflow run ci.yml

# Via GitHub UI
Actions → Select workflow → Run workflow
```

### Local Testing

```bash
# Backend checks
python3 -c "from main import app; print('✅ OK')"
black --check --line-length 120 .
flake8 --max-line-length=120
mypy agent/ backend/
pytest tests/

# Frontend checks
cd frontend
npm run lint
npm run build

# Security scans
pip-audit
cd frontend && npm audit
```

### Docker Build Locally

```bash
# Build image
docker build -t devskyy:local .

# Run container
docker run -p 8000:8000 --env-file .env devskyy:local
```

## 🔧 Configuration

### Required Secrets

None required for basic CI/CD. Optional:

- `DOCKER_USERNAME` - Docker Hub username (if using Docker Hub)
- `DOCKER_PASSWORD` - Docker Hub token
- Deployment secrets (staging/production)

### Environment Protection

**Staging:**
- No approval required
- Auto-deploys on CI success

**Production:**
- Manual approval required
- Protected branch rules
- Deployment notifications

## 📊 Workflow Status

| Workflow | Status | Description |
|----------|--------|-------------|
| CI Pipeline | ![CI](../../actions/workflows/ci.yml/badge.svg) | Main CI/CD pipeline |
| Docker Build | ![Docker](../../actions/workflows/docker.yml/badge.svg) | Container builds |
| CodeQL | ![CodeQL](../../actions/workflows/codeql.yml/badge.svg) | Security analysis |
| Security Scan | ![Security](../../actions/workflows/security-scan.yml/badge.svg) | Dependency scanning |

## 🚨 Troubleshooting

### CI Failures

**Backend fails to load:**
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Verify dependencies
pip install -r requirements.txt
```

**Frontend build fails:**
```bash
# Check Node version
node --version  # Should be 20+

# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Docker Build Issues

**Build timeout:**
- Increase timeout in workflow
- Use Docker layer caching
- Optimize Dockerfile

**Image size too large:**
- Use multi-stage builds
- Remove unnecessary dependencies
- Use `.dockerignore`

## 📝 Best Practices

1. **Always run tests locally before pushing**
2. **Use feature branches for development**
3. **Squash commits for cleaner history**
4. **Tag releases with semantic versions**
5. **Monitor security alerts daily**
6. **Review failed workflows promptly**

## 🔄 Workflow Diagram

```
Push to main/develop
    ↓
CI Pipeline (ci.yml)
    ├─ Backend Tests
    ├─ Frontend Build
    ├─ Safety Check
    └─ Security Scan
    ↓
Docker Build (docker.yml)
    ├─ Build Image
    ├─ Push to Registry
    └─ Security Scan
    ↓
Deploy (deploy.yml)
    ├─ Staging (auto)
    └─ Production (manual)
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python Testing Best Practices](https://docs.pytest.org/en/stable/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

---

**Last Updated:** 2025-10-12
**Maintained By:** DevSkyy Team
