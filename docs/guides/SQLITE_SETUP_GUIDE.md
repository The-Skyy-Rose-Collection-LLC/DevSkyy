# DevSkyy SQLite Setup Guide

## 🗄️ **Complete SQLite Database Configuration**

**Python 3.11+ — SQLite with SQLAlchemy Async Support**

### **📋 Overview**

DevSkyy uses SQLite as the default database for development and Vercel deployment, with automatic migration to PostgreSQL for production scaling.

**Database Features:**
- ✅ SQLAlchemy ORM with async support
- ✅ Automatic table creation and migrations
- ✅ Production-ready models for e-commerce
- ✅ Health checks and connection management
- ✅ Backward compatibility with existing code

---

## 🔧 **Database Configuration**

### **1. Current Database URL Configuration**

The database URL is automatically configured based on environment:

```python
# Priority order:
1. DATABASE_URL environment variable
2. Neon/Supabase/PlanetScale URLs
3. Individual PostgreSQL credentials
4. Default: SQLite (sqlite+aiosqlite:///./devskyy.db)
```

### **2. Environment Variables**

**For Local Development:**
```bash
# Optional - defaults to SQLite
DATABASE_URL=sqlite+aiosqlite:///./devskyy.db
DEBUG=True
```

**For Vercel Deployment:**
```bash
# Recommended for serverless
DATABASE_URL=sqlite+aiosqlite:///./devskyy.db
ENVIRONMENT=production
```

**For Production Scaling:**
```bash
# PostgreSQL (Neon recommended)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
# or
NEON_DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname
```

---

## 📊 **Database Models**

### **Core Models Available:**

1. **User Management**
   - `User` - Application users with authentication
   - JWT token support with role-based access

2. **E-commerce Core**
   - `Product` - Product catalog with variants, images, SEO
   - `Customer` - Customer profiles with preferences
   - `Order` - Order management with payment tracking

3. **AI & Analytics**
   - `AgentLog` - AI agent activity tracking
   - `BrandAsset` - Brand intelligence and assets
   - `Campaign` - Marketing campaign management

### **Model Features:**
- ✅ JSON fields for flexible data storage
- ✅ Automatic timestamps (created_at, updated_at)
- ✅ Proper indexing for performance
- ✅ Async-compatible with SQLAlchemy 2.0

---

## 🚀 **Setup Instructions**

### **Step 1: Database Initialization**

The database is automatically initialized when the application starts:

```python
# Automatic initialization in main.py
from database import init_db, db_manager

# Tables are created automatically on startup
await init_db()
```

### **Step 2: Manual Database Setup (Optional)**

If you need to manually initialize the database:

```bash
cd DevSkyy
python init_database.py
```

### **Step 3: Verify Database Setup**

```bash
# Check if database file exists
ls -la devskyy.db

# Test database connection
python -c "
import asyncio
from database import db_manager

async def test():
    health = await db_manager.health_check()
    print(f'Database Status: {health}')

asyncio.run(test())
"
```

---

## 💻 **Usage Examples**

### **1. Basic Database Operations**

```python
from database import get_db
from models_sqlalchemy import User, Product
from sqlalchemy import select

# Create a new user
async def create_user(db: AsyncSession):
    user = User(
        email="user@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password_here"
    )
    db.add(user)
    await db.commit()
    return user

# Query users
async def get_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### **2. FastAPI Integration**

```python
from fastapi import Depends
from database import get_db

@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [{"id": u.id, "email": u.email} for u in users]

@app.post("/users")
async def create_user(user_data: dict, db: AsyncSession = Depends(get_db)):
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email}
```

### **3. Agent Integration**

```python
from database import db_manager
from models_sqlalchemy import AgentLog

# Log agent activity
async def log_agent_activity(agent_name: str, action: str, result: dict):
    async with db_manager.get_session() as db:
        log_entry = AgentLog(
            agent_name=agent_name,
            action=action,
            status="success",
            output_data=result,
            execution_time_ms=100.5
        )
        db.add(log_entry)
        await db.commit()
```

---

## 🔍 **Database Management**

### **1. Health Checks**

```python
# Built-in health check
from database import db_manager

health_status = await db_manager.health_check()
print(health_status)
# Output: {"status": "healthy", "connected": True, "type": "SQLAlchemy"}
```

### **2. Connection Management**

```python
# Manual connection management
await db_manager.connect()    # Initialize
await db_manager.disconnect() # Cleanup
```

### **3. Session Management**

```python
# Get database session
async with db_manager.get_session() as db:
    # Use db session here
    result = await db.execute(select(User))
    users = result.scalars().all()
    # Session automatically closed and committed
```

---

## 📈 **Performance Optimization**

### **SQLite Optimizations Applied:**

1. **Connection Pooling**
   - Async session factory for efficient connections
   - Automatic session cleanup and error handling

2. **Query Optimization**
   - Proper indexing on frequently queried fields
   - JSON fields for flexible data without joins

3. **Memory Management**
   - Connection pooling with automatic cleanup
   - Efficient async operations

### **Performance Settings:**

```python
# Optimized for serverless deployment
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Disable SQL logging in production
    future=True,  # Use SQLAlchemy 2.0 features
    pool_pre_ping=True,  # Verify connections
)
```

---

## 🔄 **Migration Path**

### **SQLite → PostgreSQL Migration**

When ready to scale, migrate to PostgreSQL:

1. **Set PostgreSQL URL**
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
   ```

2. **Export SQLite Data**
   ```bash
   python -c "
   import asyncio
   from database import db_manager
   from sqlalchemy import select
   from models_sqlalchemy import User, Product, Customer
   
   async def export_data():
       async with db_manager.get_session() as db:
           # Export logic here
           pass
   
   asyncio.run(export_data())
   "
   ```

3. **Import to PostgreSQL**
   - Tables are automatically created
   - Data can be imported using standard SQL tools

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **Issue: Database file not found**
```bash
# Solution: Initialize database
python init_database.py
```

#### **Issue: Permission errors**
```bash
# Solution: Check file permissions
chmod 664 devskyy.db
```

#### **Issue: Connection errors**
```bash
# Solution: Verify database URL
python -c "from database_config import DATABASE_URL; print(DATABASE_URL)"
```

#### **Issue: Table not found**
```bash
# Solution: Recreate tables
python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
"
```

---

## 📊 **Database Schema**

### **Current Tables:**

1. **users** - User authentication and profiles
2. **products** - Product catalog with variants
3. **customers** - Customer management
4. **orders** - Order processing and tracking
5. **agent_logs** - AI agent activity logs
6. **brand_assets** - Brand intelligence data
7. **campaigns** - Marketing campaign tracking

### **Schema Features:**
- ✅ Auto-incrementing primary keys
- ✅ Proper foreign key relationships
- ✅ JSON fields for flexible data
- ✅ Timestamp tracking
- ✅ Indexing for performance

---

## 🎯 **Best Practices**

### **Development:**
1. Use SQLite for local development
2. Enable SQL logging with `DEBUG=True`
3. Regular database backups
4. Test migrations before production

### **Production:**
1. Use PostgreSQL for scaling
2. Disable SQL logging
3. Monitor connection pools
4. Regular performance analysis

### **Vercel Deployment:**
1. SQLite works perfectly for serverless
2. Database file persists across deployments
3. Automatic initialization on cold starts
4. No additional configuration needed

---

**🎉 SQLite setup is complete and production-ready!**

*The database automatically initializes on application startup.*
*No manual setup required for basic usage.*

**Last Updated:** 2024-10-24  
**Version:** 2.0.0  
**Status:** ✅ PRODUCTION READY
