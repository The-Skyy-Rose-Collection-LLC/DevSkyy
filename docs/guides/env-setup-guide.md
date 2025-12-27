# Environment Variables Setup Guide

This guide explains how to set up environment variables for the DevSkyy platform.

## Quick Start (TL;DR)

```bash
# 1. Create .env file (already done!)
# The .env file has been created with secure default values

# 2. Verify setup
cat .env | head -20

# 3. Install dependencies (if not already installed)
pip install -e .

# 4. Run the application
uvicorn main_enterprise:app --reload --port 8000
```

## What Has Been Set Up

✅ **`.env` file created** with:

- Secure JWT_SECRET_KEY (512-bit, auto-generated)
- Secure ENCRYPTION_MASTER_KEY (256-bit, auto-generated)
- Development defaults for database, CORS, logging
- Commented placeholders for optional services (AI APIs, WordPress, Redis, Email)

✅ **`scripts/generate_secrets.py`** - Helper script to regenerate secure keys

✅ **`.gitignore`** - Already configured to exclude `.env` files (keeps secrets safe)

## Environment Variables Reference

### Required Variables (Already Set)

| Variable | Purpose | Default Value |
|----------|---------|---------------|
| `JWT_SECRET_KEY` | JWT token signing | Auto-generated secure key |
| `ENCRYPTION_MASTER_KEY` | Data encryption (AES-256-GCM) | Auto-generated secure key |
| `ENVIRONMENT` | Runtime environment | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Optional Variables (Configure When Needed)

#### AI/ML APIs

```bash
# OpenAI GPT-4
OPENAI_API_KEY=sk-...

# Anthropic Claude Sonnet 4.5
ANTHROPIC_API_KEY=sk-ant-...

# Google AI
GOOGLE_AI_API_KEY=...
```

#### WordPress/WooCommerce Integration

```bash
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...
```

#### Database (Production)

```bash
# PostgreSQL (recommended for production)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/devskyy

# MySQL
# DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/devskyy
```

#### Caching

```bash
REDIS_URL=redis://localhost:6379/0
```

#### Email/SMTP

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## How to Use

### Method 1: Automatic Loading (Recommended)

The application automatically loads `.env` file on startup using `python-dotenv`:

```bash
uvicorn main_enterprise:app --reload
```

### Method 2: Manual Export (Linux/macOS)

```bash
# Export all variables at once
export $(grep -v '^#' .env | xargs)

# Or export individual variables
export JWT_SECRET_KEY="your-key-here"
export ENCRYPTION_MASTER_KEY="your-key-here"
```

### Method 3: Docker

```bash
# Use --env-file flag
docker run --env-file .env devSkyy

# Or in docker-compose.yml
services:
  app:
    env_file:
      - .env
```

## Security Best Practices

### ⚠️ Critical Security Rules

1. **Never commit `.env` to version control**
   - ✅ Already in `.gitignore`
   - ✅ Check with: `git status` (should not show `.env`)

2. **Use different keys per environment**

   ```bash
   # Development
   cp .env .env.development

   # Staging
   cp .env .env.staging
   python scripts/generate_secrets.py --env-file .env.staging

   # Production
   cp .env .env.production
   python scripts/generate_secrets.py --env-file .env.production
   ```

3. **Store production secrets in a vault**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Google Cloud Secret Manager

4. **Rotate keys regularly**

   ```bash
   # Regenerate keys every 90 days
   python scripts/generate_secrets.py
   ```

5. **Monitor for leaked secrets**
   - Use tools like `trufflehog` or `git-secrets`
   - Enable GitHub secret scanning
   - Review `.env` files in code reviews

## Regenerating Secure Keys

If you need to regenerate the secure keys (e.g., for production, key rotation, or after a compromise):

```bash
# Generate new keys and update .env
python scripts/generate_secrets.py

# Just show new keys without updating
python scripts/generate_secrets.py --show-only

# Update a different env file
python scripts/generate_secrets.py --env-file .env.production
```

## Verifying Setup

### Check that .env file exists

```bash
ls -la .env
```

### Verify critical variables are set

```bash
grep -E "JWT_SECRET_KEY|ENCRYPTION_MASTER_KEY" .env
```

### Test application startup

```bash
# Should start without warnings about missing keys
uvicorn main_enterprise:app --reload --port 8000
```

Expected output:

```
INFO:     🚀 DevSkyy Enterprise Platform starting...
INFO:     Environment: development
INFO:     Application startup complete.
```

## Troubleshooting

### Issue: Application warns about missing JWT_SECRET_KEY

**Solution:**

```bash
# Verify .env file exists
ls -la .env

# Check if key is set
grep JWT_SECRET_KEY .env

# Regenerate if needed
python scripts/generate_secrets.py
```

### Issue: .env not being loaded

**Solution:**

```bash
# Ensure python-dotenv is installed
pip install python-dotenv

# Or reinstall all dependencies
pip install -e .
```

### Issue: Different key needed for production

**Solution:**

```bash
# Create production-specific .env
cp .env .env.production

# Generate new production keys
python scripts/generate_secrets.py --env-file .env.production

# Use in production
uvicorn main_enterprise:app --env-file .env.production
```

## Environment-Specific Configuration

### Development

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite+aiosqlite:///./devskyy.db
```

### Staging

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://user:password@staging-db:5432/devskyy
REDIS_URL=redis://staging-redis:6379/0
```

### Production

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://user:password@prod-db:5432/devskyy
REDIS_URL=redis://prod-redis:6379/0
SENTRY_DSN=https://...@sentry.io/...
```

## Additional Resources

- **Main README**: `/README.md`
- **Security Documentation**: `/security/README.md`
- **Deployment Guide**: `/DEPLOYMENT_GUIDE.md`
- **Scripts Documentation**: `/scripts/README.md`

## Need Help?

- Check application logs: `tail -f logs/devskyy.log`
- Review security configuration: `cat security/jwt_oauth2_auth.py`
- Contact support: <support@skyyrose.com>
