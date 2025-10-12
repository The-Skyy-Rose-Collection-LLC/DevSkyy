# Enterprise Database Deployment Guide

**Complete guide for deploying DevSkyy with production databases**

---

## 🎯 Recommended: Neon (Serverless PostgreSQL)

**Why Neon:**
- ✅ 3GB Free Tier (generous)
- ✅ Serverless (scales to zero when idle)
- ✅ PostgreSQL 15+ (full compatibility)
- ✅ Auto-scaling
- ✅ Point-in-time recovery
- ✅ Branching (separate dev/staging databases)
- ✅ Production-ready

### Step-by-Step Setup

#### 1. Create Neon Account

```bash
# Visit and sign up
https://neon.tech

# No credit card required for free tier
```

#### 2. Create Project

1. Click "Create Project"
2. Name: `devskyy-production`
3. Region: Choose closest to your users
4. PostgreSQL Version: 15 or 16
5. Click "Create Project"

#### 3. Get Connection String

1. In your project dashboard
2. Click "Connection Details"
3. Copy the connection string:
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb
   ```

#### 4. Configure Environment

```bash
# Create production environment file
cp .env.production.template .env

# Edit .env and add your Neon URL
NEON_DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb
```

#### 5. Run Migrations

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python3 migrations/migrate.py
```

**Output:**
```
🚀 Starting Database Migration
🔧 Creating database tables...
✅ Database tables created successfully
🔍 Verifying database tables...
  ✅ Table 'products' exists
  ✅ Table 'customers' exists
  ✅ Table 'orders' exists
  ✅ Table 'payments' exists
  ✅ Table 'analytics' exists
  ✅ Table 'brand_assets' exists
  ✅ Table 'campaigns' exists
✅ Database Migration Complete
```

#### 6. Verify Connection

```bash
# Test database connection
python3 << 'EOF'
from database_config import DATABASE_URL, DB_PROVIDER
print(f"✅ Database: {DB_PROVIDER}")
print(f"✅ URL: {DATABASE_URL[:50]}...")
EOF
```

#### 7. Start Application

```bash
# Development
python3 main.py

# Production (4 workers)
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Enterprise
bash run_enterprise.sh
```

#### 8. Monitor in Neon Dashboard

- Go to Neon Console → Monitoring
- View:
  - Active connections
  - Query performance
  - Storage usage
  - CPU usage

---

## 🔄 Alternative: Supabase (PostgreSQL + Real-time)

**Why Supabase:**
- ✅ 500MB Free Tier
- ✅ PostgreSQL 15
- ✅ Real-time subscriptions
- ✅ Built-in auth
- ✅ Auto-generated REST API
- ✅ Storage included

### Setup Steps

#### 1. Create Project

```bash
# Visit
https://supabase.com

# Sign up and create project
```

#### 2. Get Database URL

1. Project Settings → Database
2. Connection String → Session mode
3. Copy connection string:
   ```
   postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
   ```

#### 3. Configure

```bash
# In .env
SUPABASE_DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

#### 4. Run Migrations

```bash
python3 migrations/migrate.py
```

---

## 💰 Alternative: PlanetScale (MySQL)

**Why PlanetScale:**
- ✅ 5GB Free Tier
- ✅ MySQL 8.0 compatible
- ✅ Branching workflow
- ✅ Non-blocking schema changes
- ✅ Production-ready

### Setup Steps

#### 1. Create Database

```bash
# Visit
https://planetscale.com

# Create account and database
```

#### 2. Get Connection String

1. Database → Connect
2. Copy connection string
3. Select "Connect with: General"

#### 3. Install MySQL Driver

```bash
# Add to requirements.txt
pip install aiomysql pymysql
```

#### 4. Configure

```bash
# In .env
PLANETSCALE_DATABASE_URL=mysql://user:password@aws.connect.psdb.cloud/database
```

#### 5. Run Migrations

```bash
python3 migrations/migrate.py
```

---

## 🔧 Custom PostgreSQL Setup

For self-hosted or custom PostgreSQL instances.

### Individual Credentials Method

```bash
# In .env
DB_HOST=your-host.com
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=devskyy

# Connection pool settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

### Direct URL Method

```bash
# In .env
DATABASE_URL=postgresql://user:password@host:5432/database
```

---

## 🚀 Production Deployment Checklist

### Before Deployment

- [ ] Choose database provider (Neon recommended)
- [ ] Create production database
- [ ] Copy `.env.production.template` to `.env`
- [ ] Configure `NEON_DATABASE_URL` (or chosen provider)
- [ ] Set `ENVIRONMENT=production`
- [ ] Generate secure `SECRET_KEY`
- [ ] Add AI service API keys
- [ ] Configure CORS origins

### Database Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test database connection
python3 -c "from database_config import DATABASE_URL, DB_PROVIDER; print(f'Provider: {DB_PROVIDER}')"

# 3. Run migrations
python3 migrations/migrate.py

# 4. Verify tables created
python3 -c "from database import engine; import asyncio; asyncio.run(engine.connect())"
```

### Application Deployment

```bash
# Option 1: Basic production
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Option 2: Enterprise with monitoring
bash run_enterprise.sh

# Option 3: Docker
docker build -t devskyy:4.0.0 .
docker run -p 8000:8000 --env-file .env devskyy:4.0.0
```

### Post-Deployment Verification

```bash
# Check health
curl https://your-domain.com/health

# Expected response:
{
  "status": "healthy",
  "platform": "operational",
  "database": "SQLAlchemy",
  "database_status": "healthy",
  "mongodb": false
}

# Check database provider
curl https://your-domain.com/

# Should show:
{
  "name": "DevSkyy Enterprise Platform",
  "version": "4.0.0",
  "features": {
    "database": "SQLAlchemy (SQLite/PostgreSQL)"
  }
}
```

---

## 📊 Database Comparison

| Feature | Neon | Supabase | PlanetScale | SQLite |
|---------|------|----------|-------------|--------|
| **Free Tier** | 3GB | 500MB | 5GB | Unlimited |
| **Type** | PostgreSQL | PostgreSQL | MySQL | File-based |
| **Serverless** | ✅ Yes | ❌ No | ✅ Yes | N/A |
| **Auto-scaling** | ✅ Yes | ❌ No | ✅ Yes | N/A |
| **Branching** | ✅ Yes | ❌ No | ✅ Yes | N/A |
| **Production Ready** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Setup Time** | 5 min | 5 min | 10 min | 0 min |
| **Best For** | Production | Full-stack apps | High-scale | Development |

**Recommendation:** Use **Neon** for production deployments.

---

## 🔐 Security Best Practices

### Environment Variables

```bash
# NEVER commit .env to git
echo ".env" >> .gitignore

# Use strong passwords
# Generate with:
openssl rand -hex 32
```

### Database Access

```bash
# Use connection pooling (already configured)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Enable SSL in production (automatic with Neon/Supabase)
ENVIRONMENT=production
```

### Backup Strategy

**Neon:**
- Automatic point-in-time recovery (7 days free tier)
- Manual backups via pg_dump

**Supabase:**
- Automatic daily backups
- Download via dashboard

**Manual Backup:**
```bash
# PostgreSQL
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20251011.sql
```

---

## 🐛 Troubleshooting

### Connection Fails

```bash
# Test connection
python3 << 'EOF'
import asyncio
from database import engine

async def test():
    async with engine.connect() as conn:
        print("✅ Connection successful")

asyncio.run(test())
EOF
```

### SSL Issues

```bash
# For Neon/Supabase, SSL is required
# The system handles this automatically

# If you see SSL errors, verify:
ENVIRONMENT=production  # Must be set
```

### Migration Fails

```bash
# Check database URL is correct
python3 -c "from database_config import DATABASE_URL; print(DATABASE_URL)"

# Verify you have write permissions
# Verify database exists

# Re-run migrations
python3 migrations/migrate.py
```

### Tables Not Created

```bash
# Manually check tables
python3 << 'EOF'
import asyncio
from sqlalchemy import inspect
from database import engine

async def check_tables():
    async with engine.connect() as conn:
        def _inspect(connection):
            inspector = inspect(connection)
            tables = inspector.get_table_names()
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")

        await conn.run_sync(_inspect)

asyncio.run(check_tables())
EOF
```

---

## 📈 Monitoring & Performance

### Database Metrics

**Neon Dashboard:**
- Active connections
- Query latency
- Storage usage
- Compute hours

**Application Metrics:**
```bash
# Check connection pool
curl http://localhost:8000/api/metrics

# Database health
curl http://localhost:8000/health
```

### Query Performance

```python
# Enable query logging in development
# In database.py:
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable SQL logging
)
```

### Connection Pool Tuning

```bash
# For high traffic:
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# For low traffic:
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

---

## 🔄 Scaling

### Vertical Scaling (Neon)

1. Go to Project Settings
2. Compute → Adjust compute units
3. Free tier: 0.25 CU (shared)
4. Paid tier: Up to 8 CU

### Horizontal Scaling

```bash
# Add read replicas (Neon Pro)
# Configure in Neon dashboard

# Update connection pool
DB_POOL_SIZE=20  # For multiple workers
```

### Caching Strategy

```python
# Already implemented in backend
from agent.modules.backend.cache_manager import cache_manager

# Use Redis for session/cache (optional)
pip install redis aioredis
```

---

## ✅ Final Checklist

### Database Setup
- [ ] Provider chosen (Neon recommended)
- [ ] Database created
- [ ] Connection string obtained
- [ ] .env configured
- [ ] Migrations run successfully
- [ ] Tables verified
- [ ] Connection tested

### Application
- [ ] Dependencies installed
- [ ] Environment variables set
- [ ] Application starts without errors
- [ ] Health endpoint returns healthy
- [ ] API docs accessible
- [ ] Database queries working

### Security
- [ ] .env not in git
- [ ] Strong SECRET_KEY set
- [ ] CORS origins configured
- [ ] SSL enabled (production)
- [ ] Backup strategy in place

### Production
- [ ] Workers configured (4 recommended)
- [ ] Monitoring enabled
- [ ] Logs configured
- [ ] Error tracking set up (Sentry optional)
- [ ] Performance baselines established

---

## 🎉 Success!

Your DevSkyy Enterprise Platform is now deployed with production-grade database!

**Next Steps:**
1. Monitor performance in database dashboard
2. Set up automated backups
3. Configure error tracking
4. Scale as needed

**Support:**
- Neon Docs: https://neon.tech/docs
- Supabase Docs: https://supabase.com/docs
- DevSkyy Docs: http://your-domain.com/docs

---

*Generated: 2025-10-11*
*Platform Version: 4.0.0*
*Database: Enterprise-Ready*
