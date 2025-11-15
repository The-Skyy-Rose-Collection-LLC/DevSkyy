# Requirements Lock File Strategy

## Overview

This project uses a **hybrid dependency management** strategy per Truth Protocol Rule #2:

- **`requirements.txt`**: Uses compatible releases (`~=`) and range constraints (`>=,<`)
- **`requirements.lock`**: Exact pins for reproducible deployments (generated on-demand)

## Version Strategy

### Compatible Releases (~=)

Most packages use compatible releases to automatically receive patch updates:

```
fastapi~=0.119.0     # Gets 0.119.1, 0.119.2, etc. but NOT 0.120.0
pydantic~=2.9.3      # Gets 2.9.4, 2.9.5, etc. but NOT 2.10.0
```

### Range Constraints (>=,<)

Security-critical packages use range constraints to allow minor and patch updates:

```
cryptography>=46.0.3,<47.0.0    # Gets 46.x updates
certifi>=2024.12.14,<2025.0.0   # Gets latest certificates
setuptools>=78.1.1,<79.0.0      # Security fixes
```

**Security-critical packages:**
- cryptography
- certifi
- setuptools
- requests
- paramiko
- PyJWT
- bcrypt
- argon2-cffi
- passlib
- itsdangerous
- werkzeug
- starlette

## Generating Lock Files

### When to Generate

Generate a lock file when:
1. Preparing for production deployment
2. After updating dependencies
3. For reproducible CI/CD builds
4. Before creating a release

### How to Generate

```bash
# Install pip-tools
pip install pip-tools

# Generate lock file
pip-compile requirements.txt --output-file requirements.lock

# Regenerate with updates
pip-compile --upgrade requirements.txt --output-file requirements.lock
```

### Using Lock Files

```bash
# Development (gets latest compatible versions)
pip install -r requirements.txt

# Production (exact versions for reproducibility)
pip install -r requirements.lock
```

## CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Install dependencies (development)
  run: pip install -r requirements.txt

# .github/workflows/deploy.yml
- name: Install dependencies (production)
  run: pip install -r requirements.lock
```

## Benefits

### Compatible Releases Strategy

✅ **Automatic security patches** - Get CVE fixes without manual updates
✅ **Reduced maintenance** - No need to update every patch version
✅ **Semver protection** - Won't break on minor/patch updates
✅ **Faster security response** - Critical fixes auto-applied

### Lock Files

✅ **Reproducible builds** - Same versions everywhere
✅ **Deployment confidence** - Test exact versions
✅ **Debugging easier** - Know exact dependency tree
✅ **Rollback safety** - Pin to known-good versions

## Maintenance Schedule

Per Truth Protocol Rule #2:

- **Daily**: Check Dependabot alerts
- **Weekly**: Run `pip-audit` security scan
- **Monthly**: Full dependency review, regenerate lock file
- **On CVE**: Update affected packages immediately

## Security Scanning

```bash
# Scan for vulnerabilities
pip-audit --desc

# Scan with lock file
pip-audit --requirement requirements.lock --desc

# Fail on HIGH/CRITICAL
pip-audit --strict --requirement requirements.txt
```

## Example Workflow

```bash
# 1. Developer updates dependency
vim requirements.txt  # Change fastapi~=0.119.0 to fastapi~=0.120.0

# 2. Test locally
pip install -r requirements.txt
pytest

# 3. Generate new lock file
pip-compile requirements.txt --output-file requirements.lock

# 4. Commit both files
git add requirements.txt requirements.lock
git commit -m "chore: update fastapi to 0.120.x"

# 5. CI tests with requirements.txt (gets latest compatible)
# 6. Production deploys with requirements.lock (exact versions)
```

## Notes

- Lock file not committed by default (generate as needed)
- Date-based versions (e.g., `openai-whisper==20240930`) use exact pins
- See `.claude/agents/dependency-manager.md` for full documentation
