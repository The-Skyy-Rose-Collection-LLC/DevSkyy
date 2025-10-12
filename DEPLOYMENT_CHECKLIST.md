# DevSkyy Deployment Checklist

## Current Status: 🔴 NOT READY FOR PRODUCTION

**Last Safety Check:** 2025-10-09

### Critical Issues to Fix (3)

#### 1. ❌ Missing ANTHROPIC_API_KEY
```bash
# Add to .env file:
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
```

**How to get:**
- Sign up at https://console.anthropic.com/
- Create an API key
- Add to `.env` file

**Required for:**
- Claude Sonnet Intelligence Service
- Advanced AI reasoning
- Content generation
- All Claude-powered features

#### 2. ❌ Missing MONGODB_URI
```bash
# Add to .env file:
MONGODB_URI=mongodb://localhost:27017/devSkyy
```

**Options:**
- **Local:** `mongodb://localhost:27017/devSkyy`
- **MongoDB Atlas (Cloud):** `mongodb+srv://username:password@cluster.mongodb.net/devSkyy`
- **Docker:** `mongodb://mongodb:27017/devSkyy`

**Required for:**
- Database persistence
- User data
- Product catalog
- Order management
- All agent data storage

#### 3. ❌ Potential hardcoded API key in scanner.py
**Action:** Review `agent/modules/scanner.py` and remove any hardcoded keys

---

## Deployment Steps

### Step 1: Fix Critical Issues ⚠️

```bash
# 1. Add ANTHROPIC_API_KEY to .env
echo 'ANTHROPIC_API_KEY=your_key_here' >> .env

# 2. Add MONGODB_URI to .env
echo 'MONGODB_URI=mongodb://localhost:27017/devSkyy' >> .env

# 3. Generate secure SECRET_KEY
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env
```

### Step 2: Install Dependencies ✅

```bash
# Backend dependencies (takes ~35 seconds)
pip install -r requirements.txt

# Frontend dependencies (takes ~10 seconds)
cd frontend && npm install

# Install terser for production builds
cd frontend && npm install terser --save-dev
```

### Step 3: Start MongoDB 🗄️

**Option A: Local MongoDB**
```bash
# Install MongoDB (if not installed)
brew install mongodb-community  # macOS
# or
sudo apt install mongodb  # Ubuntu

# Start MongoDB
brew services start mongodb-community  # macOS
# or
sudo systemctl start mongodb  # Linux
```

**Option B: MongoDB Atlas (Recommended for Production)**
1. Sign up at https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get connection string
4. Update MONGODB_URI in .env

**Option C: Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Step 4: Run Tests 🧪

```bash
# Test backend loads
python3 -c "from main import app; print('✅ Backend loads successfully')"

# Run test suite
pytest tests/ -v

# Test specific module
pytest tests/test_main.py -v
```

### Step 5: Build Frontend 🎨

```bash
cd frontend
npm run build

# Verify build succeeded
ls dist/
```

### Step 6: Start Backend Server 🚀

```bash
# Development mode
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode (after testing)
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Verify it's running:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

### Step 7: Start Frontend Dev Server 🌐

```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Step 8: Enterprise Production Deployment 🏢

**Option A: Docker Deployment**
```bash
# Build Docker image
docker build -t devskyy .

# Run with environment file
docker run -p 8000:8000 --env-file .env devskyy
```

**Option B: Enterprise Script (Recommended)**
```bash
# Runs with auto-recovery, health monitoring, and security scanning
bash run_enterprise.sh
```

Features:
- 4 workers with uvloop
- Auto health monitoring (10s intervals)
- Security scanning via pip-audit
- Auto frontend build
- Zero-downtime failover
- Comprehensive logging to `enterprise_run.log`

**Option C: Manual Production**
```bash
# Install gunicorn for production
pip install gunicorn uvicorn[standard]

# Run with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Pre-Deployment Checklist

### Required ✅
- [ ] ANTHROPIC_API_KEY configured
- [ ] MONGODB_URI configured and MongoDB running
- [ ] SECRET_KEY set (min 32 characters)
- [ ] Backend loads without errors
- [ ] Tests pass (pytest)
- [ ] Frontend builds successfully
- [ ] Health check returns 200 OK

### Recommended ⚡
- [ ] OPENAI_API_KEY configured (for GPT features)
- [ ] META_ACCESS_TOKEN configured (for social media)
- [ ] ELEVENLABS_API_KEY configured (for voice features)
- [ ] Redis installed and running (for caching)
- [ ] SSL certificate configured
- [ ] Domain name configured
- [ ] Backup strategy in place
- [ ] Monitoring/logging configured (e.g., Sentry)

### Optional 🎯
- [ ] STRIPE_SECRET_KEY (for payments)
- [ ] SHOPIFY_API_KEY (for e-commerce integration)
- [ ] ETH_RPC_URL (for blockchain features)
- [ ] Email/SMTP configured
- [ ] CI/CD pipeline set up

---

## Production Environment Variables

Create `.env` file with these required variables:

```bash
# === CRITICAL - REQUIRED ===
SECRET_KEY=your_secure_random_32_char_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MONGODB_URI=mongodb://localhost:27017/devSkyy

# === APPLICATION ===
ENVIRONMENT=production
DEBUG=False
PORT=8000
CORS_ORIGINS=https://yourdomain.com

# === OPTIONAL BUT RECOMMENDED ===
OPENAI_API_KEY=your_openai_key_here
META_ACCESS_TOKEN=your_meta_token_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
REDIS_URL=redis://localhost:6379

# === OPTIONAL ===
STRIPE_SECRET_KEY=your_stripe_key_here
SHOPIFY_API_KEY=your_shopify_key_here
ETH_RPC_URL=your_ethereum_rpc_url_here
WORDPRESS_URL=your_wordpress_url_here
```

---

## Deployment Options

### 1. Local Development
```bash
# Quick start
bash scripts/quick_start.sh

# Or manual
python3 -m uvicorn main:app --reload
cd frontend && npm run dev
```

### 2. Docker
```bash
docker-compose up --build
```

### 3. Production Server
```bash
# Enterprise deployment with monitoring
bash run_enterprise.sh
```

### 4. Cloud Platforms

**Heroku:**
```bash
heroku create devskyy
heroku addons:create mongolab
git push heroku main
```

**AWS/DigitalOcean/GCP:**
- Use Docker image
- Configure environment variables
- Set up MongoDB Atlas
- Configure load balancer
- Enable HTTPS

---

## Health Checks

### Verify Deployment

```bash
# Backend health
curl http://localhost:8000/health

# Agent status
curl http://localhost:8000/brand/intelligence

# API docs
open http://localhost:8000/docs

# Frontend
open http://localhost:3000
```

### Expected Responses

**Health Check (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-09T...",
  "services": {
    "database": "connected",
    "cache": "available",
    "agents": "loaded"
  }
}
```

---

## Troubleshooting

### Issue: Backend won't start
```bash
# Check logs
tail -f app.log

# Check if port is in use
lsof -i :8000

# Verify environment
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('MONGODB_URI'))"
```

### Issue: MongoDB connection failed
```bash
# Check MongoDB is running
mongosh  # Try to connect

# Check connection string
echo $MONGODB_URI

# Use local fallback
MONGODB_URI=mongodb://localhost:27017/devSkyy python3 -m uvicorn main:app
```

### Issue: Frontend build fails
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
npm run build
```

---

## Quick Deployment Commands

### Development (Fastest)
```bash
# Terminal 1: Backend
python3 -m uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Production (Recommended)
```bash
# Single command with auto-recovery
bash run_enterprise.sh
```

### Docker (Containerized)
```bash
# One command deployment
docker-compose -f docker-compose.prod.yml up --build
```

---

## Next Steps After Deployment

1. **Monitor logs:** `tail -f app.log` or `tail -f enterprise_run.log`
2. **Test all endpoints:** Use `/docs` for interactive API testing
3. **Configure monitoring:** Set up Sentry, DataDog, or similar
4. **Set up backups:** MongoDB backup strategy
5. **Enable HTTPS:** Use Let's Encrypt or CloudFlare
6. **Scale:** Add more workers as needed

---

## Support

- **Documentation:** See `CLAUDE.md` for architecture details
- **Agent Upgrades:** See `AGENT_UPGRADE_GUIDE.md`
- **Security:** See `SECURITY.md`
- **Issues:** Check logs first, then `PRODUCTION_SAFETY_REPORT.md`

---

**Status Legend:**
- 🔴 Critical - Must fix before deployment
- ⚠️ Warning - Should fix before production
- ✅ Ready - Good to go
- ⚡ Recommended - Nice to have
- 🎯 Optional - For advanced features
