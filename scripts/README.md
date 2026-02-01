# DevSkyy Scripts

Utility scripts for DevSkyy platform management.

## Available Scripts

### Production Environment Setup

#### `generate_secrets.sh` - Production Secret Generator (NEW)

Bash script that generates a complete production environment configuration with all required secrets.

**Usage:**

```bash
# Make executable (first time only)
chmod +x scripts/generate_secrets.sh

# Generate production secrets
./scripts/generate_secrets.sh
```

**Creates:** `.env.production` with 600 permissions containing:
- JWT secret (512-bit for HS512)
- Encryption master key (256-bit AES-GCM)
- Session secret (256-bit)
- Database password (32 chars)
- Redis password (32 chars)
- Internal API key (512-bit)
- All configuration sections with placeholders

**Next Steps:**
1. Edit `.env.production` and add external API keys
2. Update connection strings for production infrastructure
3. Validate with `validate_environment.py`

#### `validate_environment.py` - Environment Configuration Validator (NEW)

Comprehensive validation tool for environment configuration before deployment.

**Usage:**

```bash
# Make executable (first time only)
chmod +x scripts/validate_environment.py

# Validate production config (default)
python3 scripts/validate_environment.py

# Validate specific file
python3 scripts/validate_environment.py .env.staging
```

**Exit Codes:**
- `0` - Validation passed (safe to deploy)
- `1` - Validation failed (fix errors before deploying)

**Validates:**
- Security secrets (JWT, encryption, session) - CRITICAL
- Database configuration and format - CRITICAL
- Redis configuration and format - CRITICAL
- LLM provider API keys (at least one required) - CRITICAL
- WordPress/WooCommerce configuration - WARNING
- Optional feature APIs - INFO
- Security settings (DEBUG, SSL, etc.) - WARNING

**Output:**
- ❌ ERRORS: Must be fixed (validation fails)
- ⚠️ WARNINGS: Should be reviewed (validation passes)
- ✅ VALIDATED: Successfully validated variables
- ℹ️ INFO: Informational messages

**Documentation:** See [PRODUCTION_ENVIRONMENT_SETUP.md](../docs/PRODUCTION_ENVIRONMENT_SETUP.md) for complete guide.

---

### Development Environment Setup

#### `verify_env.py` - Development Environment Verification

Verifies that environment variables are properly configured before running the application.

**Usage:**

```bash
# Verify environment setup
python scripts/verify_env.py
```

**Checks:**

- ✅ Verifies `.env` file exists
- ✅ Confirms required variables are set (JWT_SECRET_KEY, ENCRYPTION_MASTER_KEY, ENVIRONMENT)
- ✅ Lists optional variables and their status
- ✅ Provides helpful error messages if configuration is incomplete

**Recommended:** Run this script before starting the application to ensure proper configuration.

#### `generate_secrets.py` - Development Secret Generator

Generates cryptographically secure keys for JWT authentication and AES-256-GCM encryption for development.

**Usage:**

```bash
# Generate and update .env file
python scripts/generate_secrets.py

# Show keys without updating .env
python scripts/generate_secrets.py --show-only

# Update custom .env file
python scripts/generate_secrets.py --env-file /path/to/.env
```

**Generated Keys:**

- `JWT_SECRET_KEY`: 512-bit key for HS512 JWT signing
- `ENCRYPTION_MASTER_KEY`: 256-bit key for AES-256-GCM encryption

**Security Best Practices:**

- ✅ Never commit `.env` file to version control (already in `.gitignore`)
- ✅ Use different keys for dev/staging/production environments
- ✅ Store production keys in secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)
- ✅ Rotate keys every 90 days
- ✅ Immediately regenerate if keys are compromised

**Note:** For production deployments, use `generate_secrets.sh` instead, which creates a complete production configuration.

## Quick Start

### For Development

1. **Initial setup:**

   ```bash
   # Create .env from template (if needed)
   cp .env.example .env

   # Generate secure keys
   python scripts/generate_secrets.py
   ```

2. **Verify setup:**

   ```bash
   # Verify all environment variables are configured
   python scripts/verify_env.py
   ```

3. **Run application:**

   ```bash
   uvicorn main_enterprise:app --reload
   ```

### For Production

1. **Generate production configuration:**

   ```bash
   # Make scripts executable
   chmod +x scripts/generate_secrets.sh scripts/validate_environment.py

   # Generate complete production configuration
   ./scripts/generate_secrets.sh
   ```

2. **Configure external services:**

   ```bash
   # Edit .env.production and add:
   # - At least one LLM provider API key (OpenAI/Anthropic/Google)
   # - Update DATABASE_URL host for production database
   # - Update REDIS_URL host for production Redis
   # - WordPress/WooCommerce credentials (if using)
   # - Optional: Monitoring, email, payment APIs
   nano .env.production
   ```

3. **Validate configuration:**

   ```bash
   # Validate all required variables are set
   python3 scripts/validate_environment.py .env.production
   ```

4. **Deploy:**

   ```bash
   # Store secrets in vault (AWS Secrets Manager, etc.)
   # Deploy application with production configuration
   # Never copy .env.production to servers directly
   ```

**See also:** [Production Environment Setup Guide](../docs/PRODUCTION_ENVIRONMENT_SETUP.md) for complete deployment workflow.

---

### Security & Maintenance

#### `fix_dependencies.sh` - Security Vulnerability Fix Script (NEW)

Automated script to resolve all GitHub Dependabot security vulnerabilities by fixing dependency conflicts and updating to secure versions.

**Usage:**

```bash
# Make executable (first time only)
chmod +x scripts/fix_dependencies.sh

# Run automated fix
./scripts/fix_dependencies.sh
```

**What it does:**
1. Uninstalls conflicting Python packages
2. Installs compatible versions with correct constraints
3. Reinstalls DevSkyy with all extras
4. Updates JavaScript dependencies via pnpm
5. Verifies all package versions

**Resolves:**
- HIGH SEVERITY: tar, next, python-multipart, bentoml, protobuf
- MEDIUM SEVERITY: hono, pypdf, lodash, lodash-es, and transitive dependencies

**Time:** 5-10 minutes

**Requirements:**
- Python 3.11+
- Node 18+
- pnpm installed (`npm install -g pnpm`)
- Virtual environment activated

**Documentation:**
- Complete technical details: `SECURITY_FIXES.md`
- Quick start guide: `EXECUTE_SECURITY_FIXES.md`
- Execution checklist: `SECURITY_FIX_CHECKLIST.md`
- Executive summary: `SECURITY_FIX_SUMMARY.md`

---

## Environment Variables

See `.env.example` for complete list of available environment variables.

**Required for production:**

- `JWT_SECRET_KEY` - JWT signing key (auto-generated by script)
- `ENCRYPTION_MASTER_KEY` - Data encryption key (auto-generated by script)

**Optional but recommended:**

- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis cache connection
- `ANTHROPIC_API_KEY` - Claude AI API key
- `OPENAI_API_KEY` - OpenAI GPT API key

## Security Notes

All scripts use Python's `secrets` module which provides cryptographically secure random number generation suitable for managing data such as passwords, account authentication, security tokens, and related secrets.

The generated keys are URL-safe base64 encoded strings that are:

- Suitable for use in environment variables
- Compatible with HTTP headers
- Safe for storage in configuration files
