# DevSkyy MCP Server Usage Guide

**Status:** ✅ Production Ready
**Protocol:** Model Context Protocol (MCP) v1.21.0
**Transport:** Server-Sent Events (SSE)
**Endpoint:** `GET /mcp/sse`

---

## Overview

DevSkyy exposes 5 AI-powered tools via standard MCP protocol for external client access.

**WHY:** Enable external tools, IDEs, and agents to use DevSkyy's AI capabilities
**HOW:** Official MCP SDK with SSE transport over FastAPI
**IMPACT:** Standardized integration with any MCP-compatible client

---

## Quick Start

### 1. Connect via MCP Client

```bash
# Using claude-agent-sdk
mcp connect http://localhost:8000/mcp/sse
```

### 2. List Available Tools

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async def list_tools():
    async with sse_client("http://localhost:8000/mcp/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools:
                print(f"- {tool.name}: {tool.description}")

# Output:
# - brand_intelligence_reviewer: Reviews content for brand consistency...
# - seo_marketing_reviewer: Reviews content for SEO effectiveness...
# - security_compliance_reviewer: Reviews content for security issues...
# - post_categorizer: Categorizes WordPress posts using AI...
# - product_seo_optimizer: Optimizes WooCommerce product titles...
```

### 3. Invoke a Tool

```python
async def invoke_tool():
    async with sse_client("http://localhost:8000/mcp/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Invoke brand intelligence reviewer
            result = await session.call_tool(
                name="brand_intelligence_reviewer",
                arguments={
                    "title": "10 Ways to Boost Your Productivity",
                    "content": "In today's fast-paced world...",
                    "brand_config": {
                        "keywords": ["productivity", "efficiency"],
                        "tone": "professional",
                        "min_word_count": 600
                    }
                }
            )

            print(result.content[0].text)
```

---

## Available Tools

### 1. Brand Intelligence Reviewer

**Tool Name:** `brand_intelligence_reviewer`
**Category:** Content Review
**Purpose:** Analyzes content for brand consistency, tone, and quality standards

**Input Schema:**
```json
{
  "title": "string (required)",
  "content": "string (required)",
  "keywords": ["string"],
  "word_count": "integer",
  "brand_config": {
    "keywords": ["string"],
    "tone": "professional|casual|friendly|formal|conversational",
    "min_word_count": "integer"
  }
}
```

**Output Schema:**
```json
{
  "decision": "approved|minor_issue|major_issue",
  "confidence": 0.0-1.0,
  "feedback": "string",
  "issues_found": ["string"],
  "suggestions": ["string"],
  "reasoning": "string"
}
```

**Example:**
```python
result = await session.call_tool(
    name="brand_intelligence_reviewer",
    arguments={
        "title": "The Future of AI in Marketing",
        "content": "Artificial intelligence is revolutionizing...",
        "brand_config": {
            "keywords": ["AI", "marketing", "automation"],
            "tone": "professional",
            "min_word_count": 800
        }
    }
)
```

---

### 2. SEO Marketing Reviewer

**Tool Name:** `seo_marketing_reviewer`
**Category:** Content Review
**Purpose:** Analyzes content for SEO effectiveness and keyword optimization

**Input Schema:**
```json
{
  "title": "string (required)",
  "content": "string (required)",
  "meta_description": "string (required)",
  "keywords": ["string"]
}
```

**Output Schema:**
```json
{
  "decision": "approved|minor_issue|major_issue",
  "confidence": 0.0-1.0,
  "feedback": "string",
  "issues_found": ["string"],
  "suggestions": ["string"],
  "seo_score": 0.0-100.0,
  "keyword_density": {"keyword": "percentage"}
}
```

**Example:**
```python
result = await session.call_tool(
    name="seo_marketing_reviewer",
    arguments={
        "title": "10 SEO Tips for 2025",
        "content": "Search engine optimization continues to evolve...",
        "meta_description": "Learn the latest SEO strategies for 2025",
        "keywords": ["SEO", "search optimization", "ranking"]
    }
)
```

---

### 3. Security Compliance Reviewer

**Tool Name:** `security_compliance_reviewer`
**Category:** Content Review
**Purpose:** Scans content for security issues, PII exposure, and compliance violations

**Input Schema:**
```json
{
  "content": "string (required)",
  "compliance_standards": ["GDPR|CCPA|HIPAA|PCI-DSS|SOC2"]
}
```

**Output Schema:**
```json
{
  "decision": "approved|minor_issue|major_issue",
  "confidence": 0.0-1.0,
  "feedback": "string",
  "issues_found": ["string"],
  "security_alerts": ["string"],
  "pii_detected": ["string"],
  "compliance_violations": ["string"]
}
```

**Example:**
```python
result = await session.call_tool(
    name="security_compliance_reviewer",
    arguments={
        "content": "Contact us at john.doe@example.com or call 555-1234",
        "compliance_standards": ["GDPR", "CCPA"]
    }
)
```

---

### 4. WordPress Post Categorizer

**Tool Name:** `post_categorizer`
**Category:** WordPress Automation
**Purpose:** Intelligently categorizes WordPress posts using AI

**Input Schema:**
```json
{
  "post_title": "string (required)",
  "post_content": "string (optional)",
  "available_categories": [
    {
      "id": "integer",
      "name": "string",
      "slug": "string",
      "description": "string"
    }
  ]
}
```

**Output Schema:**
```json
{
  "suggested_category_id": "integer",
  "suggested_category_name": "string",
  "confidence": 0.0-1.0,
  "reasoning": "string",
  "alternative_categories": [
    {
      "id": "integer",
      "name": "string",
      "confidence": 0.0-1.0
    }
  ]
}
```

**Example:**
```python
result = await session.call_tool(
    name="post_categorizer",
    arguments={
        "post_title": "5 Ways to Improve Your Python Code",
        "available_categories": [
            {"id": 1, "name": "Programming", "slug": "programming", "description": ""},
            {"id": 2, "name": "Tutorials", "slug": "tutorials", "description": ""},
            {"id": 3, "name": "News", "slug": "news", "description": ""}
        ]
    }
)
```

---

### 5. WooCommerce Product SEO Optimizer

**Tool Name:** `product_seo_optimizer`
**Category:** E-commerce Automation
**Purpose:** Optimizes WooCommerce product titles, descriptions, and metadata for SEO

**Input Schema:**
```json
{
  "product_id": "integer (required)",
  "product_data": {
    "title": "string (required)",
    "description": "string (required)",
    "short_description": "string",
    "categories": ["string"],
    "price": "number",
    "sku": "string"
  },
  "target_keywords": ["string"]
}
```

**Output Schema:**
```json
{
  "optimized_title": "string",
  "optimized_description": "string",
  "optimized_short_description": "string",
  "suggested_meta_description": "string",
  "seo_score": 0.0-100.0,
  "improvements_made": ["string"],
  "keyword_integration": {"keyword": "count"}
}
```

**Example:**
```python
result = await session.call_tool(
    name="product_seo_optimizer",
    arguments={
        "product_id": 123,
        "product_data": {
            "title": "Blue Widget",
            "description": "A widget that is blue",
            "price": 29.99,
            "sku": "BW-001"
        },
        "target_keywords": ["blue widget", "premium widget", "durable"]
    }
)
```

---

## Authentication

**Current:** JWT authentication via FastAPI middleware
**Header:** `Authorization: Bearer YOUR_JWT_TOKEN`

**Example:**
```bash
curl -X GET http://localhost:8000/mcp/sse \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## Architecture

### Hybrid Approach

**Internal (DevSkyy):** Custom MCP client with 98% token reduction
```
FastAPI Routes → MCPToolClient → On-demand loading → Anthropic Claude
```

**External (MCP Clients):** Standard MCP protocol
```
External Client → /mcp/sse → DevSkyyMCPServer → MCPToolClient → Claude
```

**Benefits:**
- **98% token reduction** via on-demand loading (150K → 2K tokens)
- **Standard compliance** for external integration
- **Best of both worlds** - efficiency + compatibility

### Observability

All requests traced with Logfire:
- Tool invocations logged with span IDs
- Token usage tracked (input/output/total)
- Error tracking with full context
- Performance metrics (P95 latency)

**View traces:**
```bash
# Logfire dashboard
logfire view devskyy-platform
```

---

## Performance

**Target SLOs:**
- P95 latency: < 200ms (endpoint overhead)
- AI invocation: 2-5 seconds (depends on model)
- Token usage: 2K-5K per tool call (98% reduction from 150K)

**Rate Limits:**
- 100 requests/minute per user
- 1000 requests/hour per user

---

## Error Handling

**Standard MCP Error Format:**
```json
{
  "error": "Tool execution failed: Missing required field 'title'",
  "tool": "brand_intelligence_reviewer",
  "timestamp": "2025-11-10T15:30:45Z"
}
```

**Common Error Codes:**
- `TOOL_NOT_FOUND` - Tool name not recognized
- `VALIDATION_ERROR` - Input schema validation failed
- `EXECUTION_ERROR` - Tool execution failed (AI error)
- `AUTH_ERROR` - Authentication failed

---

## Integration Examples

### Python Client

```python
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    async with sse_client("http://localhost:8000/mcp/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Available tools: {len(tools)}")

            # Invoke tool
            result = await session.call_tool(
                name="brand_intelligence_reviewer",
                arguments={...}
            )
            print(result.content[0].text)

asyncio.run(main())
```

### TypeScript/Node.js Client

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';

const transport = new SSEClientTransport(
  new URL('http://localhost:8000/mcp/sse')
);

const client = new Client({
  name: 'my-app',
  version: '1.0.0'
}, {
  capabilities: {}
});

await client.connect(transport);

// List tools
const tools = await client.listTools();
console.log(`Available tools: ${tools.tools.length}`);

// Invoke tool
const result = await client.callTool({
  name: 'brand_intelligence_reviewer',
  arguments: {...}
});

console.log(result.content);
```

### Claude Desktop Integration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "devskyy": {
      "url": "http://localhost:8000/mcp/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer YOUR_JWT_TOKEN"
      }
    }
  }
}
```

---

## Testing

### Local Development

```bash
# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test endpoint availability
curl http://localhost:8000/mcp/sse

# Expected: SSE stream starts
```

### Integration Tests

```python
# tests/test_mcp_server_integration.py
import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

@pytest.mark.asyncio
async def test_mcp_server_list_tools():
    async with sse_client("http://localhost:8000/mcp/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools) == 5

@pytest.mark.asyncio
async def test_brand_reviewer_tool():
    async with sse_client("http://localhost:8000/mcp/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                name="brand_intelligence_reviewer",
                arguments={
                    "title": "Test Post",
                    "content": "Test content",
                    "brand_config": {"tone": "professional", "min_word_count": 100}
                }
            )
            assert result.content[0].type == "text"
```

---

## Deployment

### Production Configuration

**Environment Variables:**
```bash
# Anthropic API Key (required)
ANTHROPIC_API_KEY=sk-ant-...

# Logfire (optional, for observability)
LOGFIRE_TOKEN=...
LOGFIRE_PROJECT_NAME=devskyy-production

# MCP Configuration
MCP_SERVER_ENABLED=true
MCP_SCHEMA_PATH=/app/config/mcp/mcp_tool_calling_schema.json
```

### Docker Deployment

```dockerfile
# Dockerfile already includes:
# - FastAPI server
# - MCP server endpoint
# - All dependencies

# Start container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e LOGFIRE_TOKEN=$LOGFIRE_TOKEN \
  devskyy:latest
```

### Health Check

```bash
# Check MCP server status
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "mcp_server": "active",
  "tools_available": 5
}
```

---

## Monitoring

### Logfire Observability

All MCP operations are traced:

```python
# View in Logfire dashboard
with logfire.span("mcp_tool_invocation") as span:
    span.set_attribute("tool_name", "brand_intelligence_reviewer")
    span.set_attribute("input_tokens", 1500)
    span.set_attribute("output_tokens", 800)
```

**Key Metrics:**
- Tool invocation count per tool
- Average token usage per tool
- P50/P95/P99 latency
- Error rate by tool
- Authentication failures

---

## Security

**Best Practices:**
1. ✅ JWT authentication required
2. ✅ RBAC: Admin/Developer roles only
3. ✅ Rate limiting (100/min, 1000/hour)
4. ✅ Input validation via Pydantic schemas
5. ✅ Output validation via MCP schemas
6. ✅ Audit logging for all tool invocations
7. ✅ No secrets in code (environment variables)
8. ✅ TLS/HTTPS in production

**Compliance:**
- GDPR: PII detection in security_compliance_reviewer
- SOC2: Full audit trail via Logfire
- Truth Protocol: All inputs/outputs validated

---

## Troubleshooting

### Common Issues

**1. Connection Refused**
```bash
# Check server is running
curl http://localhost:8000/health

# Check MCP endpoint
curl http://localhost:8000/mcp/sse
```

**2. Authentication Failed**
```bash
# Verify JWT token
curl http://localhost:8000/mcp/sse \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**3. Tool Not Found**
```python
# List available tools first
tools = await session.list_tools()
print([t.name for t in tools])
```

**4. Validation Error**
```python
# Check input schema
result = await session.call_tool(
    name="brand_intelligence_reviewer",
    arguments={
        "title": "...",      # required
        "content": "...",    # required
        "brand_config": {...} # required
    }
)
```

---

## Support

**Documentation:**
- Main docs: `/docs/MCP_ARCHITECTURE_ANALYSIS.md`
- Server implementation: `/services/mcp_server.py`
- Client implementation: `/services/mcp_client.py`
- Tool schemas: `/config/mcp/mcp_tool_calling_schema.json`

**Issues:**
- GitHub Issues: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues
- Tag: `mcp-server`

**Status:**
- ✅ Production ready
- ✅ 5 tools exposed
- ✅ Full observability
- ✅ Comprehensive testing

---

## Roadmap

**Phase 1: Current (Complete)**
- ✅ MCP server with 5 tools
- ✅ SSE transport
- ✅ JWT authentication
- ✅ Logfire observability

**Phase 2: Next (Q1 2025)**
- [ ] Additional tools (15+ planned)
- [ ] WebSocket transport option
- [ ] Streaming responses
- [ ] Tool composition/chaining

**Phase 3: Future (Q2 2025)**
- [ ] Custom tool registration API
- [ ] Multi-tenancy support
- [ ] Advanced rate limiting
- [ ] Tool marketplace

---

**Last Updated:** 2025-11-10
**Version:** 1.0.0
**Status:** ✅ Production Ready
