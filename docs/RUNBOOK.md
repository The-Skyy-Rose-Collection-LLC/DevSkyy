# DevSkyy Production Deployment Runbook

**Version**: 3.2.0
**Last Updated**: 2026-02-22
**Status**: Production Ready
**Source of Truth**: `package.json`, `.env.example`

This runbook provides copy/paste ready instructions for deploying DevSkyy to production, including WordPress.com deployment, health checks, and incident response procedures.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Backend Deployment (Render)](#backend-deployment-render)
3. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
4. [WordPress.com Deployment](#wordpresscom-deployment)
5. [HuggingFace Spaces Deployment](#huggingface-spaces-deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Health Checks](#health-checks)
8. [Rollback Procedures](#rollback-procedures)
9. [Incident Response](#incident-response)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Security Keys Generated

```bash
# Generate JWT secret (64+ chars)
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"

# Generate encryption key (32 bytes, base64)
python -c "import secrets, base64; print('ENCRYPTION_MASTER_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())"
```

### Environment Verification

- [ ] All secrets in `ENV_VARS_REFERENCE.md` are configured
- [ ] Database is provisioned and accessible
- [ ] Redis cache is provisioned (optional but recommended)
- [ ] At least one LLM provider API key is valid
- [ ] DNS records point to correct endpoints

### Quality Gates

```bash
# Run locally before deploying
make ci

# Or individual checks:
# Python
isort . && ruff check --fix . && black .
mypy . --ignore-missing-imports
pytest -v --cov

# JavaScript (from package.json scripts)
npm run precommit    # Runs: lint + type-check + test:ci
# Or individually:
npm run lint:fix     # eslint src/**/*.{ts,tsx,js,jsx} --fix
npm run type-check   # tsc --project config/typescript/tsconfig.json --noEmit
npm run test:ci      # jest --ci --coverage --watchAll=false

# Security
npm run security:audit  # npm audit
```

---

## Backend Deployment (Render)

### Option A: Via Render Dashboard

1. **Create Web Service**
   - Go to https://dashboard.render.com
   - Click "New" > "Web Service"
   - Connect GitHub repository
   - Configure:
     ```
     Name: devskyy-api
     Region: US East (Ohio)
     Branch: main
     Root Directory: (leave empty)
     Runtime: Python 3
     Build Command: pip install -e .
     Start Command: uvicorn main_enterprise:app --host 0.0.0.0 --port $PORT
     ```

2. **Add Environment Variables**
   - Go to "Environment" tab
   - Add all variables from `ENV_VARS_REFERENCE.md` Backend section

3. **Configure Database**
   - Create PostgreSQL database
   - Copy connection string to `DATABASE_URL`

4. **Deploy**
   - Click "Manual Deploy" > "Deploy latest commit"

### Option B: Via render.yaml (Infrastructure as Code)

Create `render.yaml` in repository root:

```yaml
services:
  - type: web
    name: devskyy-api
    runtime: python
    repo: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy
    region: ohio
    plan: starter
    buildCommand: pip install -e .
    startCommand: uvicorn main_enterprise:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: JWT_SECRET_KEY
        sync: false
      - key: ENCRYPTION_MASTER_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: devskyy-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: devskyy-redis
          property: connectionString
      - key: CORS_ORIGINS
        value: https://app.devskyy.app,https://skyyrose.com
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false

databases:
  - name: devskyy-db
    databaseName: devskyy
    user: devskyy
    region: ohio
    plan: starter
    postgresMajorVersion: 15

caches:
  - name: devskyy-redis
    plan: starter
    region: ohio
```

Then run:
```bash
# Via Render CLI
render deploy

# Or via Render Dashboard
# Go to Blueprints > New Blueprint Instance > Connect repo
```

### Option C: Via Deploy Hook (CI/CD)

```bash
# Get deploy hook from Render Dashboard > Service > Settings > Deploy Hook
export RENDER_DEPLOY_HOOK="https://api.render.com/deploy/srv-xxx?key=xxx"

# Trigger deployment
curl -X POST "$RENDER_DEPLOY_HOOK"
```

### Verify Backend Deployment

```bash
# Health check
curl https://api.devskyy.app/health

# Expected response:
# {"status": "healthy", "version": "3.2.0", "timestamp": "..."}

# API docs
open https://api.devskyy.app/docs
```

---

## Frontend Deployment (Vercel)

### Option A: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy to production
cd frontend
vercel --prod

# Or deploy preview
vercel
```

### Option B: Via Vercel Dashboard

1. **Import Project**
   - Go to https://vercel.com/new
   - Import Git Repository
   - Select repository
   - Configure:
     ```
     Framework Preset: Next.js
     Root Directory: frontend
     Build Command: npm run build
     Output Directory: .next
     ```

2. **Add Environment Variables**
   - Go to Project Settings > Environment Variables
   - Add:
     ```
     NEXT_PUBLIC_API_URL=https://api.devskyy.app
     ```

3. **Deploy**
   - Click "Deploy"

### Option C: Via GitHub Actions (Automatic)

Already configured in `.github/workflows/ci.yml`. Pushes to `main` automatically deploy to production.

Required secrets in GitHub:
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

### Verify Frontend Deployment

```bash
# Check deployment
curl -s -o /dev/null -w "%{http_code}" https://app.devskyy.app

# Expected: 200

# Open in browser
open https://app.devskyy.app
```

---

## WordPress.com Deployment

### Theme Packaging

1. **Navigate to Theme Directory**
   ```bash
   cd wordpress-theme/skyyrose-flagship
   ```

2. **Create Deployment Package**
   ```bash
   # Create timestamped ZIP with exclusions
   zip -r ../skyyrose-flagship-deploy-$(date +%Y%m%d-%H%M%S).zip . \
     -x "*.git*" \
     -x "*.DS_Store" \
     -x "node_modules/*" \
     -x "*.log" \
     -x ".serena/*" \
     -x "*.md"
   ```

   **Excluded Files:**
   - `.git*` - Git metadata
   - `.DS_Store` - macOS files
   - `node_modules/` - Node.js dependencies (not needed in production)
   - `*.log` - Log files
   - `.serena/*` - Serena memory files
   - `*.md` - Documentation files (optional, can include README.md)

3. **Verify Package**
   ```bash
   # List files in ZIP (verify exclusions)
   unzip -l ../skyyrose-flagship-deploy-*.zip | head -50

   # Check package size (should be <5MB)
   ls -lh ../skyyrose-flagship-deploy-*.zip
   ```

### Manual Upload to WordPress.com

1. **Open WordPress.com Theme Manager**
   ```bash
   open https://wordpress.com/themes/upload/skyyrose.co
   ```

2. **Upload Theme**
   - Click "Upload Theme"
   - Select ZIP file created in step 2
   - Click "Install Now"

3. **Activate Theme (CRITICAL)**
   - **IMPORTANT**: Select "Replace current with uploaded" (NOT "Activate as new theme")
   - This ensures the existing theme is updated, not duplicated
   - Click "Activate"

4. **Clear Cache (MANDATORY)**
   - Go to https://wordpress.com/hosting-config/skyyrose.co
   - Click "Clear Cache" button
   - Wait 60 seconds for cache propagation
   - Verify changes are live

### WP-CLI Deployment (Alternative)

```bash
# Install WP-CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
sudo mv wp-cli.phar /usr/local/bin/wp

# Upload theme via WP-CLI
wp theme install skyyrose-flagship-deploy.zip --activate --force

# Clear cache
wp cache flush
```

### WordPress Theme Security Audit Checklist

Before deploying theme, verify:

- [ ] **No hardcoded credentials** in theme files
- [ ] **CSP headers configured** for WordPress.com compatibility
  - `style-src 'unsafe-inline'` (required for inline styles)
  - `script-src https://cdn.jsdelivr.net https://cdn.babylonjs.com` (3D libraries)
  - `connect-src https://stats.wp.com` (WordPress.com stats)
- [ ] **All user inputs sanitized** (use `esc_html()`, `esc_attr()`, `wp_kses()`)
- [ ] **Nonces verified** for AJAX requests
- [ ] **File uploads validated** (file type, size)
- [ ] **SQL queries use prepared statements** (use `$wpdb->prepare()`)
- [ ] **XSS prevention** (escape all outputs)
- [ ] **CSRF protection** (use `wp_verify_nonce()`)

### Post-Deployment Theme Verification

```bash
# Create verification script
cat > /tmp/verify-theme-deployment.sh << 'EOF'
#!/bin/bash

echo "🌹 SkyyRose WordPress Theme Deployment Verification"
echo "=================================================="

SITE_URL="https://skyyrose.co"
NOCACHE="nocache=1"

# 1. Check site availability
echo "1. Checking site availability..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SITE_URL}?${NOCACHE}")
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Site is online (HTTP $HTTP_CODE)"
else
  echo "❌ Site returned HTTP $HTTP_CODE"
fi

# 2. Check CSP headers
echo "2. Checking Content Security Policy..."
CSP=$(curl -s -I "${SITE_URL}?${NOCACHE}" | grep -i "content-security-policy")
if echo "$CSP" | grep -q "style-src.*unsafe-inline"; then
  echo "✅ CSP allows inline styles"
else
  echo "⚠️  CSP might block inline styles"
fi

if echo "$CSP" | grep -q "cdn.jsdelivr.net"; then
  echo "✅ CSP allows Three.js CDN"
else
  echo "⚠️  CSP might block Three.js"
fi

if echo "$CSP" | grep -q "cdn.babylonjs.com"; then
  echo "✅ CSP allows Babylon.js CDN"
else
  echo "⚠️  CSP might block Babylon.js"
fi

# 3. Check theme stylesheet loads
echo "3. Checking theme stylesheet..."
STYLE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SITE_URL}/wp-content/themes/skyyrose-flagship/style.css?${NOCACHE}")
if [ "$STYLE_CODE" = "200" ]; then
  echo "✅ Theme stylesheet loads (HTTP $STYLE_CODE)"
else
  echo "❌ Theme stylesheet failed (HTTP $STYLE_CODE)"
fi

# 4. Check 3D library CDNs
echo "4. Checking 3D library CDNs..."
THREE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://cdn.jsdelivr.net/npm/three@0.182.0/build/three.module.js")
if [ "$THREE_CODE" = "200" ]; then
  echo "✅ Three.js CDN accessible (HTTP $THREE_CODE)"
else
  echo "❌ Three.js CDN failed (HTTP $THREE_CODE)"
fi

BABYLON_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://cdn.babylonjs.com/babylon.js")
if [ "$BABYLON_CODE" = "200" ]; then
  echo "✅ Babylon.js CDN accessible (HTTP $BABYLON_CODE)"
else
  echo "❌ Babylon.js CDN failed (HTTP $BABYLON_CODE)"
fi

# 5. Manual verification reminder
echo ""
echo "Manual Verification Steps:"
echo "1. Open ${SITE_URL} in browser"
echo "2. Open browser console (F12)"
echo "3. Count console errors (should be <10)"
echo "4. Test 3D model viewers on product pages"
echo "5. Verify mobile responsiveness"
echo ""
echo "Goal: Reduce console errors from 107+ to <10"
EOF

chmod +x /tmp/verify-theme-deployment.sh
/tmp/verify-theme-deployment.sh
```

### WordPress.com Rollback

1. **Via WordPress.com Dashboard**
   - Go to https://wordpress.com/themes/skyyrose.co
   - Find previous theme version in "Manage Themes"
   - Click "Activate" on previous version
   - Clear cache

2. **Via WP-CLI**
   ```bash
   # List available themes
   wp theme list

   # Activate previous version
   wp theme activate skyyrose-flagship-previous

   # Clear cache
   wp cache flush
   ```

---

## HuggingFace Spaces Deployment

### Prerequisites

```bash
# Install HuggingFace CLI
pip install huggingface_hub

# Login
huggingface-cli login
# Enter your token when prompted
```

### Deploy All Spaces

```bash
cd hf-spaces
chmod +x deploy-all-spaces.sh
./deploy-all-spaces.sh
```

### Deploy Individual Space

```bash
# Example: Deploy 3D Converter
cd hf-spaces/3d-converter

# Create/update space
huggingface-cli repo create skyyrose/3d-converter --type space -y || true

# Push code
git init
git remote add origin https://huggingface.co/spaces/skyyrose/3d-converter
git add .
git commit -m "Deploy 3D Converter"
git push -f origin main
```

### Configure Space Secrets

1. Go to https://huggingface.co/spaces/skyyrose/[space-name]/settings
2. Add secrets:
   - `HF_TOKEN` - Your HuggingFace token
   - Space-specific secrets (see `ENV_VARS_REFERENCE.md`)

### Verify Space Deployment

```bash
# Check space status
curl https://huggingface.co/api/spaces/skyyrose/3d-converter

# Open in browser
open https://huggingface.co/spaces/skyyrose/3d-converter
```

---

## Post-Deployment Verification

### Run Smoke Tests

```bash
# Run smoke test script
chmod +x scripts/smoke-test.sh
./scripts/smoke-test.sh
```

### Manual Verification Checklist

- [ ] Backend `/health` returns 200
- [ ] Backend `/docs` shows OpenAPI UI
- [ ] Frontend loads dashboard
- [ ] Frontend can connect to backend API
- [ ] WordPress site loads (https://skyyrose.co)
- [ ] WordPress REST API accessible
- [ ] WooCommerce products sync
- [ ] 3D model viewers load on product pages
- [ ] HuggingFace spaces are running
- [ ] 3D pipeline generates assets
- [ ] Authentication flow works

### Monitor Initial Traffic

```bash
# Check Render logs
render logs --service devskyy-api --tail

# Check Vercel deployment
vercel logs

# Check Prometheus metrics (if enabled)
curl https://api.devskyy.app/metrics
```

---

## Health Checks

### Backend Health Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Overall health | `{"status": "healthy", "version": "3.2.0"}` |
| `/health/ready` | Readiness probe | `{"ready": true}` |
| `/health/live` | Liveness probe | `{"alive": true}` |
| `/metrics` | Prometheus metrics | Metrics in Prometheus format |

**Test Health Endpoints:**
```bash
# Overall health
curl https://api.devskyy.app/health

# Readiness (database connection, services)
curl https://api.devskyy.app/health/ready

# Liveness (process running)
curl https://api.devskyy.app/health/live

# Metrics (Prometheus)
curl https://api.devskyy.app/metrics
```

### Frontend Health Checks

```bash
# Check frontend loads
curl -s -o /dev/null -w "%{http_code}" https://app.devskyy.app
# Expected: 200

# Check API connectivity from frontend
curl -s https://app.devskyy.app/api/health
# Should proxy to backend and return health status
```

### WordPress Health Checks

```bash
# Check WordPress site
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co
# Expected: 200

# Check WordPress REST API
curl https://skyyrose.co/wp-json/wp/v2/
# Expected: JSON with API routes

# Check WooCommerce REST API
curl -u "ck_xxx:cs_xxx" https://skyyrose.co/wp-json/wc/v3/products
# Expected: JSON with products

# Check theme is active
curl -s https://skyyrose.co | grep "skyyrose-flagship"
# Expected: Theme name in HTML
```

### Database Health Check

```bash
# PostgreSQL connection test
python << EOF
from sqlalchemy import create_engine
import os

try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
EOF
```

### Redis Health Check

```bash
# Redis ping
redis-cli ping
# Expected: PONG

# Redis connection from Python
python << EOF
import redis
import os

try:
    r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    r.ping()
    print("✅ Redis connection successful")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
EOF
```

### Health Check Script

```bash
#!/bin/bash
# Save as scripts/health-check.sh

echo "DevSkyy Health Check"
echo "===================="

# Backend
echo "Backend:"
curl -s https://api.devskyy.app/health | jq . || echo "❌ Backend unhealthy"

# Frontend
echo "Frontend:"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.devskyy.app)
if [ "$STATUS" = "200" ]; then
  echo "✅ Frontend healthy (HTTP $STATUS)"
else
  echo "❌ Frontend unhealthy (HTTP $STATUS)"
fi

# WordPress
echo "WordPress:"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co)
if [ "$STATUS" = "200" ]; then
  echo "✅ WordPress healthy (HTTP $STATUS)"
else
  echo "❌ WordPress unhealthy (HTTP $STATUS)"
fi

# Database
echo "Database:"
python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL')); engine.connect(); print('✅ Database healthy')" || echo "❌ Database unhealthy"

# Redis
echo "Redis:"
redis-cli ping > /dev/null && echo "✅ Redis healthy" || echo "❌ Redis unhealthy"
```

---

## Rollback Procedures

### Backend Rollback (Render)

```bash
# Via Dashboard
# Go to Render > Service > Deploys > Select previous deploy > Rollback

# Via CLI
render rollback --service devskyy-api
```

### Frontend Rollback (Vercel)

```bash
# Via CLI
vercel rollback

# Via Dashboard
# Go to Vercel > Project > Deployments > Select previous > Promote to Production
```

### WordPress Theme Rollback

1. **Via WordPress.com Dashboard**
   - Go to https://wordpress.com/themes/skyyrose.co
   - Find previous theme version
   - Click "Activate"
   - Clear cache

2. **Keep Previous Version**
   - Always keep previous theme ZIP file
   - Upload previous version if rollback needed

3. **Database Rollback (if needed)**
   - Restore from backup
   - Use hosting provider's backup tools

### Emergency Procedures

**Enable Maintenance Mode:**
```bash
curl -X POST https://api.devskyy.app/api/v1/admin/maintenance-mode \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": true}'
```

**Check Service Status:**
```bash
curl https://api.devskyy.app/health/ready
```

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Escalation |
|-------|-------------|--------------|------------|
| **P0 - Critical** | Complete outage, data loss | 15 minutes | Immediate |
| **P1 - High** | Major feature broken, security issue | 1 hour | 30 minutes |
| **P2 - Medium** | Feature degraded, workaround available | 4 hours | 2 hours |
| **P3 - Low** | Minor issue, cosmetic bug | 24 hours | 12 hours |

### Incident Response Protocol

**1. Identify & Assess (P0/P1: 0-15 min)**
```bash
# Check all services
scripts/health-check.sh

# Check logs
render logs --service devskyy-api --tail
vercel logs
tail -f /var/log/wordpress/error.log

# Check metrics
curl https://api.devskyy.app/metrics | grep error_total
```

**2. Communicate (P0/P1: Within 15 min)**
- Update status page
- Notify stakeholders
- Create incident ticket

**3. Mitigate (P0: 15-60 min)**
- Enable maintenance mode if needed
- Rollback if recent deployment caused issue
- Apply hotfix if identified

**4. Resolve**
- Fix root cause
- Deploy fix
- Verify resolution
- Monitor for 30 minutes

**5. Post-Mortem (Within 48 hours)**
- Document timeline
- Root cause analysis
- Action items to prevent recurrence

### On-Call Contacts

**Primary:**
- Platform Team: support@devskyy.com
- Phone: (Available in internal docs)

**Security Issues:**
- Email: security@devskyy.com
- PagerDuty: (Available in internal docs)

**Escalation:**
- Level 1: Team Lead
- Level 2: Engineering Manager
- Level 3: CTO

---

## Troubleshooting

### Backend Issues

**500 Internal Server Error**
```bash
# Check logs
render logs --service devskyy-api --tail

# Common causes:
# - Missing environment variables
# - Database connection failed
# - Invalid API keys

# Verify environment
curl https://api.devskyy.app/health
```

**Database Connection Failed**
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL | grep -E "postgresql\+asyncpg://.*@.*/"

# Test connection
python -c "from sqlalchemy import create_engine; import os; e = create_engine(os.getenv('DATABASE_URL')); e.connect()"
```

**CORS Errors**
```bash
# Verify CORS_ORIGINS includes requesting domain
echo $CORS_ORIGINS

# Should include: https://app.devskyy.app,https://skyyrose.co
```

### Frontend Issues

**Build Failed**
```bash
# Check build logs
vercel logs

# Common causes:
# - Missing dependencies
# - TypeScript errors
# - Environment variables not set

# Test locally
npm run build
```

**API Connection Failed**
```bash
# Verify API URL
echo $NEXT_PUBLIC_API_URL

# Test API from frontend container
curl $NEXT_PUBLIC_API_URL/health
```

### WordPress Issues

**REST API 401 Unauthorized**
```bash
# Verify application password
curl -u "admin:xxxx-xxxx-xxxx-xxxx" https://skyyrose.co/wp-json/wp/v2/users/me

# Check if Application Passwords are enabled
# WP Admin > Users > Application Passwords
```

**WooCommerce API Error**
```bash
# Verify API keys have correct permissions
# WooCommerce > Settings > Advanced > REST API

# Test API keys
curl -u "ck_xxx:cs_xxx" https://skyyrose.co/wp-json/wc/v3/products
```

**WordPress.com CSP Blocking 3D Models**
```bash
# Check CSP headers
curl -I https://skyyrose.co | grep -i content-security-policy

# Required CSP directives:
# - style-src 'unsafe-inline' (for inline styles)
# - script-src https://cdn.jsdelivr.net https://cdn.babylonjs.com
# - connect-src https://stats.wp.com

# Verify in theme security.php
grep -A 10 "Content-Security-Policy" wordpress-theme/skyyrose-flagship/inc/security.php
```

**Theme Activation Issues**
```bash
# Check PHP errors
tail -f /var/log/wordpress/debug.log

# Verify theme files
ls -la wordpress-theme/skyyrose-flagship/

# Check file permissions
chmod -R 755 wordpress-theme/skyyrose-flagship

# Verify theme header
head -20 wordpress-theme/skyyrose-flagship/style.css
```

**3D Models Not Loading**
```bash
# Check browser console for CSP errors
# Open: https://skyyrose.co (F12 for console)

# Verify CDN URLs are accessible
curl -I https://cdn.jsdelivr.net/npm/three@0.182.0/build/three.module.js
curl -I https://cdn.babylonjs.com/babylon.js

# Check CSP allows CDNs
curl -I https://skyyrose.co | grep -i content-security-policy | grep -o "cdn.jsdelivr.net\|cdn.babylonjs.com"

# Goal: <10 console errors (down from 107+)
```

### HuggingFace Issues

**Space Not Starting**
- Check space logs in HuggingFace dashboard
- Verify secrets are set
- Check hardware requirements (CPU vs GPU)

**GPU Space Sleeping**
- Spaces on free tier sleep after inactivity
- Upgrade to persistent hardware or add keep-alive pings

---

## Platform Support

**Render:**
- Support: https://render.com/support
- Docs: https://render.com/docs

**Vercel:**
- Support: https://vercel.com/support
- Docs: https://vercel.com/docs

**WordPress.com:**
- Support: https://wordpress.com/support
- Docs: https://wordpress.com/support/hosting/

**HuggingFace:**
- Support: https://huggingface.co/support
- Docs: https://huggingface.co/docs

---

**Document Owner**: DevSkyy Platform Team
**Next Review**: After each major deployment
**Last Updated**: 2026-02-22
