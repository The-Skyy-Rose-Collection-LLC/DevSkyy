#!/usr/bin/env bash
#
# DevSkyy - Production Secret Generator
# ======================================
#
# Generates cryptographically secure secrets for production deployment.
# Creates .env.production with all required secrets and connection strings.
#
# Usage:
#   ./scripts/generate_secrets.sh
#
# Security:
#   - Uses Python's secrets module (CSPRNG)
#   - Sets file permissions to 600 (owner read/write only)
#   - Never commit .env.production to version control
#   - Rotate secrets every 90 days
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Output file
ENV_FILE=".env.production"

echo -e "${BLUE}🔐 DevSkyy Production Secret Generator${NC}"
echo -e "${BLUE}=======================================${NC}\n"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 is required but not found${NC}"
    exit 1
fi

# Generate secrets using Python's secrets module
echo -e "${YELLOW}⚙️  Generating cryptographically secure secrets...${NC}\n"

# JWT secret (64 bytes / 512 bits for HS512)
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# Encryption master key (32 bytes / 256 bits for AES-256-GCM, base64 encoded)
ENCRYPTION_KEY=$(python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")

# Session secret (32 bytes / 256 bits)
SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Database password (32 character alphanumeric)
DB_PASSWORD=$(python3 -c "import secrets, string; chars=string.ascii_letters+string.digits; print(''.join(secrets.choice(chars) for _ in range(32)))")

# Redis password (32 character alphanumeric)
REDIS_PASSWORD=$(python3 -c "import secrets, string; chars=string.ascii_letters+string.digits; print(''.join(secrets.choice(chars) for _ in range(32)))")

# API key for internal services (64 bytes)
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# Generate timestamp
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# Create .env.production file
cat > "$ENV_FILE" << EOF
# =============================================================================
# DevSkyy Production Environment Configuration
# =============================================================================
# Generated: $TIMESTAMP
#
# ⚠️  SECURITY WARNINGS:
#   - Never commit this file to version control
#   - Store in secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)
#   - Rotate secrets every 90 days
#   - Use different secrets for each environment
#   - If compromised, regenerate immediately
#
# 📋 DEPLOYMENT CHECKLIST:
#   [ ] Add external API keys (OpenAI, Anthropic, etc.)
#   [ ] Update DATABASE_URL host/port for production database
#   [ ] Update REDIS_URL host/port for production Redis
#   [ ] Configure WordPress/WooCommerce credentials
#   [ ] Set up monitoring and alerting
#   [ ] Enable SSL/TLS for all connections
#   [ ] Review and test all endpoints
# =============================================================================

# =============================================================================
# Security - Core Secrets
# =============================================================================
JWT_SECRET_KEY=$JWT_SECRET
ENCRYPTION_MASTER_KEY=$ENCRYPTION_KEY
SESSION_SECRET=$SESSION_SECRET
API_KEY=$API_KEY

# =============================================================================
# Database Configuration
# =============================================================================
# PostgreSQL connection string for production
# Update host, port, and database name as needed
DATABASE_URL=postgresql+asyncpg://devskyy:$DB_PASSWORD@localhost:5432/devskyy_production
DATABASE_PASSWORD=$DB_PASSWORD

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# =============================================================================
# Redis Configuration
# =============================================================================
# Redis connection for caching and session storage
# Update host and port for production Redis instance
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/0
REDIS_PASSWORD=$REDIS_PASSWORD

# Redis connection settings
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# =============================================================================
# LLM Provider API Keys
# =============================================================================
# ⚠️  Required: Add at least one LLM provider key
# Get keys from respective provider dashboards

# OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5)
# https://platform.openai.com/api-keys
OPENAI_API_KEY=

# Anthropic Claude (Claude 3.5 Sonnet, Opus)
# https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=

# Google AI (Gemini Pro, Gemini Ultra)
# https://makersuite.google.com/app/apikey
GOOGLE_AI_API_KEY=

# Mistral AI
# https://console.mistral.ai/api-keys
MISTRAL_API_KEY=

# Cohere
# https://dashboard.cohere.com/api-keys
COHERE_API_KEY=

# Groq
# https://console.groq.com/keys
GROQ_API_KEY=

# =============================================================================
# 3D Asset Generation
# =============================================================================
# Tripo3D - 3D model generation from text/images
# https://platform.tripo3d.ai/dashboard
TRIPO_API_KEY=
TRIPO_API_BASE_URL=https://api.tripo3d.ai/v2

# FASHN - Virtual try-on and clothing visualization
# https://fashn.ai/dashboard
FASHN_API_KEY=
FASHN_API_BASE_URL=https://api.fashn.ai/v1

# =============================================================================
# WordPress & WooCommerce
# =============================================================================
# WordPress site URL (production)
WORDPRESS_URL=https://skyyrose.com

# WooCommerce REST API credentials
# Generate from: WordPress Admin > WooCommerce > Settings > Advanced > REST API
WOOCOMMERCE_KEY=
WOOCOMMERCE_SECRET=

# WordPress admin credentials (for automated operations)
WORDPRESS_USERNAME=
WORDPRESS_PASSWORD=

# =============================================================================
# Image Generation & Processing
# =============================================================================
# Stability AI (Stable Diffusion)
# https://platform.stability.ai/account/keys
STABILITY_API_KEY=

# Replicate (model hosting)
# https://replicate.com/account/api-tokens
REPLICATE_API_TOKEN=

# =============================================================================
# Application Settings
# =============================================================================
# Environment
ENVIRONMENT=production

# Debug mode (MUST be false in production)
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS settings
CORS_ORIGINS=https://skyyrose.com,https://www.skyyrose.com
CORS_ALLOW_CREDENTIALS=true

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# =============================================================================
# Monitoring & Observability
# =============================================================================
# Sentry (error tracking)
# https://sentry.io/settings/account/api/auth-tokens/
SENTRY_DSN=

# DataDog (APM)
DD_API_KEY=
DD_APP_KEY=

# New Relic
NEW_RELIC_LICENSE_KEY=

# =============================================================================
# Cloud Provider Credentials
# =============================================================================
# AWS (if using S3, SES, etc.)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1

# Google Cloud (if using GCS, etc.)
GOOGLE_APPLICATION_CREDENTIALS=

# =============================================================================
# Email & Notifications
# =============================================================================
# SendGrid
SENDGRID_API_KEY=

# Twilio (SMS)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# =============================================================================
# Payment Processing
# =============================================================================
# Stripe
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# =============================================================================
# Feature Flags
# =============================================================================
ENABLE_3D_GENERATION=true
ENABLE_VIRTUAL_TRYON=true
ENABLE_ML_PREDICTIONS=true
ENABLE_AB_TESTING=true
ENABLE_CACHE=true
ENABLE_METRICS=true

# =============================================================================
# Security Headers
# =============================================================================
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
X_FRAME_OPTIONS=DENY
CONTENT_SECURITY_POLICY=default-src 'self'

# =============================================================================
# Backup & Recovery
# =============================================================================
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"

EOF

# Set restrictive permissions (owner read/write only)
chmod 600 "$ENV_FILE"

echo -e "${GREEN}✅ Secrets generated successfully!${NC}\n"

# Display summary
echo -e "${BLUE}📋 Summary:${NC}"
echo -e "   File: ${YELLOW}$ENV_FILE${NC}"
echo -e "   Permissions: ${YELLOW}600 (owner read/write only)${NC}"
echo -e "   Generated: ${YELLOW}$TIMESTAMP${NC}\n"

echo -e "${BLUE}🔑 Generated Secrets:${NC}"
echo -e "   ✓ JWT_SECRET_KEY (512-bit)"
echo -e "   ✓ ENCRYPTION_MASTER_KEY (256-bit AES-GCM)"
echo -e "   ✓ SESSION_SECRET (256-bit)"
echo -e "   ✓ DATABASE_PASSWORD (32 chars)"
echo -e "   ✓ REDIS_PASSWORD (32 chars)"
echo -e "   ✓ API_KEY (512-bit)\n"

echo -e "${YELLOW}⚠️  NEXT STEPS:${NC}"
echo -e "   1. Edit ${YELLOW}$ENV_FILE${NC} and add external API keys:"
echo -e "      - At least one LLM provider (OpenAI, Anthropic, or Google)"
echo -e "      - WordPress/WooCommerce credentials"
echo -e "      - Optional: 3D generation APIs (Tripo, FASHN)"
echo -e ""
echo -e "   2. Update database connection strings:"
echo -e "      - DATABASE_URL: Set correct host/port for production DB"
echo -e "      - REDIS_URL: Set correct host/port for production Redis"
echo -e ""
echo -e "   3. Validate configuration:"
echo -e "      ${BLUE}python3 scripts/validate_environment.py $ENV_FILE${NC}"
echo -e ""
echo -e "   4. Store secrets securely:"
echo -e "      - Use AWS Secrets Manager, HashiCorp Vault, or similar"
echo -e "      - Never commit $ENV_FILE to version control"
echo -e "      - Add to .gitignore if not already present"
echo -e ""
echo -e "   5. Deploy to production:"
echo -e "      - Export secrets to environment variables"
echo -e "      - Or use --env-file flag with Docker"
echo -e ""

echo -e "${RED}🚨 SECURITY REMINDERS:${NC}"
echo -e "   • Rotate secrets every 90 days"
echo -e "   • Use different secrets for dev/staging/production"
echo -e "   • Monitor for unauthorized access"
echo -e "   • Enable audit logging"
echo -e "   • Set up alerts for failed authentication"
echo -e "   • Review security policies regularly\n"

echo -e "${GREEN}✨ Generation complete!${NC}\n"
