# MCP Quick Reference Card

**Version:** 5.2.0 | **Last Updated:** 2025-11-20

---

## Overview

DevSkyy supports multiple MCP (Model Context Protocol) servers:
- **DevSkyy** - Internal tools and agents
- **Neon** - PostgreSQL database management
- **HuggingFace** - AI models and datasets

---

## Quick Commands

### Local Claude Desktop (On Your Machine)

```bash
# Add Neon MCP server to Claude Desktop
claude mcp add --transport http neon https://mcp.neon.tech/mcp

# List configured MCP servers
claude mcp list

# Remove a server
claude mcp remove neon

# Test connection
claude mcp test neon
```

### DevSkyy MCP Gateway (Server-Side)

```bash
# Start MCP gateway
docker-compose -f docker-compose.mcp.yml up -d mcp-gateway

# Check gateway status
curl http://localhost:3000/health

# List available servers
curl http://localhost:3000/servers
```

---

## Neon MCP Tools

### 1. List Branches

**cURL:**
```bash
curl -X POST http://localhost:3000/mcp/neon \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "list_branches",
    "params": {},
    "id": 1
  }'
```

**Python:**
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:3000/mcp/neon",
        json={
            "jsonrpc": "2.0",
            "method": "list_branches",
            "id": 1
        }
    )
    print(response.json())
```

### 2. Create Branch

**cURL:**
```bash
curl -X POST http://localhost:3000/mcp/neon \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "create_branch",
    "params": {
      "branch_name": "dev",
      "parent_branch_id": "br-main-xxx"
    },
    "id": 1
  }'
```

### 3. Execute SQL

**cURL:**
```bash
curl -X POST http://localhost:3000/mcp/neon \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "execute_sql",
    "params": {
      "branch_id": "br-main-xxx",
      "database": "devskyy",
      "sql": "SELECT * FROM users LIMIT 10"
    },
    "id": 1
  }'
```

### 4. Get Schema

**cURL:**
```bash
curl -X POST http://localhost:3000/mcp/neon \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_schema",
    "params": {
      "branch_id": "br-main-xxx",
      "database": "devskyy"
    },
    "id": 1
  }'
```

---

## Environment Variables

Required for Neon MCP:

```bash
# Database connection
DATABASE_URL=postgresql://...

# API credentials
NEON_API_KEY=your_api_key
NEON_PROJECT_ID=your_project_id

# MCP server URL
NEON_MCP_URL=https://mcp.neon.tech/mcp
```

---

## Testing

### Test MCP Gateway

```bash
# Health check
curl http://localhost:3000/health

# List servers
curl http://localhost:3000/servers

# Test Neon server with MCP request
curl -X POST http://localhost:3000/mcp/neon \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "list_branches",
    "params": {},
    "id": 1
  }'
```

### Test Local Claude Desktop

In Claude Desktop, try:
```
List all branches in my Neon project
```

---

## Troubleshooting

### Issue: "Server not found"

```bash
# Check if gateway is running
docker-compose -f docker-compose.mcp.yml ps mcp-gateway

# Check logs
docker-compose -f docker-compose.mcp.yml logs mcp-gateway

# Restart gateway
docker-compose -f docker-compose.mcp.yml restart mcp-gateway
```

### Issue: "Authentication failed"

```bash
# Verify environment variables
env | grep NEON

# Check API key in Neon dashboard
# Regenerate if needed
```

### Issue: "Connection timeout"

```bash
# Check network connectivity
curl https://mcp.neon.tech/mcp

# Verify firewall rules
# Check Docker networking
```

---

## Common Workflows

### Create Development Environment

```bash
# 1. Create dev branch
python scripts/neon_manager.py create-branches

# 2. Get connection string
python scripts/neon_manager.py connection-strings

# 3. Update .env with dev connection string
# DATABASE_URL=postgresql://...dev-branch...

# 4. Start DevSkyy
docker-compose -f docker-compose.dev.yml up -d
```

### Run Migrations

```bash
# 1. Set branch connection string
export DATABASE_URL="postgresql://...branch..."

# 2. Run Alembic migrations
alembic upgrade head

# 3. Verify schema
python scripts/neon_manager.py execute-sql \
  --branch dev \
  --sql "SELECT table_name FROM information_schema.tables"
```

### Test Feature Branch

```bash
# 1. Create feature branch
curl -X POST http://localhost:3000/mcp/neon \
  -d '{"method":"create_branch","params":{"branch_name":"feature-xyz"}}'

# 2. Run tests on feature branch
pytest --database-url="postgresql://...feature-xyz..."

# 3. Delete feature branch when done
python scripts/neon_manager.py delete-branch feature-xyz
```

---

## Documentation

- **MCP Setup:** `NEON_MCP_SETUP.md`
- **Neon Integration:** `NEON_INTEGRATION_GUIDE.md`
- **API Reference:** `API_ENDPOINTS_REFERENCE.md`
- **Neon Docs:** https://neon.tech/docs/mcp

---

## Quick Links

- **Neon Console:** https://console.neon.tech
- **Claude Desktop MCP:** https://claude.ai/mcp
- **DevSkyy MCP Gateway:** http://localhost:3000

---

**Status:** ✅ Ready to use
**Version:** 5.2.0
