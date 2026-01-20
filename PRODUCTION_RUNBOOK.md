# DevSkyy Production Deployment Runbook

**Version**: 3.0.0
**Last Updated**: 2026-01-16
**Status**: Production Ready

This runbook provides copy/paste ready instructions for deploying DevSkyy to production.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Backend Deployment (Render)](#backend-deployment-render)
3. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
4. [WordPress Deployment](#wordpress-deployment)
5. [HuggingFace Spaces Deployment](#huggingface-spaces-deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)

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
- [ ] All secrets in `ENV_VARS_MANIFEST.md` are configured
- [ ] Database is provisioned and accessible
- [ ] Redis cache is provisioned (optional but recommended)
- [ ] At least one LLM provider API key is valid
- [ ] DNS records point to correct endpoints

### Quality Gates
```bash
# Run locally before deploying
make ci

# Or individual checks:
ruff check .                    # Lint
black --check .                 # Format
mypy . --ignore-missing-imports # Types
pytest tests/ -v                # Tests
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
   - Add all variables from `ENV_VARS_MANIFEST.md` Backend section

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
# {"status": "healthy", "version": "3.0.0", "timestamp": "..."}

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

## WordPress Deployment

### Theme Installation

1. **Package Theme**
   ```bash
   cd wordpress/skyyrose-immersive
   zip -r skyyrose-immersive.zip . -x "*.git*" -x "*.DS_Store"
   ```

2. **Upload Theme**
   - Go to WP Admin > Appearance > Themes > Add New > Upload Theme
   - Select `skyyrose-immersive.zip`
   - Click "Install Now"
   - Activate theme

3. **Configure Parent Theme**
   - Ensure Shoptimizer theme is installed
   - skyyrose-immersive is a child theme of Shoptimizer

### Plugin Installation

1. **Package Plugins**
   ```bash
   cd wordpress/plugins

   # Package devskyy-abilities
   zip -r devskyy-abilities.zip devskyy-abilities/

   # Package skyyrose-3d-experience
   zip -r skyyrose-3d-experience.zip skyyrose-3d-experience/
   ```

2. **Upload Plugins**
   - Go to WP Admin > Plugins > Add New > Upload Plugin
   - Upload each zip file
   - Activate plugins

### WooCommerce Configuration

1. **Generate API Keys**
   - WooCommerce > Settings > Advanced > REST API
   - Add Key:
     - Description: DevSkyy Integration
     - User: Admin
     - Permissions: Read/Write
   - Copy keys to backend environment

2. **Configure Webhooks** (Optional)
   - WooCommerce > Settings > Advanced > Webhooks
   - Add webhook for order updates:
     - Name: DevSkyy Order Sync
     - Status: Active
     - Topic: Order updated
     - Delivery URL: https://api.devskyy.app/api/v1/webhooks/woocommerce/order
     - Secret: (generate and store securely)

### Verify WordPress Deployment

```bash
# Check site
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.com

# Check REST API
curl https://skyyrose.com/wp-json/wp/v2/

# Check WooCommerce API
curl -u "ck_xxx:cs_xxx" https://skyyrose.com/wp-json/wc/v3/products
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
   - Space-specific secrets (see `ENV_VARS_MANIFEST.md`)

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
- [ ] WordPress site loads
- [ ] WordPress REST API accessible
- [ ] WooCommerce products sync
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

### WordPress Rollback

1. **Theme Rollback**
   - Keep previous theme version
   - Activate previous version in WP Admin

2. **Database Rollback**
   - Restore from backup
   - Use hosting provider's backup tools

### Emergency Procedures

```bash
# Disable all external services (set maintenance mode)
curl -X POST https://api.devskyy.app/api/v1/admin/maintenance-mode \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": true}'

# Check service status
curl https://api.devskyy.app/health/ready
```

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
```

**Database Connection Failed**
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL | grep -E "postgresql\+asyncpg://.*@.*/"

# Test connection
python -c "from sqlalchemy import create_engine; e = create_engine('$DATABASE_URL'); e.connect()"
```

**CORS Errors**
```bash
# Verify CORS_ORIGINS includes requesting domain
echo $CORS_ORIGINS

# Should include: https://app.devskyy.app,https://skyyrose.com
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
curl -u "admin:xxxx-xxxx-xxxx-xxxx" https://skyyrose.com/wp-json/wp/v2/users/me

# Check if Application Passwords are enabled in WP
```

**WooCommerce API Error**
```bash
# Verify API keys have correct permissions
# Check WooCommerce > Settings > Advanced > REST API
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

## Contacts

**On-Call Support**
- Primary: DevSkyy Platform Team
- Email: support@skyyrose.com
- GitHub Issues: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

**Security Issues**
- Email: security@skyyrose.com

**Platform Support**
- Render: https://render.com/support
- Vercel: https://vercel.com/support
- HuggingFace: https://huggingface.co/support

---

**Document Owner**: DevSkyy Platform Team
**Next Review**: After each major deployment
