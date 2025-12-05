# Neon PostgreSQL Integration Guide for DevSkyy

**Version:** 5.2.0
**Last Updated:** 2025-11-20
**Package:** `neon-api==0.3.0`

---

## Table of Contents

1. [What is Neon?](#what-is-neon)
2. [Why Use Neon with DevSkyy?](#why-use-neon-with-devskyy)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Using the Neon API](#using-the-neon-api)
6. [Database Management](#database-management)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## What is Neon?

**Neon** is a serverless PostgreSQL database platform that provides:

✅ **Serverless Postgres** - Auto-scaling, pay-per-use
✅ **Instant Provisioning** - Databases ready in seconds
✅ **Branching** - Git-like database branches for dev/staging/prod
✅ **Automatic Backups** - Point-in-time recovery
✅ **Global Availability** - Low-latency worldwide
✅ **Cost Effective** - Scale to zero when not in use

**Website:** https://neon.tech
**Documentation:** https://neon.tech/docs

---

## Why Use Neon with DevSkyy?

### Perfect for Cloud Deployments

1. **No Server Management** - Focus on your app, not database ops
2. **Auto-Scaling** - Handles traffic spikes automatically
3. **Cost Effective** - Free tier available, pay only for what you use
4. **Production Ready** - Enterprise-grade reliability
5. **Developer Friendly** - Easy to set up and manage

### DevSkyy Benefits

- **Multiple Environments** - Use branches for dev/staging/prod
- **Fast Startup** - No need to run local PostgreSQL
- **CI/CD Integration** - Easy to provision test databases
- **Global Performance** - Low latency for worldwide users

---

## Quick Start

### 1. Install neon-api

```bash
pip install neon-api
```

✅ Already added to `requirements.txt`

### 2. Sign Up for Neon

1. Go to https://neon.tech
2. Sign up (free tier available)
3. Create a new project
4. Get your API key from Settings > API Keys

### 3. Get Your Database Connection String

After creating a project, you'll get a connection string like:

```
postgresql://user:password@ep-cool-name-123456.us-east-2.aws.neon.tech/dbname?sslmode=require
```

### 4. Configure DevSkyy

**Option A: Environment Variables (.env)**

```bash
# Add to .env file
DATABASE_URL=postgresql://user:password@ep-cool-name-123456.us-east-2.aws.neon.tech/devskyy?sslmode=require
NEON_API_KEY=your_neon_api_key_here
```

**Option B: Docker Compose**

```yaml
# docker-compose.prod.yml
services:
  api:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - NEON_API_KEY=${NEON_API_KEY}
```

### 5. Test Connection

```python
# Quick test script
import asyncpg
import asyncio

async def test_neon_connection():
    conn = await asyncpg.connect('your-neon-connection-string')
    version = await conn.fetchval('SELECT version()')
    print(f"Connected to: {version}")
    await conn.close()

asyncio.run(test_neon_connection())
```

---

## Configuration

### Environment Variables

```bash
# .env file
# ===========================================================================
# Neon PostgreSQL Configuration
# ===========================================================================

# Database Connection (from Neon dashboard)
DATABASE_URL=postgresql://user:password@ep-name-123456.us-east-2.aws.neon.tech/devskyy?sslmode=require

# Neon API Key (for database management)
NEON_API_KEY=your_neon_api_key

# Neon Project ID (optional, for programmatic access)
NEON_PROJECT_ID=your_project_id

# Connection Pool Settings (recommended for Neon)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800  # 30 minutes
```

### SQLAlchemy Configuration

DevSkyy uses SQLAlchemy. Neon works seamlessly:

```python
# In your database configuration
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

# Create async engine (Neon supports asyncpg)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Important for Neon
    pool_recycle=1800,   # Recycle connections every 30 min
)

# Create session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

---

## Using the Neon API

The `neon-api` package allows you to programmatically manage your Neon databases.

### Basic Usage

```python
from neon_api import NeonAPI
import os

# Initialize client
neon = NeonAPI(api_key=os.getenv("NEON_API_KEY"))

# List projects
projects = neon.projects.list()
print(f"Found {len(projects)} projects")

# Get project details
project = neon.projects.get(project_id="your-project-id")
print(f"Project: {project.name}")

# List branches
branches = neon.branches.list(project_id="your-project-id")
for branch in branches:
    print(f"Branch: {branch.name} - {branch.id}")
```

### Creating Development Branches

```python
from neon_api import NeonAPI
import os

neon = NeonAPI(api_key=os.getenv("NEON_API_KEY"))
project_id = os.getenv("NEON_PROJECT_ID")

# Create a dev branch from main
dev_branch = neon.branches.create(
    project_id=project_id,
    branch_name="dev",
    parent_branch_id="main"
)

print(f"Dev branch created: {dev_branch.name}")
print(f"Connection string: {dev_branch.connection_uri}")

# Create a staging branch
staging_branch = neon.branches.create(
    project_id=project_id,
    branch_name="staging",
    parent_branch_id="main"
)

print(f"Staging branch created: {staging_branch.name}")
```

### Managing Databases

```python
# Create a new database
database = neon.databases.create(
    project_id=project_id,
    branch_id=branch.id,
    database_name="devskyy_test"
)

# List databases
databases = neon.databases.list(
    project_id=project_id,
    branch_id=branch.id
)

# Delete a database
neon.databases.delete(
    project_id=project_id,
    branch_id=branch.id,
    database_name="old_database"
)
```

---

## Database Management

### Creating a Management Script

Create `scripts/neon_manager.py`:

```python
#!/usr/bin/env python3
"""
Neon Database Management Script for DevSkyy
Manages Neon branches and databases programmatically
"""

import os
import sys
from neon_api import NeonAPI
from dotenv import load_dotenv

load_dotenv()

class NeonManager:
    def __init__(self):
        self.api_key = os.getenv("NEON_API_KEY")
        self.project_id = os.getenv("NEON_PROJECT_ID")

        if not self.api_key:
            raise ValueError("NEON_API_KEY not set in environment")
        if not self.project_id:
            raise ValueError("NEON_PROJECT_ID not set in environment")

        self.client = NeonAPI(api_key=self.api_key)

    def create_environment_branches(self):
        """Create dev, staging, and prod branches"""
        environments = ["dev", "staging", "prod"]

        for env in environments:
            try:
                branch = self.client.branches.create(
                    project_id=self.project_id,
                    branch_name=env,
                    parent_branch_id="main"
                )
                print(f"✅ Created {env} branch: {branch.id}")
                print(f"   Connection: {branch.connection_uri}")
            except Exception as e:
                print(f"❌ Failed to create {env} branch: {e}")

    def list_branches(self):
        """List all branches"""
        branches = self.client.branches.list(project_id=self.project_id)

        print(f"\n📊 Branches in project {self.project_id}:")
        for branch in branches:
            print(f"  - {branch.name} (ID: {branch.id})")

    def get_connection_strings(self):
        """Get connection strings for all branches"""
        branches = self.client.branches.list(project_id=self.project_id)

        print(f"\n🔗 Connection Strings:")
        for branch in branches:
            print(f"\n{branch.name.upper()}:")
            print(f"  {branch.connection_uri}")

    def create_test_database(self):
        """Create a test database for CI/CD"""
        try:
            # Get dev branch
            branches = self.client.branches.list(project_id=self.project_id)
            dev_branch = next((b for b in branches if b.name == "dev"), None)

            if not dev_branch:
                print("❌ Dev branch not found. Create it first.")
                return

            # Create test database
            database = self.client.databases.create(
                project_id=self.project_id,
                branch_id=dev_branch.id,
                database_name="devskyy_test"
            )

            print(f"✅ Created test database: {database.name}")
        except Exception as e:
            print(f"❌ Failed to create test database: {e}")

def main():
    manager = NeonManager()

    if len(sys.argv) < 2:
        print("Usage: python neon_manager.py [command]")
        print("Commands:")
        print("  create-branches    - Create dev/staging/prod branches")
        print("  list-branches      - List all branches")
        print("  connection-strings - Get connection strings")
        print("  create-test-db     - Create test database")
        return

    command = sys.argv[1]

    if command == "create-branches":
        manager.create_environment_branches()
    elif command == "list-branches":
        manager.list_branches()
    elif command == "connection-strings":
        manager.get_connection_strings()
    elif command == "create-test-db":
        manager.create_test_database()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
```

### Using the Management Script

```bash
# Create environment branches
python scripts/neon_manager.py create-branches

# List all branches
python scripts/neon_manager.py list-branches

# Get connection strings
python scripts/neon_manager.py connection-strings

# Create test database
python scripts/neon_manager.py create-test-db
```

---

## Production Deployment

### Docker Compose Configuration

**docker-compose.prod.yml:**

```yaml
services:
  api:
    environment:
      # Neon Production Database
      - DATABASE_URL=${NEON_PROD_DATABASE_URL}
      - NEON_API_KEY=${NEON_API_KEY}
      - NEON_PROJECT_ID=${NEON_PROJECT_ID}

      # Connection pool optimization for Neon
      - DB_POOL_SIZE=20
      - DB_MAX_OVERFLOW=10
      - DB_POOL_TIMEOUT=30
      - DB_POOL_RECYCLE=1800
```

### Environment-Specific Branches

**Development (.env.dev):**
```bash
DATABASE_URL=postgresql://user:pass@ep-dev-123.neon.tech/devskyy?sslmode=require
```

**Staging (.env.staging):**
```bash
DATABASE_URL=postgresql://user:pass@ep-staging-456.neon.tech/devskyy?sslmode=require
```

**Production (.env.prod):**
```bash
DATABASE_URL=postgresql://user:pass@ep-prod-789.neon.tech/devskyy?sslmode=require
```

### Database Migrations with Alembic

```bash
# Run migrations on Neon database
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Rollback
alembic downgrade -1
```

### Best Practices for Neon in Production

1. **Use Connection Pooling**
   ```python
   pool_size=20
   max_overflow=10
   pool_pre_ping=True
   pool_recycle=1800
   ```

2. **Enable SSL**
   ```
   ?sslmode=require
   ```

3. **Use Branches for Environments**
   - `main` branch → Production
   - `staging` branch → Staging
   - `dev` branch → Development

4. **Monitor Connection Usage**
   - Neon has connection limits per plan
   - Use connection pooling efficiently
   - Monitor `pg_stat_activity`

5. **Backups**
   - Neon handles backups automatically
   - Point-in-time recovery available
   - Test restore procedures regularly

---

## Troubleshooting

### Issue: Connection Refused

**Symptom:** `connection refused` or `timeout`

**Solution:**
1. Check your connection string is correct
2. Ensure `sslmode=require` is in the URL
3. Verify your IP is not blocked
4. Check Neon status: https://neon.tech/status

### Issue: Too Many Connections

**Symptom:** `FATAL: remaining connection slots are reserved`

**Solution:**
```python
# Reduce pool size
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,  # Reduce from 20
    max_overflow=5,  # Reduce from 10
)
```

### Issue: SSL Error

**Symptom:** `SSL connection error`

**Solution:**
```bash
# Ensure sslmode is in connection string
DATABASE_URL=postgresql://...?sslmode=require

# Or set SSL context in Python
import ssl
ssl_context = ssl.create_default_context()
```

### Issue: Slow Queries

**Symptom:** Queries taking longer than expected

**Solution:**
1. Check query execution plan:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM your_table;
   ```

2. Add indexes:
   ```sql
   CREATE INDEX idx_column ON your_table(column);
   ```

3. Use connection pooling properly

4. Check Neon region vs your app region (latency)

### Getting Help

- **Neon Documentation:** https://neon.tech/docs
- **Neon Community:** https://discord.gg/neon
- **DevSkyy Issues:** https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

---

## Integration with DevSkyy Features

### Health Checks

The monitoring endpoints will automatically work with Neon:

```bash
# Check database health
curl http://localhost:8000/api/v1/monitoring/health
```

### Prometheus Metrics

Neon connection metrics are tracked:

```
devskyy_database_connections_active
devskyy_database_query_duration_seconds
devskyy_database_errors_total
```

### Database Init Scripts

The init scripts in `docker/init-db/` work with Neon:

```bash
# Scripts will run on first connection
- 01-init-database.sql
- 02-create-indexes.sql
```

---

## Example: Complete Setup

Here's a complete example of setting up DevSkyy with Neon:

### 1. Create Neon Project

```bash
# Sign up at https://neon.tech
# Create a project named "devskyy"
# Get your connection string
```

### 2. Configure Environment

```bash
# .env
DATABASE_URL=postgresql://user:pass@ep-cool-name-123456.us-east-2.aws.neon.tech/devskyy?sslmode=require
NEON_API_KEY=your_api_key_here
NEON_PROJECT_ID=your_project_id
```

### 3. Update requirements

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start Application

```bash
# With Docker
docker-compose -f docker-compose.prod.yml up -d

# Or locally
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6. Verify Connection

```bash
curl http://localhost:8000/api/v1/monitoring/health
```

---

## Neon vs Self-Hosted PostgreSQL

| Feature | Neon | Self-Hosted |
|---------|------|-------------|
| Setup Time | Seconds | Hours/Days |
| Maintenance | None | Ongoing |
| Scaling | Automatic | Manual |
| Backups | Automatic | Manual setup |
| Cost | Pay-per-use | Fixed |
| Branching | Built-in | Manual |
| Performance | Optimized | Depends |

**Recommendation:** Use Neon for production DevSkyy deployments for ease and reliability.

---

## Next Steps

1. ✅ **Installed** `neon-api` package
2. ✅ **Added** to `requirements.txt`
3. 📝 **Sign up** for Neon account
4. 🔧 **Configure** connection string in `.env`
5. 🧪 **Test** connection
6. 🚀 **Deploy** to production

---

**Resources:**
- Neon Dashboard: https://console.neon.tech
- Neon Documentation: https://neon.tech/docs
- DevSkyy Deployment Guide: `DOCKER_DEPLOYMENT_GUIDE.md`
- API Reference: `API_ENDPOINTS_REFERENCE.md`

**Status:** ✅ Ready to use | **Version:** 5.2.0 | **Last Updated:** 2025-11-20
