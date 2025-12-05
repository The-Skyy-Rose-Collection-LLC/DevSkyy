# Neon MCP Server Setup Guide

**Version:** 5.2.0
**Last Updated:** 2025-11-20

---

## Overview

Neon provides an MCP (Model Context Protocol) server that allows Claude to interact with your Neon databases directly. This guide covers two setups:

1. **Local Claude Desktop App** - Use Neon MCP in Claude desktop
2. **DevSkyy Integration** - Integrate Neon MCP with DevSkyy platform

---

## Part 1: Local Claude Desktop App Setup

### Prerequisites

- Claude Desktop App installed (macOS/Windows)
- Neon account with API key
- Project already created in Neon

### Step 1: Add Neon MCP Server

**On Your Local Machine (NOT in this terminal):**

```bash
# Run this on your local machine where Claude Desktop is installed
claude mcp add --transport http neon https://mcp.neon.tech/mcp
```

### Step 2: Configure Environment Variables

The MCP server needs your Neon credentials. Add to your local environment:

**macOS/Linux:**
```bash
# Add to ~/.zshrc or ~/.bashrc
export NEON_API_KEY="your_neon_api_key"
export NEON_PROJECT_ID="your_project_id"
```

**Windows:**
```powershell
# Add to environment variables via System Settings
# Or in PowerShell:
$env:NEON_API_KEY="your_neon_api_key"
$env:NEON_PROJECT_ID="your_project_id"
```

### Step 3: Restart Claude Desktop

After adding the MCP server:
1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Check MCP settings to verify Neon server is active

### Step 4: Verify in Claude Desktop

In Claude Desktop, you should now be able to:
- Query your Neon databases
- Create branches
- Manage schemas
- Run SQL queries

Example prompt:
```
List all branches in my Neon project
```

---

## Part 2: DevSkyy Platform Integration

### Overview

DevSkyy has its own MCP gateway that can route requests to multiple MCP servers, including Neon.

### Architecture

```
DevSkyy API
    ↓
MCP Gateway (docker/mcp_gateway.py)
    ↓
  ┌─────┼──────┐
  ↓     ↓      ↓
DevSkyy Neon  HuggingFace
  MCP   MCP     MCP
```

### Step 1: Update MCP Gateway Configuration

Already configured! The DevSkyy MCP gateway supports Neon.

**File:** `docker/mcp_gateway.py`

The gateway is pre-configured with Neon support via HTTP transport.

### Step 2: Configure Environment Variables

Add to your `.env` file (already done if you followed Neon setup):

```bash
# Neon MCP Configuration
NEON_API_KEY=your_neon_api_key
NEON_PROJECT_ID=your_project_id
NEON_MCP_URL=https://mcp.neon.tech/mcp
```

### Step 3: Update Docker Compose

The MCP gateway is already configured in your Docker setup. To enable it:

**docker-compose.dev.yml:**
```yaml
services:
  mcp-gateway:
    build:
      context: .
      dockerfile: docker/Dockerfile.mcp
    container_name: devskyy-mcp-gateway
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEON_API_KEY=${NEON_API_KEY}
      - NEON_PROJECT_ID=${NEON_PROJECT_ID}
      - NEON_MCP_URL=https://mcp.neon.tech/mcp
      - DEVSKYY_API_KEY=${DEVSKYY_API_KEY}
      - HUGGING_FACE_TOKEN=${HUGGING_FACE_TOKEN}
    networks:
      - devskyy-dev-network
```

### Step 4: Start MCP Gateway

```bash
# Start with MCP gateway
docker-compose -f docker-compose.dev.yml up -d mcp-gateway

# Check logs
docker-compose -f docker-compose.dev.yml logs -f mcp-gateway
```

### Step 5: Test Neon MCP Integration

```bash
# Test Neon MCP endpoint
curl -X POST http://localhost:3000/mcp/neon \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "list_branches",
    "params": {},
    "id": 1
  }'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "branches": [
      {"name": "main", "id": "br-xxx"},
      {"name": "dev", "id": "br-yyy"},
      {"name": "staging", "id": "br-zzz"}
    ]
  },
  "id": 1
}
```

---

## Available Neon MCP Tools

Once configured, you can use these tools:

### 1. List Branches
```json
{
  "method": "list_branches",
  "params": {
    "project_id": "ep-xxx-xxx"
  }
}
```

### 2. Create Branch
```json
{
  "method": "create_branch",
  "params": {
    "project_id": "ep-xxx-xxx",
    "branch_name": "feature-branch",
    "parent_branch_id": "br-main-xxx"
  }
}
```

### 3. Execute SQL
```json
{
  "method": "execute_sql",
  "params": {
    "project_id": "ep-xxx-xxx",
    "branch_id": "br-xxx-xxx",
    "database": "devskyy",
    "sql": "SELECT * FROM users LIMIT 10"
  }
}
```

### 4. Get Database Schema
```json
{
  "method": "get_schema",
  "params": {
    "project_id": "ep-xxx-xxx",
    "branch_id": "br-xxx-xxx",
    "database": "devskyy"
  }
}
```

### 5. Create Database
```json
{
  "method": "create_database",
  "params": {
    "project_id": "ep-xxx-xxx",
    "branch_id": "br-xxx-xxx",
    "database_name": "new_db"
  }
}
```

---

## Using Neon MCP in DevSkyy API

### Example: Create Branch via API

```python
import os
import asyncio
import httpx

async def create_neon_branch(branch_name: str, parent_branch: str = "main"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3000/mcp/neon",
            json={
                "jsonrpc": "2.0",
                "method": "create_branch",
                "params": {
                    "project_id": os.getenv("NEON_PROJECT_ID"),
                    "branch_name": branch_name,
                    "parent_branch_id": parent_branch
                },
                "id": 1
            }
        )
        return response.json()

# Usage
result = asyncio.run(create_neon_branch("feature-xyz"))
print(f"Created branch: {result['result']['branch_id']}")
```

### Example: Execute SQL Query

```python
async def query_neon_database(sql: str, branch: str = "main"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3000/mcp/neon",
            json={
                "jsonrpc": "2.0",
                "method": "execute_sql",
                "params": {
                    "project_id": os.getenv("NEON_PROJECT_ID"),
                    "branch_id": branch,
                    "database": "devskyy",
                    "sql": sql
                },
                "id": 1
            }
        )
        return response.json()

# Usage
result = await query_neon_database("SELECT COUNT(*) FROM users")
print(f"User count: {result['result']['rows'][0][0]}")
```

---

## Integration with DevSkyy Features

### Health Monitoring

Neon MCP is integrated with DevSkyy's health checks:

```bash
# Check MCP gateway health
curl http://localhost:3000/health

# Check Neon MCP specifically
curl http://localhost:3000/health/neon
```

### Prometheus Metrics

MCP gateway exports metrics:

```
devskyy_mcp_requests_total{server="neon"}
devskyy_mcp_request_duration_seconds{server="neon"}
devskyy_mcp_errors_total{server="neon"}
```

### Logging

All MCP requests are logged with request IDs:

```json
{
  "timestamp": "2025-11-20T12:00:00Z",
  "level": "INFO",
  "message": "MCP request",
  "server": "neon",
  "method": "create_branch",
  "request_id": "req_xxx",
  "duration_ms": 123
}
```

---

## Troubleshooting

### Issue: "MCP server not responding"

**Solution:**
1. Check environment variables:
   ```bash
   echo $NEON_API_KEY
   echo $NEON_PROJECT_ID
   ```

2. Verify MCP gateway is running:
   ```bash
   docker-compose ps mcp-gateway
   ```

3. Check logs:
   ```bash
   docker-compose logs mcp-gateway
   ```

### Issue: "Authentication failed"

**Solution:**
1. Verify API key is correct in Neon dashboard
2. Check API key has correct permissions
3. Ensure API key is not expired

### Issue: "Project not found"

**Solution:**
1. Verify project ID is correct
2. Check you have access to the project
3. Ensure project is in correct region

### Issue: "Rate limit exceeded"

**Solution:**
1. Neon has rate limits on MCP API
2. Implement retry logic with exponential backoff
3. Consider caching frequently accessed data

---

## Security Best Practices

### 1. API Key Management

✅ **DO:**
- Store API keys in environment variables
- Use different keys for dev/staging/prod
- Rotate keys regularly
- Limit key permissions to minimum required

❌ **DON'T:**
- Commit API keys to git
- Share API keys in chat/email
- Use production keys in development
- Give keys excessive permissions

### 2. Access Control

```python
# Example: Restrict MCP access to admin users only
from security.jwt_auth import require_admin

@router.post("/api/v1/mcp/neon")
async def neon_mcp_proxy(
    request: dict,
    current_user = Depends(require_admin)
):
    # Only admins can use MCP
    return await mcp_gateway.route_request("neon", request)
```

### 3. Request Validation

```python
# Validate SQL queries before execution
def validate_sql_query(sql: str) -> bool:
    dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
    return not any(keyword in sql.upper() for keyword in dangerous_keywords)
```

---

## Performance Optimization

### 1. Connection Pooling

MCP gateway maintains connection pools to Neon:

```python
# Configured in mcp_gateway.py
NEON_POOL_SIZE = 10
NEON_POOL_TIMEOUT = 30
```

### 2. Caching

Cache frequently accessed data:

```python
# For async functions, use async-aware caching (e.g., aiocache or async_lru)
# Note: functools.lru_cache does not work with async functions

from aiocache import cached, Cache
from aiocache.serializers import JsonSerializer

@cached(ttl=300, cache=Cache.MEMORY, serializer=JsonSerializer())
async def get_neon_branches(project_id: str):
    # Cached for 5 minutes (300 seconds)
    return await mcp_client.list_branches(project_id)

# Alternative: Manual caching with dict
_branch_cache = {}

async def get_neon_branches_manual(project_id: str):
    if project_id in _branch_cache:
        return _branch_cache[project_id]
    result = await mcp_client.list_branches(project_id)
    _branch_cache[project_id] = result
    return result
```

### 3. Batch Operations

Batch multiple operations:

```python
# Instead of multiple single queries
# Use batch execution
batch_queries = [
    "SELECT * FROM users WHERE id = 1",
    "SELECT * FROM orders WHERE user_id = 1",
    "SELECT * FROM products WHERE id IN (1,2,3)"
]

result = await mcp_client.execute_batch(batch_queries)
```

---

## Advanced Usage

### 1. Database Branching Workflow

```python
# Create feature branch
feature_branch = await create_neon_branch("feature-user-auth")

# Run migrations on feature branch
await run_migrations(branch_id=feature_branch.id)

# Test on feature branch
await run_integration_tests(branch_id=feature_branch.id)

# Merge to main (manual in Neon dashboard)
# Delete feature branch when done
await delete_neon_branch(feature_branch.id)
```

### 2. Schema Evolution

```python
# Get current schema
schema = await get_neon_schema(branch_id="main")

# Apply schema changes
await execute_sql(
    branch_id="dev",
    sql="ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE"
)

# Test schema changes
await run_schema_tests(branch_id="dev")

# Promote to staging/production
```

### 3. Point-in-Time Recovery

```python
# Restore database to specific timestamp
await restore_database(
    project_id="ep-xxx",
    branch_id="main",
    timestamp="2025-11-20T10:00:00Z"
)
```

---

## Next Steps

1. **Configure Local Claude Desktop:**
   ```bash
   claude mcp add --transport http neon https://mcp.neon.tech/mcp
   ```

2. **Enable MCP Gateway in DevSkyy:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d mcp-gateway
   ```

3. **Test Integration:**
   ```bash
   curl http://localhost:3000/mcp/neon -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"list_branches","id":1}'
   ```

4. **Read Full Documentation:**
   - Neon MCP: https://neon.tech/docs/mcp
   - DevSkyy MCP: `docker/mcp_gateway.py`

---

**Status:** ✅ Configuration Ready
**Last Updated:** 2025-11-20
**Version:** 5.2.0
