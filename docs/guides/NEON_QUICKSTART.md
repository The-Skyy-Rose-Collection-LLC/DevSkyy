# 🚀 Neon Quick Start Guide for DevSkyy

**Time to setup:** ~5 minutes
**Difficulty:** Easy

---

## ⚡ Quick Setup (3 Steps)

### Step 1: Sign Up & Create Project (2 min)

1. **Go to:** https://neon.tech
2. **Sign up** using GitHub (fastest)
3. **Create project:**
   - Name: `devskyy`
   - Region: Choose closest to you
   - Click "Create project"

### Step 2: Get Your Credentials (2 min)

**A. Get Connection String** (from project dashboard)
```
postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**B. Get API Key** (Settings → API Keys → Create API key)
```
Copy the key - you won't see it again!
```

**C. Get Project ID** (from URL or Settings)
```
Example: ep-aged-mountain-12345678
```

### Step 3: Configure DevSkyy (1 min)

**Option A - Interactive (Easiest):**
```bash
bash scripts/configure_neon.sh
```

**Option B - Manual:**
```bash
# Edit .env file
nano .env

# Find and replace these lines:
DATABASE_URL=your_actual_neon_connection_string
NEON_API_KEY=your_actual_api_key
NEON_PROJECT_ID=your_actual_project_id

# Save and exit (Ctrl+O, Enter, Ctrl+X)
```

---

## ✅ Verify Setup

```bash
# Test connection
python scripts/neon_manager.py project-info

# Expected output:
# ✅ Connected to Neon project: ep-xxx-xxx
# 📊 Project Information:
# ================================
# Project ID: ep-xxx-xxx
# Name: devskyy
# Region: us-east-2
# Status: active
```

---

## 🎯 Create Environment Branches

```bash
# Create dev, staging, prod branches
python scripts/neon_manager.py create-branches

# View all branches
python scripts/neon_manager.py list-branches

# Get connection strings
python scripts/neon_manager.py connection-strings
```

---

## 🚀 Start DevSkyy

```bash
# Start with Docker
docker-compose -f docker-compose.dev.yml up -d

# Check health
curl http://localhost:8000/health
```

---

## 📋 What You Get

✅ **Serverless PostgreSQL** - No server management
✅ **Auto-scaling** - Handles traffic automatically
✅ **Database Branching** - Like Git for databases
✅ **Automatic Backups** - Point-in-time recovery
✅ **Free Tier** - 0.5GB storage, unlimited queries
✅ **Global Performance** - Low latency worldwide

---

## 🆘 Troubleshooting

### Issue: "NEON_API_KEY not set"

**Solution:**
```bash
# Check if .env exists and has Neon config
cat .env | grep NEON

# If empty, run configuration:
bash scripts/configure_neon.sh
```

### Issue: "Connection refused"

**Solution:**
1. Check connection string has `?sslmode=require`
2. Verify credentials in Neon dashboard
3. Check your IP is not blocked

### Issue: "Project not found"

**Solution:**
1. Verify PROJECT_ID is correct
2. Check API key is valid
3. Ensure you're using the right project

---

## 📚 Learn More

- **Full Guide:** `NEON_INTEGRATION_GUIDE.md`
- **Neon Docs:** https://neon.tech/docs
- **DevSkyy Deployment:** `DOCKER_DEPLOYMENT_GUIDE.md`

---

## 🎉 You're Ready!

Once configured, you can:

```bash
# Create branches
python scripts/neon_manager.py create-branches

# List branches
python scripts/neon_manager.py list-branches

# Get connection strings
python scripts/neon_manager.py connection-strings

# Start DevSkyy
docker-compose -f docker-compose.dev.yml up -d

# Check health
curl http://localhost:8000/api/v1/monitoring/health
```

---

**Need Help?**
- Run: `python scripts/neon_manager.py help`
- Check: `NEON_INTEGRATION_GUIDE.md`
- Visit: https://neon.tech/docs
