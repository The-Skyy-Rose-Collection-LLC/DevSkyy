# DevSkyy - Production Environment Setup Instructions

## Quick Setup (Run These Commands)

### 1. Make Scripts Executable

```bash
chmod +x /Users/coreyfoster/DevSkyy/scripts/generate_secrets.sh
chmod +x /Users/coreyfoster/DevSkyy/scripts/validate_environment.py
```

### 2. Generate Production Secrets

```bash
cd /Users/coreyfoster/DevSkyy
./scripts/generate_secrets.sh
```

This creates `.env.production` with:
- JWT_SECRET_KEY (512-bit)
- ENCRYPTION_MASTER_KEY (256-bit AES-GCM)
- SESSION_SECRET (256-bit)
- DATABASE_PASSWORD (32 chars)
- REDIS_PASSWORD (32 chars)
- API_KEY (512-bit)

### 3. Configure External APIs

Edit `.env.production` and add:

```bash
# Required: At least one LLM provider
OPENAI_API_KEY=sk-...           # OR
ANTHROPIC_API_KEY=sk-ant-...    # OR
GOOGLE_AI_API_KEY=...

# Update for production infrastructure
DATABASE_URL=postgresql+asyncpg://devskyy:GENERATED_PASSWORD@your-db-host:5432/devskyy_production
REDIS_URL=redis://:GENERATED_PASSWORD@your-redis-host:6379/0

# Optional: E-commerce
WORDPRESS_URL=https://skyyrose.com
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...

# Optional: 3D generation
TRIPO_API_KEY=...
FASHN_API_KEY=...
```

### 4. Validate Configuration

```bash
python3 scripts/validate_environment.py .env.production
```

Expected output:
```
✅ VALIDATION PASSED
```

If you see errors, fix them before deploying.

### 5. Secure the Secrets

```bash
# Verify .env.production is NOT committed
git status

# If it shows up (it shouldn't):
echo ".env.production" >> .gitignore

# Store in secrets manager (AWS example)
aws secretsmanager create-secret \
  --name devskyy/production/env \
  --secret-string file://.env.production
```

## What Was Created

### Scripts

1. **`scripts/generate_secrets.sh`** (11KB)
   - Generates cryptographically secure secrets
   - Creates complete `.env.production` template
   - Sets file permissions to 600
   - Provides deployment checklist

2. **`scripts/validate_environment.py`** (15KB)
   - Validates all required environment variables
   - Checks secret strength and format
   - Validates database/Redis URLs
   - Ensures at least one LLM provider configured
   - Exit code 0 = safe to deploy, 1 = fix errors

3. **`tests/test_environment_scripts.py`** (7KB)
   - Test suite for both scripts
   - Verifies secret generation
   - Validates configuration checks
   - Ensures security requirements met

### Documentation

1. **`docs/PRODUCTION_ENVIRONMENT_SETUP.md`** (24KB)
   - Complete production deployment guide
   - Security best practices
   - Troubleshooting guide
   - Monitoring and maintenance checklist

2. **`scripts/README.md`** (Updated)
   - Script usage documentation
   - Quick start guide
   - Differentiation between dev/production workflows

## File Permissions

Current state:
```
-rw------- scripts/generate_secrets.sh        (needs chmod +x)
-rw------- scripts/validate_environment.py    (needs chmod +x)
```

After running chmod commands:
```
-rwx------ scripts/generate_secrets.sh        (executable)
-rwx------ scripts/validate_environment.py    (executable)
```

## Security Checklist

- [ ] Scripts made executable
- [ ] Production secrets generated
- [ ] External API keys added to `.env.production`
- [ ] Connection strings updated for production hosts
- [ ] Configuration validated (no errors)
- [ ] `.env.production` NOT committed to git
- [ ] Secrets stored in secure vault
- [ ] File permissions verified (600 for .env.production)
- [ ] Different secrets for dev/staging/production
- [ ] Secret rotation schedule documented (every 90 days)

## Testing

Run the test suite to verify everything works:

```bash
# Install pytest if needed
pip install pytest

# Run environment script tests
pytest tests/test_environment_scripts.py -v

# Expected: All tests pass
```

## Deployment Workflow

```mermaid
graph TD
    A[Run generate_secrets.sh] --> B[Edit .env.production]
    B --> C[Add API keys]
    B --> D[Update connection strings]
    C --> E[Run validate_environment.py]
    D --> E
    E --> F{Validation Passed?}
    F -->|No| G[Fix errors]
    G --> E
    F -->|Yes| H[Store in vault]
    H --> I[Deploy to production]
    I --> J[Verify health endpoints]
```

## Next Steps

1. Run the chmod commands above
2. Generate production secrets
3. Add your API keys
4. Validate configuration
5. Review [PRODUCTION_ENVIRONMENT_SETUP.md](docs/PRODUCTION_ENVIRONMENT_SETUP.md)
6. Deploy!

## Support

- **Documentation**: `/Users/coreyfoster/DevSkyy/docs/PRODUCTION_ENVIRONMENT_SETUP.md`
- **Security Issues**: security@skyyrose.com
- **General Support**: support@skyyrose.com

---

**Status**: Ready for production deployment
**Version**: 1.0.0
**Date**: 2026-01-05
