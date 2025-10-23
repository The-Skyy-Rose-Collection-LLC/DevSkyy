# DevSkyy Vercel Deployment Guide

## 🚀 **Essential Root-Level Files for Vercel Deployment**

This guide provides comprehensive instructions for deploying the DevSkyy Enterprise Platform on Vercel with optimal configuration.

---

## **📁 Required Root-Level Files**

### **1. vercel.json (Primary Configuration)**
```json
{
  "version": 2,
  "name": "devskyy-enterprise-platform",
  "framework": "other",
  "buildCommand": "pip install -r requirements.txt",
  "outputDirectory": ".",
  "installCommand": "pip install --upgrade pip && pip install -r requirements.txt",
  "devCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT --reload",
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb",
        "runtime": "python3.11"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "main.py"
    },
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ],
  "env": {
    "PYTHONPATH": ".",
    "ENVIRONMENT": "production",
    "LOG_LEVEL": "INFO",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1"
  },
  "functions": {
    "main.py": {
      "maxDuration": 30,
      "memory": 1024,
      "runtime": "python3.11"
    }
  },
  "regions": ["iad1"],
  "github": {
    "autoDeployment": true,
    "autoJobCancelation": true
  }
}
```

### **2. requirements.txt (Python Dependencies)**
```txt
# Core FastAPI Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Essential Dependencies
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Database
sqlalchemy==2.0.23
alembic==1.13.0

# HTTP Client
httpx==0.25.2
requests==2.31.0

# Logging and Monitoring
structlog==23.2.0

# Security
cryptography==41.0.8

# Utilities
python-dotenv==1.0.0
email-validator==2.1.0

# Agent Framework Dependencies
redis==5.0.1
aioredis==2.0.1
```

### **3. runtime.txt (Python Version)**
```txt
python-3.11
```

### **4. .vercelignore (Exclude Files)**
```txt
# Development files
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git/
.mypy_cache/
.pytest_cache/
.hypothesis/

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
tests/
docs/
*.md
!README.md
tools/
scripts/
.github/
```

### **5. package.json (Node.js Compatibility)**
```json
{
  "name": "devskyy-enterprise-platform",
  "version": "5.2.0",
  "description": "DevSkyy Enterprise Fashion E-commerce Automation Platform",
  "main": "main.py",
  "scripts": {
    "build": "pip install -r requirements.txt",
    "start": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "dev": "uvicorn main:app --host 0.0.0.0 --port $PORT --reload"
  },
  "engines": {
    "node": ">=18.0.0"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/SkyyRoseLLC/DevSkyy.git"
  },
  "keywords": [
    "fashion",
    "ecommerce",
    "ai",
    "automation",
    "enterprise"
  ],
  "author": "Skyy Rose LLC",
  "license": "MIT"
}
```

---

## **🏗️ Entry Point Files and Naming Conventions**

### **Primary Entry Point: main.py**
- **Location**: Root directory (`/main.py`)
- **Purpose**: FastAPI application entry point
- **Requirements**:
  - Must contain `app = FastAPI()` instance
  - Should handle all routing and middleware
  - Must be compatible with ASGI servers

### **Alternative Entry Points**
```python
# api/index.py (Alternative structure)
from main import app

# For Vercel's automatic detection
handler = app

# wsgi.py (WSGI compatibility)
from main import app
application = app
```

---

## **📂 Directory Structure Requirements**

### **Recommended Structure**
```
DevSkyy/                          # Root directory
├── main.py                       # Primary entry point ✅
├── vercel.json                   # Vercel configuration ✅
├── requirements.txt              # Python dependencies ✅
├── runtime.txt                   # Python version ✅
├── package.json                  # Node.js compatibility ✅
├── .vercelignore                 # Exclude files ✅
├── .env.example                  # Environment template
├── api/                          # API modules
│   ├── __init__.py
│   ├── v1/                       # API versioning
│   └── middleware/               # Custom middleware
├── agent/                        # Agent framework
│   ├── modules/                  # Agent modules
│   ├── orchestrator.py           # Agent coordination
│   └── registry.py               # Agent registry
├── models/                       # Data models
├── security/                     # Security modules
├── ml/                          # Machine learning
├── static/                      # Static files (optional)
└── templates/                   # Templates (optional)
```

### **Vercel-Specific Requirements**
- **Root-level main.py**: Must be in project root
- **No nested entry points**: Vercel looks for entry point in root
- **Static files**: Place in `/static` or `/public` directory
- **Environment files**: Use Vercel dashboard for production secrets

---

## **🔧 Environment Variable Configuration**

### **Required Environment Variables**
```bash
# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONPATH=.
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1

# FastAPI Settings
FASTAPI_ENV=production
API_V1_STR=/api/v1
PROJECT_NAME=DevSkyy Enterprise Platform
VERSION=5.2.0

# Security Settings
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ENCRYPTION_KEY=your-encryption-key-here

# Database Settings
DATABASE_URL=your-database-url-here
REDIS_URL=your-redis-url-here

# External API Keys
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here

# Feature Flags
ENTERPRISE_FEATURES_ENABLED=true
AGENT_ORCHESTRATION_ENABLED=true
ML_FEATURES_ENABLED=true

# Performance Settings
MAX_WORKERS=1
TIMEOUT_SECONDS=30
MAX_REQUEST_SIZE=10485760

# CORS Settings
ALLOWED_ORIGINS=["https://your-domain.com"]
ALLOWED_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
ALLOWED_HEADERS=["*"]
```

### **Setting Environment Variables in Vercel**
1. Go to Vercel Dashboard → Project Settings
2. Navigate to Environment Variables
3. Add each variable with appropriate values
4. Set environment scope (Production, Preview, Development)

---

## **🐍 Python-Specific Requirements for Vercel**

### **Runtime Configuration**
- **Python Version**: 3.11 (specified in runtime.txt)
- **Package Manager**: pip (default)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### **Dependency Management**
```txt
# requirements.txt optimization for Vercel
# Keep dependencies minimal for faster cold starts
# Use specific versions for reproducible builds
# Avoid heavy ML libraries in serverless environment
```

### **Memory and Timeout Limits**
- **Memory**: 1024MB (configurable in vercel.json)
- **Timeout**: 30 seconds (maximum for Hobby plan)
- **Bundle Size**: 50MB maximum (including dependencies)

### **Cold Start Optimization**
```python
# main.py optimizations
import os
import sys

# Lazy imports for faster cold starts
def get_ml_engine():
    from ml.recommendation_engine import RecommendationEngine
    return RecommendationEngine()

# Minimize startup time
if os.getenv("ENVIRONMENT") == "production":
    # Production optimizations
    import gc
    gc.set_threshold(700, 10, 10)
```

---

## **⚡ Best Practices for Vercel Organization**

### **1. Project Structure**
- Keep root directory clean
- Use clear module organization
- Separate concerns (API, agents, models)
- Follow Python package conventions

### **2. Configuration Management**
- Use environment variables for all secrets
- Separate development and production configs
- Version control configuration files
- Document all required variables

### **3. Performance Optimization**
- Minimize cold start time
- Use lazy loading for heavy imports
- Optimize bundle size
- Implement proper caching strategies

### **4. Security Best Practices**
- Never commit secrets to version control
- Use Vercel's environment variable encryption
- Implement proper CORS policies
- Validate all inputs and outputs

### **5. Monitoring and Logging**
- Use structured logging
- Implement health checks
- Monitor performance metrics
- Set up error tracking

---

## **🚀 Deployment Commands**

### **Local Development**
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link project
vercel link

# Local development
vercel dev
```

### **Production Deployment**
```bash
# Deploy to production
vercel --prod

# Deploy with environment variables
vercel --prod --env ENVIRONMENT=production
```

### **Automated Deployment**
- **GitHub Integration**: Automatic deployment on push to main
- **Preview Deployments**: Automatic deployment for pull requests
- **Environment Promotion**: Promote preview to production

---

This configuration ensures optimal performance, security, and maintainability for the DevSkyy Enterprise Platform on Vercel.
