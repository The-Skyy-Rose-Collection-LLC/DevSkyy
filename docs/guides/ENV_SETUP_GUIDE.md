# Environment Variables Setup Guide

## Quick Start

### 1. Copy the Template

```bash
cd /Users/coreyfoster/DevSkyy
cp .env.template .env
```

### 2. Edit Your .env File

```bash
# Use any text editor
nano .env
# or
code .env
# or
vim .env
```

### 3. Fill in Required Values

**Minimum required for basic functionality:**
```env
SECRET_KEY=generate-random-string-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Where to Find API Keys

### 🔑 Required Keys

#### 1. SECRET_KEY
**What:** Encryption key for sessions and tokens
**How to generate:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
**Example:** `xK7jP9mN2qR5vL8wT3yZ6bC4nF1dG0hS`

#### 2. ANTHROPIC_API_KEY (REQUIRED)
**What:** Powers Claude Sonnet 4.5 - needed for theme builder, product descriptions, all ML features
**Where to get:**
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Click **"API Keys"** in the left sidebar
4. Click **"Create Key"**
5. Copy the key (starts with `sk-ant-`)

**Pricing:**
- Free tier: $5 credit for testing
- Pay as you go: ~$3 per million input tokens

---

### 💾 Database (Choose One)

#### Option 1: SQLite (Default - No Setup)
**What:** File-based database, perfect for development
**Setup:** Already configured!
```env
DATABASE_URL=sqlite:///./devskyy.db
```
**No API key needed** ✅

#### Option 2: PostgreSQL (Local)
**What:** Production-grade database
**Setup with Docker:** Already included in docker-compose.yml
```env
DATABASE_URL=postgresql://devskyy:your-password@postgres:5432/devskyy
POSTGRES_PASSWORD=your-secure-password-here
```

#### Option 3: Neon (Cloud PostgreSQL - Free Tier)
**What:** Serverless PostgreSQL with generous free tier
**Where to get:**
1. Go to https://neon.tech
2. Sign up (free)
3. Create a new project
4. Copy the connection string from the dashboard
```env
DATABASE_URL=postgresql://username:password@ep-xxx-xxx.neon.tech/neondb
```
**Free tier:** 0.5 GB storage, unlimited compute hours

#### Option 4: Supabase (Cloud PostgreSQL - Free Tier)
**What:** PostgreSQL + more features
**Where to get:**
1. Go to https://supabase.com
2. Create account (free)
3. Create new project
4. Go to **Settings > Database**
5. Copy the **Connection String (URI)**
```env
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```
**Free tier:** 500 MB database, unlimited API requests

---

### 🚀 Optional But Recommended

#### Redis Cache
**What:** Super-fast caching for better performance
**Option 1: Local (with docker-compose)**
```env
REDIS_URL=redis://redis:6379
```
Already configured in docker-compose.yml ✅

**Option 2: Upstash (Cloud Redis - Free Tier)**
1. Go to https://upstash.com
2. Create account (free)
3. Create new database
4. Copy the **Redis URL**
```env
REDIS_URL=redis://default:password@xxx.upstash.io:6379
```
**Free tier:** 10,000 commands/day

#### OpenAI GPT-4 (Multi-model support)
**What:** Adds GPT-4 alongside Claude
**Where to get:**
1. Go to https://platform.openai.com
2. Sign up or log in
3. Click **API Keys** (left sidebar)
4. Click **Create new secret key**
5. Copy the key (starts with `sk-`)
```env
OPENAI_API_KEY=sk-your-key-here
```
**Pricing:** Pay as you go, ~$0.03 per 1K tokens (GPT-4)

---

### 🎨 WordPress Theme Deployment

#### WordPress Credentials
**What:** Deploy generated themes to your WordPress site
**Where to get:**
1. Log into your WordPress admin
2. Go to **Users > Profile**
3. Scroll to **Application Passwords**
4. Enter a name (e.g., "DevSkyy")
5. Click **Add New Application Password**
6. Copy the generated password

```env
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your-wp-username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

---

### 📱 Social Media Automation

#### Meta/Facebook Graph API
**What:** Automate Instagram and Facebook posts
**Where to get:**
1. Go to https://developers.facebook.com
2. Create an app (choose "Business")
3. Add **Instagram Graph API** product
4. Get your **Access Token** from the dashboard
5. Get your **Instagram Business Account ID**

```env
META_ACCESS_TOKEN=your-long-access-token
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
INSTAGRAM_ACCOUNT_ID=your-instagram-business-id
```

**Requirements:**
- Instagram Business account
- Facebook Page connected to Instagram
- App reviewed by Meta (for production)

---

### 💳 Payment Processing

#### Stripe (Recommended)
**What:** Accept credit card payments
**Where to get:**
1. Go to https://stripe.com
2. Create account (free)
3. Go to **Developers > API Keys**
4. Copy **Publishable key** and **Secret key**

```env
STRIPE_PUBLIC_KEY=pk_test_your-key
STRIPE_SECRET_KEY=sk_test_your-key
```

**Test mode:** Free forever, use test cards
**Live mode:** 2.9% + $0.30 per transaction

---

### 🔊 Voice & Audio

#### ElevenLabs
**What:** Text-to-speech, voice cloning
**Where to get:**
1. Go to https://elevenlabs.io
2. Sign up (free tier available)
3. Go to **Profile > API Keys**
4. Copy your API key

```env
ELEVENLABS_API_KEY=your-key-here
```

**Free tier:** 10,000 characters/month

---

### 📧 Email Service

#### SendGrid (Recommended)
**What:** Send transactional emails (order confirmations, etc.)
**Where to get:**
1. Go to https://sendgrid.com
2. Sign up (free)
3. Go to **Settings > API Keys**
4. Create API Key with **Full Access**

```env
SENDGRID_API_KEY=SG.your-key-here
SENDGRID_FROM_EMAIL=noreply@your-domain.com
```

**Free tier:** 100 emails/day

---

### 📊 Monitoring & Analytics

#### Sentry (Error Tracking)
**What:** Track and fix errors in production
**Where to get:**
1. Go to https://sentry.io
2. Create account (free)
3. Create new project (Python/FastAPI)
4. Copy the **DSN** from the setup page

```env
SENTRY_DSN=https://xxx@sentry.io/xxx
```

**Free tier:** 5,000 errors/month

#### Google Analytics
**What:** Track website visitors and conversions
**Where to get:**
1. Go to https://analytics.google.com
2. Create account and property
3. Copy your **Measurement ID** (starts with G- or UA-)

```env
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

**Free:** Unlimited

---

### ☁️ Cloud Storage

#### AWS S3
**What:** Store product images, media files
**Where to get:**
1. Go to https://aws.amazon.com/s3
2. Create account
3. Create **IAM user** with S3 permissions
4. Generate **Access Keys**

```env
AWS_ACCESS_KEY_ID=AKIAXXXXXXXX
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=devskyy-media
AWS_REGION=us-east-1
```

**Pricing:** ~$0.023/GB/month

#### Cloudflare R2 (Cheaper Alternative)
**What:** S3-compatible storage, no egress fees
**Where to get:**
1. Go to https://cloudflare.com
2. Go to **R2** in dashboard
3. Create bucket
4. Create **API token**

```env
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_ACCESS_KEY_ID=your-key
CLOUDFLARE_SECRET_ACCESS_KEY=your-secret
CLOUDFLARE_BUCKET=devskyy-media
```

**Pricing:** $0.015/GB/month (50% cheaper than S3)

---

## 🚀 Deployment-Specific Variables

### For Docker
```env
POSTGRES_DB=devskyy
POSTGRES_USER=devskyy
POSTGRES_PASSWORD=secure-password-here
GRAFANA_PASSWORD=admin
```

### For Production
```env
NODE_ENV=production
APP_URL=https://your-domain.com
LOG_LEVEL=warning
ENABLE_ANALYTICS=true
ENABLE_MONITORING=true
```

---

## ✅ Testing Your Configuration

### 1. Verify .env is loaded
```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✅ Loaded' if os.getenv('SECRET_KEY') else '❌ Not loaded')"
```

### 2. Test Anthropic API
```bash
python -c "from anthropic import Anthropic; import os; client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY')); print('✅ API key valid')"
```

### 3. Test Database Connection
```bash
python -c "from database import db_manager; import asyncio; asyncio.run(db_manager.health_check())"
```

### 4. Start the application
```bash
# With Docker
docker-compose up -d

# Or without Docker
python -m uvicorn main:app --reload
```

---

## 🔒 Security Best Practices

1. **Never commit .env to git**
   - Already in `.gitignore` ✅

2. **Use different keys for dev/production**
   - Create separate API keys for each environment

3. **Rotate keys regularly**
   - Change production keys every 90 days

4. **Use strong passwords**
   - Minimum 16 characters
   - Mix of letters, numbers, symbols

5. **Enable 2FA on all accounts**
   - Especially for payment processors and cloud providers

---

## 🆘 Troubleshooting

### "Module 'dotenv' not found"
```bash
pip install python-dotenv
```

### "API key not found"
Make sure your .env file is in the project root directory:
```bash
ls -la .env
```

### "Database connection failed"
Check your DATABASE_URL format:
```env
# SQLite (file path)
DATABASE_URL=sqlite:///./devskyy.db

# PostgreSQL (must include postgresql://)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### "Permission denied"
Make sure .env file has correct permissions:
```bash
chmod 600 .env
```

---

## 📝 Summary

**Minimum to get started:**
```env
SECRET_KEY=<generate with python command>
ANTHROPIC_API_KEY=sk-ant-<from console.anthropic.com>
DATABASE_URL=sqlite:///./devskyy.db
```

**Recommended for production:**
- PostgreSQL (Neon or Supabase)
- Redis (Upstash)
- Sentry (error tracking)
- Email service (SendGrid)
- Cloud storage (S3 or R2)

**Optional enhancements:**
- OpenAI (multi-model support)
- WordPress credentials (theme deployment)
- Stripe (payments)
- Meta API (social automation)
- ElevenLabs (voice features)

---

**Need help?** Check the logs:
```bash
docker-compose logs -f api
```
