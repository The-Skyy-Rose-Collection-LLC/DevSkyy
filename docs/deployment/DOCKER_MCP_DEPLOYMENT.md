# DevSkyy MCP Gateway - Docker Deployment Guide

## 🐳 Complete Docker-based MCP Infrastructure

This guide covers deploying DevSkyy's multi-server MCP infrastructure using Docker and Docker Compose.

---

## 📦 What's Included

**Services:**
- ✅ **DevSkyy API** - FastAPI backend (port 8000)
- ✅ **MCP Gateway** - Multi-server MCP router (port 3000)
- ✅ **MCP Server** - stdio server for Claude Desktop
- ✅ **PostgreSQL 15** - Production database (port 5432)
- ✅ **Redis 7** - Cache and session storage (port 6379)

**Features:**
- 🚀 One-command deployment
- 🔒 Production-ready security (non-root user, secrets via .env)
- 📊 Health checks and auto-restart
- 🌐 Multi-server MCP routing (DevSkyy + HuggingFace + custom)
- 🔄 Hot reloading for development
- 📝 Comprehensive logging

---

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites

```bash
# Required
docker --version      # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+

# Check installation
docker ps
docker-compose version
```

### 2. Configure Environment

```bash
# Copy example .env file
cp .env.example .env

# Edit .env and add your keys
nano .env
```

**Required Variables:**
```bash
# DevSkyy MCP
DEVSKYY_API_KEY=your-devskyy-api-key-here
DEVSKYY_API_URL=http://devskyy-api:8000

# HuggingFace MCP
HUGGING_FACE_TOKEN=hf_your_token_here

# Security
SECRET_KEY=your-secret-key-at-least-32-chars-long

# AI APIs
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-key

# Database (defaults work for local dev)
DATABASE_URL=postgresql://devskyy:devskyy@postgres:5432/devskyy
REDIS_URL=redis://redis:6379/0
```

### 3. Start All Services

```bash
# Build and start all services
docker-compose -f docker-compose.mcp.yml up -d

# View logs
docker-compose -f docker-compose.mcp.yml logs -f

# Check status
docker-compose -f docker-compose.mcp.yml ps
```

### 4. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check MCP Gateway
curl http://localhost:3000/health

# Check available MCP servers
curl http://localhost:3000/servers
```

**Expected Output:**
```json
{
  "servers": {
    "devskyy": {
      "type": "stdio",
      "status": "active"
    },
    "huggingface": {
      "type": "http",
      "status": "active"
    }
  }
}
```

---

## 🛠️ Service Details

### 1. DevSkyy API (port 8000)

Main FastAPI application with 54 AI agents.

**Endpoints:**
- `http://localhost:8000` - API root
- `http://localhost:8000/docs` - Swagger UI
- `http://localhost:8000/health` - Health check
- `http://localhost:8000/api/v1/mcp/install` - MCP deeplink generator

**Configuration:**
```yaml
# In docker-compose.mcp.yml
devskyy-api:
  ports:
    - "8000:8000"
  environment:
    - WORKERS=4  # Adjust based on CPU cores
    - LOG_LEVEL=INFO
```

### 2. MCP Gateway (port 3000)

Routes MCP requests to multiple servers (DevSkyy, HuggingFace, custom).

**Endpoints:**
- `http://localhost:3000` - Gateway status
- `http://localhost:3000/health` - Health check
- `http://localhost:3000/servers` - List MCP servers
- `http://localhost:3000/mcp/{server_name}` - Route to specific server

**Usage Example:**
```bash
# Call DevSkyy MCP server
curl -X POST http://localhost:3000/mcp/devskyy \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "devskyy_list_agents",
    "params": {},
    "id": 1
  }'

# Call HuggingFace MCP server
curl -X POST http://localhost:3000/mcp/huggingface \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "search_models",
    "params": {"query": "BERT"},
    "id": 2
  }'
```

### 3. MCP Server (stdio mode)

stdio-based MCP server for direct Claude Desktop integration.

**Connect from Claude Desktop:**
```json
{
  "mcpServers": {
    "devskyy-docker": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "devskyy-mcp-server",
        "python",
        "devskyy_mcp.py"
      ]
    }
  }
}
```

### 4. PostgreSQL Database (port 5432)

Production-grade PostgreSQL database.

**Connection:**
```bash
# Connect via psql
docker exec -it devskyy-postgres psql -U devskyy -d devskyy

# Backup database
docker exec devskyy-postgres pg_dump -U devskyy devskyy > backup.sql

# Restore database
cat backup.sql | docker exec -i devskyy-postgres psql -U devskyy -d devskyy
```

### 5. Redis Cache (port 6379)

High-performance cache for sessions and ML model results.

**Connection:**
```bash
# Connect via redis-cli
docker exec -it devskyy-redis redis-cli

# Check cache stats
docker exec devskyy-redis redis-cli INFO stats
```

---

## 🔧 Configuration

### Environment Variables

All configuration via `.env` file (never commit this!):

```bash
# =============================================================================
# APPLICATION
# =============================================================================
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# =============================================================================
# PORTS
# =============================================================================
API_PORT=8000
GATEWAY_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379

# =============================================================================
# WORKERS
# =============================================================================
API_WORKERS=4        # FastAPI workers (CPU cores)
GATEWAY_WORKERS=2    # MCP gateway workers

# =============================================================================
# MCP SERVERS
# =============================================================================
DEVSKYY_API_KEY=your-api-key
DEVSKYY_API_URL=http://devskyy-api:8000
HUGGING_FACE_TOKEN=hf_your_token

# =============================================================================
# SECURITY (Per Truth Protocol Rule #5)
# =============================================================================
SECRET_KEY=generate-with-secrets.token_urlsafe-32
JWT_SECRET_KEY=your-jwt-secret
ENCRYPTION_KEY=generate-with-Fernet.generate_key

# =============================================================================
# DATABASE
# =============================================================================
DATABASE_URL=postgresql://devskyy:devskyy@postgres:5432/devskyy
POSTGRES_DB=devskyy
POSTGRES_USER=devskyy
POSTGRES_PASSWORD=change-in-production

# =============================================================================
# REDIS
# =============================================================================
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=change-in-production

# =============================================================================
# AI APIS
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-key
GEMINI_API_KEY=your-gemini-key
```

### Docker Compose Profiles

Run specific services only:

```bash
# Development: API + Database only
docker-compose -f docker-compose.mcp.yml up devskyy-api postgres redis

# MCP Gateway only
docker-compose -f docker-compose.mcp.yml up mcp-gateway postgres redis

# Production: All services
docker-compose -f docker-compose.mcp.yml up -d
```

---

## 📊 Monitoring & Logs

### View Logs

```bash
# All services
docker-compose -f docker-compose.mcp.yml logs -f

# Specific service
docker-compose -f docker-compose.mcp.yml logs -f mcp-gateway

# Last 100 lines
docker-compose -f docker-compose.mcp.yml logs --tail=100 devskyy-api

# Filter by timestamp
docker-compose -f docker-compose.mcp.yml logs --since=30m mcp-gateway
```

### Health Checks

```bash
# Check all services
docker-compose -f docker-compose.mcp.yml ps

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' devskyy-api

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' devskyy-api
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Service-specific stats
docker stats devskyy-api mcp-gateway

# Memory usage
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"
```

---

## 🔄 Updates & Maintenance

### Update Services

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.mcp.yml build --no-cache

# Restart with new images
docker-compose -f docker-compose.mcp.yml up -d
```

### Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.mcp.yml exec devskyy-api alembic upgrade head

# Create new migration
docker-compose -f docker-compose.mcp.yml exec devskyy-api alembic revision --autogenerate -m "description"
```

### Backup & Restore

```bash
# Backup database
docker exec devskyy-postgres pg_dump -U devskyy devskyy > backup-$(date +%Y%m%d).sql

# Backup Redis
docker exec devskyy-redis redis-cli SAVE
docker cp devskyy-redis:/data/dump.rdb redis-backup-$(date +%Y%m%d).rdb

# Restore database
cat backup.sql | docker exec -i devskyy-postgres psql -U devskyy -d devskyy
```

---

## 🚨 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.mcp.yml logs

# Check .env file
cat .env | grep -v "^#" | grep -v "^$"

# Verify network
docker network inspect devskyy-mcp-network

# Remove and recreate
docker-compose -f docker-compose.mcp.yml down -v
docker-compose -f docker-compose.mcp.yml up -d
```

### Connection Issues

```bash
# Check if services are running
docker-compose -f docker-compose.mcp.yml ps

# Test database connection
docker-compose -f docker-compose.mcp.yml exec devskyy-api python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://devskyy:devskyy@postgres:5432/devskyy'); print('DB OK' if engine.connect() else 'DB FAIL')"

# Test Redis connection
docker-compose -f docker-compose.mcp.yml exec redis redis-cli PING
```

### Performance Issues

```bash
# Check resource usage
docker stats --no-stream

# Increase workers
# Edit docker-compose.mcp.yml:
# environment:
#   - WORKERS=8  # Increase based on CPU cores

# Restart services
docker-compose -f docker-compose.mcp.yml restart devskyy-api
```

### MCP Gateway Issues

```bash
# Check gateway logs
docker-compose -f docker-compose.mcp.yml logs mcp-gateway

# Test gateway directly
curl http://localhost:3000/health

# List available servers
curl http://localhost:3000/servers

# Restart gateway
docker-compose -f docker-compose.mcp.yml restart mcp-gateway
```

---

## 🔒 Security Best Practices

### Production Deployment

1. **Never commit .env file**
   ```bash
   # .gitignore already includes .env
   git status  # Verify .env is not tracked
   ```

2. **Use strong secrets**
   ```bash
   # Generate SECRET_KEY
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Generate ENCRYPTION_KEY
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. **Use non-root user** (already configured in Dockerfile)

4. **Enable HTTPS** (use reverse proxy like Nginx or Traefik)

5. **Limit exposed ports**
   ```yaml
   # Only expose what's needed
   ports:
     - "127.0.0.1:8000:8000"  # API - localhost only
     - "127.0.0.1:3000:3000"  # Gateway - localhost only
   ```

6. **Use Docker secrets** (instead of environment variables)
   ```yaml
   # docker-compose.mcp.yml
   secrets:
     devskyy_api_key:
       file: ./secrets/devskyy_api_key.txt
   services:
     devskyy-api:
       secrets:
         - devskyy_api_key
   ```

---

## 📚 Additional Resources

**Documentation:**
- Main README: `README.md`
- MCP Setup: `README_MCP.md`
- API Docs: `http://localhost:8000/docs`
- Gateway API: `http://localhost:3000/`

**Support:**
- Email: support@devskyy.com
- Docs: https://devskyy.com/docs
- GitHub: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy

---

## 📝 Per Truth Protocol

This deployment follows DevSkyy's Truth Protocol:
- ✅ **Rule #1:** Never guess - All configuration verified
- ✅ **Rule #2:** Pin versions - Python 3.11.9, PostgreSQL 15, Redis 7
- ✅ **Rule #3:** Cite standards - Docker Compose spec v3.8, OCI image spec
- ✅ **Rule #5:** No secrets in code - All secrets via .env or Docker secrets
- ✅ **Rule #6:** RBAC roles - Non-root user in containers
- ✅ **Rule #7:** Input validation - Health checks and restart policies
- ✅ **Rule #9:** Document all - Comprehensive inline documentation
- ✅ **Rule #12:** Performance SLOs - Health checks, resource limits
- ✅ **Rule #13:** Security baseline - Non-root, secrets management, TLS ready

**Version:** 1.0.0
**Last Updated:** 2025-01-12
**Status:** Production Ready ✅
