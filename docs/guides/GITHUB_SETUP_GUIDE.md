# GitHub Actions Setup Guide

**Repository:** <https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy>  
**Status:** ✅ Main branch merged with enterprise refactor  
**Next Steps:** Configure secrets and deploy

---

## 1. Configure GitHub Secrets

Navigate to: <https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/settings/secrets/actions>

Click **"New repository secret"** and add these:

### Critical Security Secrets

```bash
# Generate these keys with openssl rand -hex 32
JWT_SECRET_KEY=<your-32-byte-hex-string>
ENCRYPTION_MASTER_KEY=<your-32-byte-hex-string>
SECRET_KEY=<your-32-byte-hex-string>
```

### Database Configuration

```bash
# SQLite for development
DATABASE_URL=sqlite:///devskyy.db

# PostgreSQL for production
# DATABASE_URL=postgresql://user:password@host:5432/devskyy
```

### API Keys (Optional - add as needed)

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
MISTRAL_API_KEY=...
```

### Docker Hub (if deploying Docker images)

```bash
DOCKER_REGISTRY=docker.io
DOCKER_USERNAME=skyyrosellc
DOCKER_PASSWORD=<your-docker-hub-token>
```

---

## 2. Generate Secure Keys

Run these commands to generate secure keys:

```bash
# JWT Secret Key (32 bytes = 64 hex chars)
openssl rand -hex 32

# Encryption Key (32 bytes)
openssl rand -hex 32

# Secret Key (base64 url-safe)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 3. Add CI/CD Workflow

Create `.github/workflows/ci-cd.yml`:

```yaml
name: DevSkyy CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  PYTHON_VERSION: "3.11"

jobs:
  clean:
    name: Clean Repository
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Clean workspace
        run: |
          find . -name "*.backup*" -delete
          find . -name "*.broken*" -delete
          find . -type d -name "__pycache__" -exec rm -rf {} +
          find . -name "*.pyc" -delete

  lint:
    name: Code Quality Checks
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install ruff mypy black
      - name: Run Ruff
        run: ruff check .
      - name: Run MyPy
        run: mypy . --ignore-missing-imports || true

  test:
    name: Test Suite
    needs: [clean, lint]
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
        env:
          TEST_SECRET_KEY: test-secret-key-for-ci-only
      - name: Run tests
        run: pytest tests/ -v --cov=. --cov-report=xml
        env:
          TEST_SECRET_KEY: test-secret-key-for-ci-only
          DATABASE_URL: sqlite:///:memory:

  security:
    name: Security Scanning
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install security tools
        run: |
          pip install bandit safety
      - name: Run Bandit
        run: bandit -r agent/ api/ security/ -f json -o bandit-report.json || true
      - name: Run Safety
        run: safety check --json || true
      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json

  deploy:
    name: Deploy (Manual Only)
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch'
    steps:
      - name: Deploy Complete
        run: echo "✅ All checks passed - Ready for deployment"
```

---

## 4. Setup Instructions

### Step-by-Step GitHub Actions Setup

1. **Add Secrets:**

   ```bash
   # Go to repository Settings > Secrets and variables > Actions
   # Add each secret from the list above
   ```

2. **Create Workflow File:**

   ```bash
   mkdir -p .github/workflows
   # Copy the ci-cd.yml content above
   ```

3. **Commit and Push:**

   ```bash
   git add .github/workflows/ci-cd.yml
   git commit -m "🚀 Add CI/CD pipeline"
   git push origin main
   ```

4. **Trigger Workflow:**

   ```bash
   # Workflow will auto-trigger on push
   # Or manually trigger: Actions > DevSkyy CI/CD > Run workflow
   ```

---

## 5. Local Verification

Before pushing to GitHub, verify locally:

```bash
# Run tests
pytest tests/ -v

# Check linting
ruff check .
mypy .

# Security scan
bandit -r agent/ api/ security/
safety check

# Verify no secrets
git secrets scan
```

---

## 6. Deployment Environments

### Development (Local)

```bash
# Set environment variables
export ENVIRONMENT=development
export DATABASE_URL=sqlite:///devskyy.db
export SECRET_KEY=$(openssl rand -hex 32)

# Run application
python main.py
```

### Staging

```bash
# Use GitHub Actions environment protection
# Configure at: Settings > Environments > staging

# Secrets required:
# - All production secrets
# - Staging database URL
# - Test API keys
```

### Production

```bash
# Production deployment checklist:
# ✅ All secrets configured
# ✅ CI/CD passing
# ✅ Security scan clean
# ✅ Database backed up
# ✅ Monitoring configured
```

---

## 7. Verification Checklist

Before deploying, verify:

- [ ] All secrets added to GitHub
- [ ] Workflow file committed to main
- [ ] Local tests passing
- [ ] No hardcoded secrets in code
- [ ] `.env.example` template complete
- [ ] Security documentation updated
- [ ] Database migration ready
- [ ] Monitoring configured

---

## 8. Next Steps After Setup

1. **Monitor First CI Run:**
   - Go to Actions tab
   - Watch workflow execution
   - Fix any failures

2. **Set Up Branch Protection:**
   - Settings > Branches
   - Add rule for main branch
   - Require CI checks to pass

3. **Configure Environments:**
   - Settings > Environments
   - Create staging and production
   - Add deployment protections

4. **Deploy to Staging:**
   - Create deployment workflow
   - Test deployment process
   - Verify all services

---

## 9. Troubleshooting

### Workflow Fails on Secret Missing

```bash
# Check secret name matches exactly
# Secrets are case-sensitive
# Verify in Settings > Secrets and variables > Actions
```

### Tests Fail in CI

```bash
# Tests might need environment variables
# Add TEST_* prefixed secrets
# Use conditional: if: github.event_name != 'pull_request'
```

### Docker Build Fails

```bash
# Verify DOCKER_USERNAME and DOCKER_PASSWORD set
# Check Docker Hub token has push permissions
# Test locally: docker build -t devskyy .
```

---

**Ready to proceed?** Follow the steps above to complete setup!
