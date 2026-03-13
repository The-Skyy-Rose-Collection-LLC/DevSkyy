# Production Environment Setup Guide

## Overview

This guide covers the production environment setup for DevSkyy, including secret generation, validation, and deployment best practices.

## Quick Start

### 1. Generate Production Secrets

```bash
# Make scripts executable (if not already)
chmod +x scripts/generate_secrets.sh scripts/validate_environment.py

# Generate secrets
./scripts/generate_secrets.sh
```

This creates `.env.production` with:
- JWT secret (512-bit for HS512)
- Encryption master key (256-bit AES-GCM)
- Session secret (256-bit)
- Database password (32 chars)
- Redis password (32 chars)
- Internal API key (512-bit)

### 2. Add External API Keys

Edit `.env.production` and add:

**Required** (at least one LLM provider):
```bash
# Choose at least one:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...
```

**WordPress/WooCommerce** (if using e-commerce features):
```bash
WORDPRESS_URL=https://your-site.com
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...
```

**Optional** (for specific features):
```bash
# 3D Generation
TRIPO_API_KEY=...
FASHN_API_KEY=...

# Image Generation
STABILITY_API_KEY=...
REPLICATE_API_TOKEN=...

# Monitoring
SENTRY_DSN=...
DD_API_KEY=...
```

### 3. Update Connection Strings

Edit `.env.production` and update for your production infrastructure:

```bash
# PostgreSQL (update host, port, database name)
DATABASE_URL=postgresql+asyncpg://devskyy:GENERATED_PASSWORD@your-db-host:5432/devskyy_production

# Redis (update host, port)
REDIS_URL=redis://:GENERATED_PASSWORD@your-redis-host:6379/0
```

### 4. Validate Configuration

```bash
# Validate the environment file
python3 scripts/validate_environment.py .env.production
```

Expected output:
```
✅ VALIDATION PASSED
✓ Validated Variables (X):
   ✓ JWT_SECRET_KEY
   ✓ ENCRYPTION_MASTER_KEY
   ✓ DATABASE_URL
   ...
```

### 5. Secure the Secrets

**CRITICAL**: Never commit `.env.production` to version control!

```bash
# Verify it's in .gitignore
git check-ignore .env.production
# Should output: .env.production

# Store in secure vault
# Examples:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Google Cloud Secret Manager
# - Azure Key Vault
```

## Scripts Reference

### generate_secrets.sh

**Purpose**: Generate cryptographically secure secrets for production deployment.

**Location**: `scripts/generate_secrets.sh`

**Usage**:
```bash
./scripts/generate_secrets.sh
```

**What it does**:
1. Generates 6 cryptographically secure secrets using Python's `secrets` module
2. Creates `.env.production` with all required configuration sections
3. Sets file permissions to 600 (owner read/write only)
4. Provides checklist and next steps

**Generated Secrets**:
- `JWT_SECRET_KEY`: 512-bit (64 bytes) for HS512 JWT signing
- `ENCRYPTION_MASTER_KEY`: 256-bit (32 bytes) base64-encoded for AES-256-GCM
- `SESSION_SECRET`: 256-bit (32 bytes) for session management
- `DATABASE_PASSWORD`: 32-character alphanumeric password
- `REDIS_PASSWORD`: 32-character alphanumeric password
- `API_KEY`: 512-bit (64 bytes) for internal service authentication

**Output File**: `.env.production` with permissions `600`

**Security Features**:
- Uses cryptographically secure random number generator (CSPRNG)
- Meets industry standards for key lengths
- Automatic timestamp tracking
- Secure file permissions
- Comprehensive security warnings

### validate_environment.py

**Purpose**: Validate environment configuration before deployment.

**Location**: `scripts/validate_environment.py`

**Usage**:
```bash
# Validate default file (.env.production)
python3 scripts/validate_environment.py

# Validate specific file
python3 scripts/validate_environment.py .env.staging
```

**Exit Codes**:
- `0`: Validation passed (safe to deploy)
- `1`: Validation failed (fix errors before deploying)

**Validation Checks**:

1. **Security Secrets** (CRITICAL):
   - JWT_SECRET_KEY (min 64 chars)
   - ENCRYPTION_MASTER_KEY (min 32 chars)
   - SESSION_SECRET (min 32 chars)

2. **Database Configuration** (CRITICAL):
   - DATABASE_URL format validation
   - PostgreSQL scheme check
   - Host/port/database name presence
   - Localhost warning for production

3. **Redis Configuration** (CRITICAL):
   - REDIS_URL format validation
   - Redis scheme check
   - TLS recommendation for production
   - Localhost warning for production

4. **LLM Providers** (CRITICAL):
   - At least one provider required
   - Validates API key presence for all providers
   - Lists configured providers

5. **WordPress/WooCommerce** (WARNING):
   - URL format validation
   - HTTPS recommendation
   - Optional - warnings only

6. **Optional Features** (INFO):
   - 3D generation APIs
   - Image generation APIs
   - Monitoring services
   - Payment processors
   - Email/SMS services

7. **Security Settings** (WARNING):
   - DEBUG mode (must be false)
   - Environment setting
   - SSL/HTTPS configuration
   - Secure cookie settings

**Output Categories**:
- ❌ **ERRORS**: Must be fixed (validation fails)
- ⚠️ **WARNINGS**: Should be reviewed (validation passes)
- ✅ **VALIDATED**: Successfully validated variables
- ℹ️ **INFO**: Informational messages

**Example Output**:
```
🔍 DevSkyy Environment Validator
================================================================================
Validating: .env.production

Checking security secrets...
Checking database configuration...
Checking Redis configuration...
Checking LLM providers...
Checking WordPress configuration...
Checking optional features...
Checking security settings...

================================================================================
Validation Summary
================================================================================

✓ Validated Variables (15):
   ✓ JWT_SECRET_KEY
   ✓ ENCRYPTION_MASTER_KEY
   ✓ SESSION_SECRET
   ✓ DATABASE_URL
   ✓ REDIS_URL
   ✓ OPENAI_API_KEY
   ...

⚠️  WARNINGS (3):
   ! DATABASE_URL uses localhost - update for production deployment
   ! REDIS_URL uses localhost - update for production deployment
   ! 3D Generation features disabled: TRIPO_API_KEY, FASHN_API_KEY

ℹ️  Information:
   • JWT_SECRET_KEY: 86 characters (strong)
   • ENCRYPTION_MASTER_KEY: 44 characters (strong)
   • Session_SECRET: 64 characters (strong)
   • Database: postgresql+asyncpg://localhost:5432/devskyy_production
   • Redis: redis://localhost:6379/0
   • LLM Providers: OpenAI
   • Debug mode: disabled (correct for production)
   • Environment: production

================================================================================
✅ VALIDATION PASSED
⚠️  3 warning(s) - review recommended
================================================================================
```

## Environment File Structure

The generated `.env.production` includes these sections:

### 1. Security - Core Secrets
Essential cryptographic keys for application security.

### 2. Database Configuration
PostgreSQL connection and pool settings.

### 3. Redis Configuration
Redis connection for caching and sessions.

### 4. LLM Provider API Keys
API keys for AI model providers (at least one required).

### 5. 3D Asset Generation
Optional APIs for 3D model and virtual try-on features.

### 6. WordPress & WooCommerce
E-commerce integration credentials.

### 7. Image Generation & Processing
Optional APIs for image generation and enhancement.

### 8. Application Settings
Core application configuration.

### 9. Monitoring & Observability
Error tracking and APM integrations.

### 10. Cloud Provider Credentials
AWS, Google Cloud, Azure credentials.

### 11. Email & Notifications
Email and SMS service credentials.

### 12. Payment Processing
Payment gateway credentials.

### 13. Feature Flags
Enable/disable features.

### 14. Security Headers
HTTP security headers configuration.

### 15. Backup & Recovery
Backup automation settings.

## Deployment Workflow

### Development to Production Checklist

- [ ] **Generate Secrets**
  ```bash
  ./scripts/generate_secrets.sh
  ```

- [ ] **Add API Keys**
  - Edit `.env.production`
  - Add at least one LLM provider key
  - Add WordPress credentials (if using)
  - Add monitoring keys (recommended)

- [ ] **Update Connection Strings**
  - Replace `localhost` with production hosts
  - Update database name/credentials
  - Update Redis host/credentials
  - Enable TLS/SSL connections

- [ ] **Validate Configuration**
  ```bash
  python3 scripts/validate_environment.py .env.production
  ```
  - Fix all ERRORS
  - Review WARNINGS
  - Verify all required features are enabled

- [ ] **Store Secrets Securely**
  - Upload to secrets manager
  - Document access procedures
  - Set up rotation schedule
  - Configure access controls

- [ ] **Test Application**
  ```bash
  # Load production config (dry run)
  export $(grep -v '^#' .env.production | xargs)

  # Run application
  uvicorn main_enterprise:app --host 0.0.0.0 --port 8000

  # Test endpoints
  curl http://localhost:8000/health
  curl http://localhost:8000/api/v1/health/ready
  ```

- [ ] **Deploy**
  - Use secrets manager integration
  - Never copy `.env.production` to servers
  - Inject secrets at runtime
  - Monitor deployment logs

- [ ] **Verify Deployment**
  ```bash
  # Check health endpoints
  curl https://your-domain.com/health
  curl https://your-domain.com/api/v1/health/ready

  # Check metrics
  curl https://your-domain.com/metrics
  ```

- [ ] **Post-Deployment**
  - Monitor error rates
  - Check performance metrics
  - Verify integrations working
  - Review security logs
  - Set up alerts

## Security Best Practices

### Secret Management

1. **Never Commit Secrets**
   ```bash
   # Verify .env.production is ignored
   git check-ignore .env.production

   # If not, add to .gitignore
   echo ".env.production" >> .gitignore
   ```

2. **Use Secrets Manager**
   ```bash
   # AWS Secrets Manager example
   aws secretsmanager create-secret \
     --name devskyy/production/env \
     --secret-string file://.env.production

   # Google Cloud Secret Manager example
   gcloud secrets create devskyy-production-env \
     --data-file=.env.production
   ```

3. **Rotate Secrets Regularly**
   - Schedule: Every 90 days
   - Process:
     1. Generate new secrets
     2. Update secrets manager
     3. Deploy new configuration
     4. Verify application still works
     5. Revoke old secrets
     6. Document rotation

4. **Restrict Access**
   - Limit who can view secrets
   - Use IAM roles/policies
   - Enable audit logging
   - Monitor access patterns

### Environment Separation

Maintain separate configurations for each environment:

```
.env.development    # Local development
.env.staging        # Staging environment
.env.production     # Production environment
```

**Never**:
- Use production secrets in development
- Use development secrets in production
- Share secrets between environments
- Reuse database passwords across environments

### Connection Security

1. **Database**
   ```bash
   # Use SSL/TLS
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require

   # Use connection pooling
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=10
   ```

2. **Redis**
   ```bash
   # Use TLS
   REDIS_URL=rediss://:password@host:6380/0

   # Enable SSL certificate verification
   REDIS_SSL_CERT_REQS=required
   ```

3. **External APIs**
   - Store API keys in environment variables
   - Never hardcode in source code
   - Use minimum required permissions
   - Monitor API usage and costs

### Production Hardening

```bash
# Application Settings
DEBUG=false                      # Disable debug mode
ENVIRONMENT=production          # Set production environment

# Security Headers
SECURE_SSL_REDIRECT=true        # Force HTTPS
SESSION_COOKIE_SECURE=true      # Secure cookies
CSRF_COOKIE_SECURE=true         # Secure CSRF tokens
X_FRAME_OPTIONS=DENY            # Prevent clickjacking
CONTENT_SECURITY_POLICY=...     # CSP headers

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# Logging
LOG_LEVEL=INFO                  # Production log level
LOG_FORMAT=json                 # Structured logging
```

## Troubleshooting

### Validation Failures

**Error**: "Missing required variable: JWT_SECRET_KEY"
```bash
# Solution: Regenerate secrets
./scripts/generate_secrets.sh
```

**Error**: "DATABASE_URL: Invalid format"
```bash
# Solution: Check URL format
# Correct: postgresql+asyncpg://user:pass@host:5432/dbname
# Wrong: postgres://... (use postgresql+asyncpg)
```

**Error**: "No LLM provider API keys configured"
```bash
# Solution: Add at least one API key
export OPENAI_API_KEY=sk-...
# Or edit .env.production
```

**Warning**: "DATABASE_URL uses localhost"
```bash
# Solution: Update to production database host
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db.example.com:5432/devskyy
```

### Common Issues

1. **Permission Denied**
   ```bash
   # Make scripts executable
   chmod +x scripts/generate_secrets.sh
   chmod +x scripts/validate_environment.py
   ```

2. **Python Module Not Found**
   ```bash
   # Install required packages
   pip install python-dotenv
   ```

3. **Secrets Not Loading**
   ```bash
   # Verify file exists and has correct permissions
   ls -la .env.production

   # Should show: -rw------- (600)
   # If not: chmod 600 .env.production
   ```

4. **Database Connection Fails**
   ```bash
   # Test database connection
   psql "$DATABASE_URL"

   # Or using Python
   python3 -c "
   import asyncpg
   import asyncio
   async def test():
       conn = await asyncpg.connect('$DATABASE_URL')
       print('Connection successful!')
       await conn.close()
   asyncio.run(test())
   "
   ```

5. **Redis Connection Fails**
   ```bash
   # Test Redis connection
   redis-cli -u "$REDIS_URL" ping

   # Should output: PONG
   ```

## Monitoring and Maintenance

### Regular Tasks

**Daily**:
- Check application logs
- Monitor error rates
- Review failed authentication attempts

**Weekly**:
- Review API usage and costs
- Check database performance
- Verify backups are running

**Monthly**:
- Review security alerts
- Update dependencies
- Review access logs
- Test disaster recovery

**Quarterly** (Every 90 Days):
- Rotate all secrets
- Security audit
- Penetration testing
- Update documentation

### Metrics to Monitor

```bash
# Application Health
curl https://your-domain.com/metrics | grep http_requests_total
curl https://your-domain.com/metrics | grep agent_executions_total
curl https://your-domain.com/metrics | grep llm_tokens_total

# Database Performance
curl https://your-domain.com/metrics | grep db_connections
curl https://your-domain.com/metrics | grep db_query_duration

# Cache Performance
curl https://your-domain.com/metrics | grep redis_hits
curl https://your-domain.com/metrics | grep redis_misses
```

### Alerting Rules

Set up alerts for:
- Error rate > 1% over 5 minutes
- Response time > 1s (p95) over 5 minutes
- Failed authentication > 10/minute
- Database connections > 80% of pool
- Disk usage > 80%
- Memory usage > 85%
- API rate limit approaching (> 80%)

## References

- [DevSkyy CLAUDE.md](/Users/coreyfoster/DevSkyy/CLAUDE.md) - Main configuration guide
- [Security Documentation](/Users/coreyfoster/DevSkyy/docs/ZERO_TRUST_ARCHITECTURE.md)
- [API Documentation](/Users/coreyfoster/DevSkyy/docs/api/ECOMMERCE_API.md)
- [MCP Architecture](/Users/coreyfoster/DevSkyy/docs/MCP_ARCHITECTURE.md)

## Support

- **Security Issues**: security@skyyrose.com
- **General Support**: support@skyyrose.com
- **Documentation**: docs/

## Version History

- **1.0.0** (2026-01-05): Initial production environment setup guide
  - Added generate_secrets.sh
  - Added validate_environment.py
  - Comprehensive validation and security best practices
