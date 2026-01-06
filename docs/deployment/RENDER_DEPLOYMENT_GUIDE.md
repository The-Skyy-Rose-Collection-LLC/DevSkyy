# DevSkyy Backend - Render Deployment Guide

**Version:** 1.0.0
**Last Updated:** 2026-01-06
**Target Platform:** Render.com
**Status:** Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Environment Variables Configuration](#environment-variables-configuration)
6. [Database & Redis Setup](#database--redis-setup)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Custom Domain Setup](#custom-domain-setup)
9. [Monitoring & Logging](#monitoring--logging)
10. [Troubleshooting](#troubleshooting)
11. [Production Maintenance](#production-maintenance)

---

## Overview

This guide provides comprehensive instructions for deploying the DevSkyy backend to Render's cloud platform. The deployment includes:

- **Web Service**: FastAPI application (main_enterprise.py)
- **PostgreSQL Database**: Render Postgres Standard plan
- **Redis Instance**: Render Redis Standard plan
- **Auto-deploy**: Connected to GitHub main branch
- **Health Checks**: Automatic monitoring at `/health` endpoint

**Architecture:**
```
GitHub (main) → Render Build → Web Service (Uvicorn)
                                    ↓
                          PostgreSQL + Redis
                                    ↓
                          Custom Domain (api.skyyrose.com)
```

---

## Prerequisites

### Required Accounts

- [ ] **GitHub Account**: Repository access to [The-Skyy-Rose-Collection-LLC/DevSkyy](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy)
- [ ] **Render Account**: Sign up at [render.com](https://render.com) (Free to start)
- [ ] **Domain Access**: DNS configuration for api.skyyrose.com (optional)

### Required API Keys

You MUST have at least ONE of the following LLM provider API keys:

- [ ] **OpenAI API Key**: Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] **Anthropic API Key**: Get from [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
- [ ] **Google AI API Key**: Get from [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

Optional but recommended:

- [ ] **Tripo3D API Key**: For 3D generation - [platform.tripo3d.ai](https://platform.tripo3d.ai)
- [ ] **FASHN API Key**: For virtual try-on - [fashn.ai](https://fashn.ai)
- [ ] **WooCommerce Credentials**: For e-commerce integration

### Local Environment

- [ ] **Git**: Version 2.x+
- [ ] **Python 3.11+**: For local testing (optional)
- [ ] **curl or HTTPie**: For API testing

---

## Pre-Deployment Checklist

### 1. Verify Repository Configuration

```bash
# Clone the repository (if not already done)
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy

# Ensure you're on the main branch
git checkout main
git pull origin main

# Verify render.yaml exists
ls -la render.yaml

# Verify requirements.txt is up to date
cat requirements.txt | head -20
```

### 2. Review Environment Variables

Check that `.env.production` has placeholder values (we'll set real values in Render):

```bash
# Review the production environment template
cat .env.production | grep -E "REPLACE|CHANGE|GENERATE"
```

**IMPORTANT**: Never commit real API keys to `.env.production`. This file is a template only.

### 3. Verify Application Entry Point

Confirm the application starts correctly:

```bash
# Test locally (optional)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from main_enterprise import app; print('✓ App imports successfully')"
```

---

## Step-by-Step Deployment

### Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Click "Get Started" or "Sign Up"
3. Sign up with GitHub (recommended for easy repo integration)
4. Authorize Render to access your GitHub account
5. Select "The-Skyy-Rose-Collection-LLC" organization when prompted

### Step 2: Create PostgreSQL Database

1. From Render Dashboard, click **"New +"** → **"PostgreSQL"**

2. Configure database:
   ```
   Name:              devskyy-postgres
   Database:          devskyy_production
   User:              devskyy
   Region:            Oregon (us-west-2) - Match web service region
   PostgreSQL Version: 16 (latest stable)
   Plan:              Standard ($7/month) - Production recommended
   ```

3. Click **"Create Database"**

4. Wait for provisioning (2-3 minutes)

5. **CRITICAL**: Copy the connection strings:
   - **Internal Database URL**: `postgresql://devskyy:***@***-postgres/devskyy_production`
   - **External Database URL**: `postgresql://devskyy:***@***-postgres.render.com/devskyy_production`

   > **Note**: Use the **Internal Database URL** for the web service (faster, no external network)

6. Store credentials securely (password manager or secrets vault)

### Step 3: Create Redis Instance

1. From Render Dashboard, click **"New +"** → **"Redis"**

2. Configure Redis:
   ```
   Name:              devskyy-redis
   Region:            Oregon (us-west-2) - Match database region
   Plan:              Standard ($7/month) - Production recommended
   Max Memory Policy: allkeys-lru (evict least recently used)
   ```

3. Click **"Create Redis"**

4. Wait for provisioning (1-2 minutes)

5. **CRITICAL**: Copy the Redis connection string:
   - **Internal Redis URL**: `redis://red-***:6379`

6. Store credentials securely

### Step 4: Create Web Service from Blueprint

#### Option A: Using render.yaml (Recommended)

1. From Render Dashboard, click **"New +"** → **"Blueprint"**

2. Connect repository:
   - Select **"The-Skyy-Rose-Collection-LLC/DevSkyy"**
   - Branch: **main**
   - Render will auto-detect `render.yaml`

3. Review the blueprint configuration:
   ```yaml
   Service Name: devskyy-api
   Runtime:      Python
   Region:       Oregon
   Plan:         Free (upgrade later)
   Branch:       main
   Build:        pip install -r requirements.txt
   Start:        uvicorn main_enterprise:app --host 0.0.0.0 --port $PORT
   Health:       /health
   Auto-deploy:  Enabled
   ```

4. Click **"Apply"** to create the service

5. Render will start the first build (this takes 5-10 minutes)

#### Option B: Manual Web Service Creation

If blueprint doesn't work:

1. From Render Dashboard, click **"New +"** → **"Web Service"**

2. Connect repository:
   - Select **"The-Skyy-Rose-Collection-LLC/DevSkyy"**
   - Branch: **main**

3. Configure service:
   ```
   Name:          devskyy-api
   Region:        Oregon (us-west-2)
   Branch:        main
   Runtime:       Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main_enterprise:app --host 0.0.0.0 --port $PORT
   Plan:          Free (upgrade to Starter $7/month for production)
   ```

4. Add environment variable:
   ```
   PYTHON_VERSION = 3.11.11
   ```

5. Click **"Create Web Service"**

### Step 5: Configure Environment Variables

This is the MOST CRITICAL step. Each variable must be set correctly.

1. Go to your web service → **"Environment"** tab

2. Click **"Add Environment Variable"**

3. Add the following variables one by one:

#### Core Security (REQUIRED)

```bash
# Generate these with the provided script (see below)
JWT_SECRET_KEY=<generated-by-render>
ENCRYPTION_MASTER_KEY=<generated-by-render>
```

**Note**: Render auto-generates these if you used the blueprint. Otherwise, generate with:

```bash
# On your local machine
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
python -c "import secrets, base64; print('ENCRYPTION_MASTER_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())"
```

#### Database & Redis (REQUIRED)

```bash
# Use the Internal URLs from Steps 2 and 3
DATABASE_URL=postgresql://devskyy:<password>@<internal-host>/devskyy_production
REDIS_URL=redis://red-<id>:6379
```

**Example** (replace with your actual values):
```bash
DATABASE_URL=postgresql://devskyy:kX9mP2nQ@dpg-abc123-a/devskyy_production
REDIS_URL=redis://red-xyz789:6379
```

#### Application Settings (REQUIRED)

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://devskyy-dashboard.vercel.app,https://skyyrose.com,https://api.skyyrose.com
```

#### LLM Provider (REQUIRED - At least ONE)

```bash
# Add at least one of these
OPENAI_API_KEY=sk-proj-***
ANTHROPIC_API_KEY=sk-ant-***
GOOGLE_AI_API_KEY=AI***
```

#### Optional 3D/Visual Generation

```bash
TRIPO_API_KEY=***
FASHN_API_KEY=***
HUGGINGFACE_ACCESS_TOKEN=hf_***
```

#### WordPress/WooCommerce (Optional)

```bash
WORDPRESS_URL=https://skyyrose.com
WOOCOMMERCE_KEY=ck_***
WOOCOMMERCE_SECRET=cs_***
```

#### Performance & Monitoring (Recommended)

```bash
# Database connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis settings
REDIS_MAX_CONNECTIONS=50

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Features
ENABLE_3D_GENERATION=true
ENABLE_METRICS=true
ENABLE_CACHE=true
```

### Step 6: Trigger Deployment

1. After adding all environment variables, click **"Save Changes"**

2. Render will automatically redeploy with the new environment

3. Monitor the build logs:
   - Go to **"Logs"** tab
   - Watch for successful deployment
   - Look for: `Application startup complete`

4. Build should complete in 5-10 minutes

### Step 7: Initial Health Check

Once the service is live (status shows "Live" in green):

```bash
# Replace with your Render service URL
curl https://devskyy-api.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2026-01-06T12:00:00.000Z",
  "version": "1.0.0",
  "environment": "production"
}
```

---

## Environment Variables Configuration

### Complete Variable Reference

Here's the complete set of environment variables organized by category:

#### 🔒 Security (REQUIRED)

| Variable | Description | Example/Format | Required |
|----------|-------------|----------------|----------|
| `JWT_SECRET_KEY` | JWT signing secret (512-bit) | Auto-generated by Render | ✅ |
| `ENCRYPTION_MASTER_KEY` | AES-256-GCM key (base64) | Auto-generated by Render | ✅ |
| `SECRET_KEY` | General app secret | `secrets.token_urlsafe(64)` | ✅ |

#### 💾 Database & Cache (REQUIRED)

| Variable | Description | Example/Format | Required |
|----------|-------------|----------------|----------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` | ✅ |
| `REDIS_URL` | Redis connection | `redis://host:6379/0` | ✅ |
| `DB_POOL_SIZE` | Connection pool size | `20` | Recommended |
| `DB_MAX_OVERFLOW` | Pool overflow limit | `10` | Recommended |

#### 🤖 LLM Providers (At least ONE required)

| Variable | Description | Provider | Required |
|----------|-------------|----------|----------|
| `OPENAI_API_KEY` | OpenAI API key | OpenAI | One of |
| `ANTHROPIC_API_KEY` | Anthropic API key | Anthropic | these |
| `GOOGLE_AI_API_KEY` | Google AI key | Google | required |
| `MISTRAL_API_KEY` | Mistral API key | Mistral | Optional |
| `COHERE_API_KEY` | Cohere API key | Cohere | Optional |
| `GROQ_API_KEY` | Groq API key | Groq | Optional |

#### 🎨 3D & Visual Generation (Optional)

| Variable | Description | Provider | Required |
|----------|-------------|----------|----------|
| `TRIPO_API_KEY` | 3D generation | Tripo3D | Optional |
| `FASHN_API_KEY` | Virtual try-on | FASHN | Optional |
| `HUGGINGFACE_ACCESS_TOKEN` | Model access | HuggingFace | Optional |

#### 🛒 E-Commerce (Optional)

| Variable | Description | Format | Required |
|----------|-------------|--------|----------|
| `WORDPRESS_URL` | WordPress site URL | `https://skyyrose.com` | Optional |
| `WOOCOMMERCE_KEY` | WooCommerce consumer key | `ck_***` | Optional |
| `WOOCOMMERCE_SECRET` | WooCommerce secret | `cs_***` | Optional |

#### ⚙️ Application Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment name | `production` | ✅ |
| `DEBUG` | Debug mode | `false` | ✅ |
| `LOG_LEVEL` | Logging level | `INFO` | ✅ |
| `CORS_ORIGINS` | Allowed origins | Comma-separated URLs | ✅ |
| `PYTHON_VERSION` | Python version | `3.11.11` | ✅ |

### Using the Secret Generation Script

For local testing or to generate example secrets:

```bash
# Run the secret generator
cd /Users/coreyfoster/DevSkyy
./scripts/generate_secrets.sh

# This creates .env.production with secure secrets
# DO NOT commit this file to Git
# Use it as a reference for Render environment variables
```

---

## Database & Redis Setup

### Database Migrations

After the first deployment, run migrations:

```bash
# Option 1: Using Render Shell (if available on your plan)
# Go to Web Service → Shell tab
python -c "from db import init_db; init_db()"

# Option 2: Using a one-off job (Render Standard plan)
# Create a one-off job with:
# Command: python -c "from db import init_db; init_db()"
```

### Database Connection Pooling

Render's free tier has connection limits. Configure pooling:

```bash
# Add to environment variables
DB_POOL_SIZE=5          # Free tier: use 5, Standard: use 20
DB_MAX_OVERFLOW=2       # Free tier: use 2, Standard: use 10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600    # Recycle connections every hour
```

### Redis Configuration

```bash
# Redis is configured automatically
# But you can tune these settings:
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

---

## Post-Deployment Verification

### 1. Health Check

```bash
# Basic health check
curl https://devskyy-api.onrender.com/health

# Expected: 200 OK
{
  "status": "healthy",
  "timestamp": "2026-01-06T...",
  "version": "1.0.0",
  "environment": "production"
}
```

### 2. Database Connectivity

```bash
# Check database health
curl https://devskyy-api.onrender.com/health/ready

# Expected: 200 OK
{
  "status": "ready",
  "database": "connected",
  "redis": "connected"
}
```

### 3. API Documentation

```bash
# Access interactive API docs
open https://devskyy-api.onrender.com/docs

# Should show FastAPI Swagger UI with all endpoints
```

### 4. Test Agent Endpoint

```bash
# List available agents
curl https://devskyy-api.onrender.com/api/v1/agents

# Expected: Array of agent objects
[
  {
    "id": "commerce",
    "name": "Commerce Agent",
    "description": "E-commerce operations",
    "status": "active"
  },
  ...
]
```

### 5. Test LLM Integration

```bash
# Test Round Table endpoint (requires LLM API key)
curl -X POST https://devskyy-api.onrender.com/api/v1/round-table/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is 2+2?",
    "providers": ["openai"]
  }'

# Expected: LLM response
{
  "result": "4",
  "provider": "openai",
  "model": "gpt-4",
  "tokens": {...}
}
```

### 6. Monitor Logs

```bash
# In Render Dashboard:
# 1. Go to your web service
# 2. Click "Logs" tab
# 3. Look for:
#    - "Application startup complete"
#    - No error traces
#    - Successful health checks
```

### 7. Performance Check

```bash
# Check response time
time curl -w "@-" -o /dev/null -s https://devskyy-api.onrender.com/health

# Expected: < 500ms for Oregon region
# Free tier: May have cold start delays (10-30s)
# Paid tier: Instant responses
```

---

## Custom Domain Setup

### Option 1: api.skyyrose.com (Subdomain)

1. **In Render Dashboard:**
   - Go to your web service
   - Click **"Settings"** → **"Custom Domains"**
   - Click **"Add Custom Domain"**
   - Enter: `api.skyyrose.com`
   - Click **"Save"**

2. **Get CNAME Target:**
   - Render will show: `devskyy-api.onrender.com`
   - Copy this value

3. **In Your DNS Provider (Cloudflare, Route53, etc.):**
   ```
   Type:  CNAME
   Name:  api
   Value: devskyy-api.onrender.com
   TTL:   Auto or 3600
   ```

4. **Wait for DNS Propagation:**
   ```bash
   # Check DNS propagation (may take 5-60 minutes)
   dig api.skyyrose.com

   # Or use online tool:
   # https://www.whatsmydns.net/#CNAME/api.skyyrose.com
   ```

5. **Enable SSL (Automatic):**
   - Render automatically provisions Let's Encrypt SSL
   - Wait 2-5 minutes after DNS propagates
   - Certificate renews automatically every 90 days

6. **Verify HTTPS:**
   ```bash
   curl https://api.skyyrose.com/health
   ```

### Option 2: Custom Apex Domain (skyyrose.com)

For apex domain, use ALIAS or ANAME record (not available with all DNS providers):

1. **Check if your DNS provider supports ALIAS/ANAME:**
   - Cloudflare: ✅ (Use CNAME flattening)
   - Route53: ✅ (Use ALIAS)
   - Namecheap: ❌ (Use subdomain instead)

2. **Add ALIAS record:**
   ```
   Type:  ALIAS
   Name:  @
   Value: devskyy-api.onrender.com
   ```

### Update CORS Origins

After setting up custom domain:

```bash
# Update environment variable in Render
CORS_ORIGINS=https://api.skyyrose.com,https://skyyrose.com,https://devskyy-dashboard.vercel.app
```

---

## Monitoring & Logging

### Built-in Render Monitoring

1. **Metrics Dashboard:**
   - Go to Web Service → **"Metrics"** tab
   - View: CPU, Memory, Request rate, Response time
   - Alerts: Configure in **"Settings"** → **"Notifications"**

2. **Log Streaming:**
   - Go to Web Service → **"Logs"** tab
   - Real-time log stream
   - Filter by level: INFO, WARNING, ERROR

3. **Health Checks:**
   - Automatic checks every 30s at `/health`
   - Auto-restart on failure (3 consecutive fails)

### Application Metrics

The DevSkyy backend exposes Prometheus metrics:

```bash
# Access metrics endpoint
curl https://api.skyyrose.com/metrics

# Returns Prometheus format:
# http_requests_total{method="GET",path="/health"} 1234
# agent_executions_total{agent="commerce",status="success"} 567
```

### External Monitoring (Optional)

#### Sentry (Error Tracking)

```bash
# Add to environment variables
SENTRY_DSN=https://***@sentry.io/***
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

#### Datadog APM

```bash
# Add to environment variables
DD_API_KEY=***
DD_APP_KEY=***
DD_SERVICE=devskyy-api
DD_ENV=production
```

#### UptimeRobot (Uptime Monitoring)

1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Create monitor:
   ```
   Type:     HTTPS
   URL:      https://api.skyyrose.com/health
   Interval: 5 minutes
   Alert:    Email/SMS on downtime
   ```

### Log Aggregation

For production, consider log aggregation:

- **Papertrail**: Built-in Render integration
- **Logtail**: Better.Stack log management
- **CloudWatch**: If using AWS services

---

## Troubleshooting

### Common Issues & Solutions

#### 1. Build Fails

**Symptom**: Build fails with "No module named 'X'"

**Solution**:
```bash
# Check requirements.txt includes the module
grep -i "module-name" requirements.txt

# If missing, add it and push:
echo "module-name>=version" >> requirements.txt
git add requirements.txt
git commit -m "fix: add missing dependency"
git push origin main
```

#### 2. Application Won't Start

**Symptom**: Build succeeds but app crashes on start

**Solution**:
```bash
# Check logs for the error
# Common causes:

# Missing environment variable
# Fix: Add in Render Environment tab

# Database connection failed
# Fix: Verify DATABASE_URL is correct (use Internal URL)

# Port binding error
# Fix: Ensure start command uses $PORT variable
# uvicorn main_enterprise:app --host 0.0.0.0 --port $PORT
```

#### 3. 502 Bad Gateway

**Symptom**: Intermittent 502 errors

**Solution**:
```bash
# Free tier: Cold start issue
# Fix: Upgrade to Starter plan ($7/month) for zero downtime

# Or: Use a cron job to keep service warm
# Add a cron service in render.yaml:
# schedule: "*/5 * * * *"  # Every 5 minutes
# command: curl https://devskyy-api.onrender.com/health
```

#### 4. Database Connection Pool Exhausted

**Symptom**: "Too many connections" errors

**Solution**:
```bash
# Reduce pool size for free tier
DB_POOL_SIZE=3
DB_MAX_OVERFLOW=1

# Or upgrade to Standard database plan (25 connections)
```

#### 5. Slow Response Times

**Symptom**: Requests take > 5 seconds

**Solution**:
```bash
# 1. Enable Redis caching
ENABLE_CACHE=true
REDIS_URL=redis://...

# 2. Increase worker count (Starter plan+)
# In render.yaml or start command:
uvicorn main_enterprise:app --workers 2

# 3. Use Render's CDN for static assets
# Add in render.yaml:
# headers:
#   - path: /static/*
#     name: Cache-Control
#     value: public, max-age=31536000
```

#### 6. Environment Variable Not Loading

**Symptom**: Code shows "env var not set"

**Solution**:
```bash
# 1. Verify variable is set in Render
# Dashboard → Environment → Check variable exists

# 2. Restart service after adding variables
# Click "Manual Deploy" → "Clear build cache & deploy"

# 3. Check for typos in variable names
# Variable names are case-sensitive
```

#### 7. LLM API Calls Failing

**Symptom**: "Invalid API key" or "Rate limit exceeded"

**Solution**:
```bash
# 1. Verify API key is correct
# Test locally first:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 2. Check API quota/billing
# Each provider has different limits

# 3. Add retry logic in code (already implemented)
# LLM_MAX_RETRIES=3
# LLM_TIMEOUT=30
```

---

## Production Maintenance

### Regular Tasks

#### Daily
- [ ] Check error logs for exceptions
- [ ] Monitor response times (< 500ms)
- [ ] Verify health check status

#### Weekly
- [ ] Review metrics dashboard
- [ ] Check database disk usage
- [ ] Update dependencies with security patches

#### Monthly
- [ ] Rotate API keys (if policy requires)
- [ ] Review and optimize database queries
- [ ] Update Python runtime if new version available
- [ ] Test backup restoration

#### Quarterly
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Rotate JWT secrets
- [ ] Update SSL certificates (auto-renewed, just verify)

### Backup Strategy

#### Database Backups

Render provides automatic daily backups (Standard plan):

```bash
# Backups are retained for 30 days
# To restore:
# 1. Go to PostgreSQL service → Backups tab
# 2. Select backup date
# 3. Click "Restore"
```

Manual backup:

```bash
# Export database
render db:dump devskyy-postgres > backup.sql

# Import to new database
render db:restore devskyy-postgres < backup.sql
```

#### Environment Variable Backup

```bash
# Export all environment variables
# In Render Dashboard → Environment → Export button
# Save to secure location (password manager)
```

### Scaling Strategy

#### Vertical Scaling (Upgrade Plan)

1. **Free → Starter ($7/month)**
   - No cold starts
   - Zero downtime deploys
   - Better performance

2. **Starter → Standard ($25/month)**
   - More CPU/RAM
   - Multiple workers
   - Priority support

3. **Standard → Pro ($85/month)**
   - Dedicated resources
   - Custom metrics
   - SLA guarantees

#### Horizontal Scaling (Multiple Instances)

```bash
# In render.yaml, set:
numInstances: 2  # Run 2 instances with load balancing

# Or in Dashboard:
# Settings → Scaling → Horizontal → Set instance count
```

### Security Maintenance

#### Dependency Updates

```bash
# Check for outdated packages
pip list --outdated

# Update requirements.txt
pip-compile --upgrade

# Test locally, then deploy
git commit -am "chore: update dependencies"
git push origin main
```

#### Security Scanning

```bash
# Run security audit locally
pip-audit

# Check for known vulnerabilities
safety check

# Render also scans for CVEs automatically
```

---

## Deployment Checklist

Use this checklist for each deployment:

### Pre-Deployment

- [ ] All tests passing locally
- [ ] Dependencies updated in requirements.txt
- [ ] Environment variables documented
- [ ] Database migrations prepared
- [ ] API documentation updated
- [ ] CHANGELOG.md updated
- [ ] Git tag created for release

### Deployment

- [ ] Create database backup
- [ ] Deploy to Render
- [ ] Monitor build logs
- [ ] Verify health checks pass
- [ ] Run smoke tests
- [ ] Check error logs

### Post-Deployment

- [ ] Verify all endpoints working
- [ ] Test critical user flows
- [ ] Check performance metrics
- [ ] Monitor error rates
- [ ] Update status page
- [ ] Notify team of deployment

### Rollback Plan

If deployment fails:

```bash
# 1. In Render Dashboard → Deploys tab
# 2. Find last successful deploy
# 3. Click "Redeploy"
# 4. Service will rollback to previous version
```

---

## Cost Estimate

### Minimal Production Setup (Recommended)

| Service | Plan | Cost/Month |
|---------|------|------------|
| Web Service | Starter | $7 |
| PostgreSQL | Standard | $7 |
| Redis | Standard | $7 |
| **Total** | | **$21/month** |

### Free Tier (Testing Only)

| Service | Plan | Cost/Month | Limitations |
|---------|------|------------|-------------|
| Web Service | Free | $0 | Cold starts, 750h/month |
| PostgreSQL | Free | $0 | 90 days, then $7 |
| Redis | Free | $0 | 90 days, then $7 |
| **Total** | | **$0** | Not for production use |

### Enterprise Setup

| Service | Plan | Cost/Month |
|---------|------|------------|
| Web Service | Standard (2 instances) | $50 |
| PostgreSQL | Pro | $50 |
| Redis | Pro | $25 |
| Custom Domain | Included | $0 |
| SSL Certificate | Included | $0 |
| **Total** | | **$125/month** |

---

## Support & Resources

### Render Documentation

- [Render Docs](https://render.com/docs)
- [Deploy from GitHub](https://render.com/docs/deploy-from-github)
- [Environment Variables](https://render.com/docs/environment-variables)
- [PostgreSQL](https://render.com/docs/databases)
- [Redis](https://render.com/docs/redis)

### DevSkyy Resources

- [GitHub Repository](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy)
- [API Documentation](https://api.skyyrose.com/docs)
- [Architecture Guide](/docs/architecture/DEVSKYY_MASTER_PLAN.md)
- [Security Guide](/docs/ZERO_TRUST_ARCHITECTURE.md)

### Getting Help

- **Technical Issues**: Open GitHub issue
- **Render Support**: support@render.com (Pro plan+ gets priority)
- **DevSkyy Team**: support@skyyrose.com

---

## Next Steps

After successful deployment:

1. **Set Up Monitoring**
   - Configure UptimeRobot
   - Add Sentry for error tracking
   - Set up Slack/email alerts

2. **Frontend Integration**
   - Update frontend `BACKEND_URL` to point to `https://api.skyyrose.com`
   - Test all API integrations
   - Deploy frontend to Vercel

3. **Domain Configuration**
   - Set up custom domain
   - Configure SSL
   - Update CORS settings

4. **Performance Optimization**
   - Enable Redis caching
   - Configure CDN for static assets
   - Optimize database queries

5. **Security Hardening**
   - Enable rate limiting
   - Configure WAF (Cloudflare)
   - Set up audit logging

6. **Documentation**
   - Create API changelog
   - Document deployment process
   - Create runbooks for common operations

---

**Last Updated**: 2026-01-06
**Version**: 1.0.0
**Maintained By**: DevSkyy Team
**Status**: Production Ready ✅
