---
name: DevSkyy MCP Server Development
description: This skill should be used when the user asks to "create MCP server", "add MCP tools", "implement FastMCP endpoints", "expose MCP resources", "configure MCP servers", or mentions Model Context Protocol, tool schemas, or MCP integration patterns.
version: 1.0.0
---

# DevSkyy MCP Server Development Skill

Use this skill when developing, extending, or troubleshooting MCP (Model Context Protocol) servers for DevSkyy.

## When to Use This Skill

Invoke this skill when the user:

- Wants to create a new MCP server or tools
- Needs to expose DevSkyy capabilities via MCP
- Asks about MCP tool schemas or resource definitions
- Requests MCP server configuration or deployment
- Mentions FastMCP, tool annotations, or MCP client integration

## DevSkyy MCP Architecture

### Current MCP Servers

1. **Main MCP Server** (`devskyy_mcp.py`):
   - 13 tools for agent operations
   - Code scanning, fixing, theme generation
   - ML predictions, product management, pricing
   - 3D generation (text & image prompts)
   - Marketing campaigns, multi-agent workflows
   - System monitoring, agent listing

2. **RAG MCP Server** (`mcp/rag_server.py`):
   - Semantic search across DevSkyy docs
   - Document ingestion and chunking
   - Context retrieval with similarity thresholds
   - Query rewriting strategies (zero_shot, few_shot, sub_queries, step_back, hyde)
   - Source management and statistics

3. **WooCommerce MCP Server** (`mcp/woocommerce_mcp.py`):
   - Product CRUD operations
   - Order management
   - Customer data access
   - Inventory synchronization

## FastMCP Pattern

### Basic MCP Tool Definition

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional

mcp = FastMCP("devskyy")

class ToolInput(BaseModel):
    """Input schema with validation."""
    param1: str = Field(..., description="Parameter description")
    param2: Optional[int] = Field(None, description="Optional parameter")

@mcp.tool(annotations={
    "readOnlyHint": True,  # Safe read-only operation
    "idempotentHint": True  # Same input always produces same output
})
async def my_tool(input: ToolInput) -> str:
    """Tool description for Claude to understand when to use it."""
    result = await process(input.param1, input.param2)
    return f"Result: {result}"
```

### Tool Categories & Severity

```python
from runtime.tools import ToolCategory, SeverityLevel

# Categories
CATEGORIES = [
    ToolCategory.CONTENT,      # CMS, documentation
    ToolCategory.COMMERCE,     # E-commerce operations
    ToolCategory.MEDIA,        # Images, 3D, video
    ToolCategory.COMMUNICATION,# Email, notifications
    ToolCategory.ANALYTICS,    # Metrics, reporting
    ToolCategory.INTEGRATION,  # External APIs
    ToolCategory.SYSTEM,       # Infrastructure
    ToolCategory.AI,           # ML/AI operations
    ToolCategory.OPERATIONS,   # DevOps, deployment
    ToolCategory.SECURITY      # Auth, encryption
]

# Severity Levels
SEVERITY = [
    SeverityLevel.READ_ONLY,   # No modifications
    SeverityLevel.LOW,         # Minor changes
    SeverityLevel.MEDIUM,      # Moderate impact
    SeverityLevel.HIGH,        # Significant changes
    SeverityLevel.DESTRUCTIVE  # Irreversible operations
]
```

### MCP Resource Definition

```python
@mcp.resource("resource://path/{id}")
async def get_resource(id: str) -> str:
    """Expose data as MCP resource."""
    data = await fetch_data(id)
    return json.dumps(data)
```

## DevSkyy MCP Tools Reference

### Main MCP Server Tools (`devskyy_mcp.py`)

1. **`devskyy_scan_code`**: Static analysis of codebase
2. **`devskyy_fix_code`**: Auto-fix code issues
3. **`devskyy_generate_wordpress_theme`**: Theme scaffolding
4. **`devskyy_ml_prediction`**: ML model inference
5. **`devskyy_manage_products`**: WooCommerce product ops
6. **`devskyy_dynamic_pricing`**: ML-based pricing
7. **`devskyy_generate_3d_from_description`**: Text-to-3D
8. **`devskyy_generate_3d_from_image`**: Image-to-3D
9. **`devskyy_marketing_campaign`**: Campaign generation
10. **`devskyy_multi_agent_workflow`**: Orchestration
11. **`devskyy_system_monitoring`**: Health checks
12. **`devskyy_list_agents`**: Agent discovery

### RAG MCP Server Tools (`mcp/rag_server.py`)

1. **`rag_query`**: Semantic search
2. **`rag_ingest`**: Document indexing
3. **`rag_get_context`**: Context retrieval
4. **`rag_query_rewrite`**: Query optimization
5. **`rag_list_sources`**: Source enumeration
6. **`rag_stats`**: Vector store statistics

## Creating New MCP Tools

### Step 1: Define Input Schema

```python
class Generate3DInput(BaseModel):
    prompt: str = Field(..., description="3D model description")
    style: str = Field("realistic", description="Style: realistic|cartoon|low_poly")
    output_format: str = Field("glb", description="Format: glb|obj|fbx")
```

### Step 2: Implement Tool Logic

```python
@mcp.tool(annotations={"readOnlyHint": False, "idempotentHint": False})
async def generate_3d_asset(input: Generate3DInput) -> dict:
    """Generate 3D asset using Tripo3D API.

    This tool creates 3D models from text descriptions using AI.
    Use when the user asks to create 3D models, assets, or meshes.
    """
    # 1. Validate input
    if not input.prompt:
        raise ValueError("Prompt required")

    # 2. Call Tripo3D agent
    from agents.tripo_agent import TripoAgent
    agent = TripoAgent(tool_registry=get_tool_registry())

    result = await agent.generate_from_text(
        prompt=input.prompt,
        style=input.style,
        output_format=input.output_format
    )

    # 3. Return structured result
    return {
        "model_url": result.url,
        "format": input.output_format,
        "metadata": result.metadata
    }
```

### Step 3: Register with ToolRegistry

```python
from orchestration.tool_registry import ToolRegistry, ToolSpec

tool_spec = ToolSpec(
    name="generate_3d_asset",
    description="Generate 3D models from text",
    schema={
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "style": {"type": "string"},
            "output_format": {"type": "string"}
        },
        "required": ["prompt"]
    },
    category=ToolCategory.MEDIA,
    severity=SeverityLevel.MEDIUM,
    permissions=["tripo_api"],
    timeout_ms=30000
)

registry = ToolRegistry()
registry.register(tool_spec)
```

## MCP Server Configuration

### Claude Desktop Config

```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python",
      "args": ["/path/to/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_KEY": "sk-...",  # pragma: allowlist secret
        "TRIPO_API_KEY": "...",
        "WORDPRESS_URL": "https://..."
      }
    },
    "devskyy-rag": {
      "command": "python",
      "args": ["/path/to/mcp/rag_server.py"],
      "env": {
        "VECTOR_DB_PATH": "./data/vectordb"
      }
    }
  }
}
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY devskyy_mcp.py .
COPY agents/ agents/
COPY orchestration/ orchestration/

EXPOSE 8000
CMD ["python", "devskyy_mcp.py"]
```

## Tool Export Formats

MCP servers can export tools in multiple formats:

```python
# OpenAI Functions format
registry.to_openai_functions()

# Anthropic Tools format
registry.to_anthropic_tools()

# MCP Tools format
registry.to_mcp_tools()
```

## Testing MCP Tools

```python
import pytest
from mcp.client import Client

@pytest.mark.asyncio
async def test_mcp_tool():
    client = Client("http://localhost:8000")

    result = await client.call_tool("generate_3d_asset", {
        "prompt": "modern chair design",
        "style": "realistic"
    })

    assert result["model_url"]
    assert result["format"] == "glb"
```

## File Locations

- **Main MCP**: `devskyy_mcp.py`
- **RAG MCP**: `mcp/rag_server.py`
- **WooCommerce MCP**: `mcp/woocommerce_mcp.py`
- **Tool Runtime**: `runtime/tools.py`
- **Tool Registry**: `orchestration/tool_registry.py`

## Best Practices

1. **Input Validation**: Always use Pydantic models
2. **Error Handling**: Raise descriptive exceptions
3. **Documentation**: Clear tool descriptions for Claude
4. **Timeouts**: Set appropriate timeouts for long operations
5. **Permissions**: Specify required permissions in ToolSpec
6. **Idempotency**: Mark read-only and idempotent operations
7. **Testing**: Write tests for all MCP tools

## Common Patterns

### Pattern 1: Agent-Backed Tool

```python
@mcp.tool()
async def commerce_operation(input: CommerceInput) -> dict:
    from agents.commerce_agent import CommerceAgent
    agent = CommerceAgent(tool_registry=get_registry())
    return await agent.execute_task(input.operation)
```

### Pattern 2: Direct API Call

```python
@mcp.tool()
async def external_api_call(input: APIInput) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            API_URL,
            json=input.dict(),
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        return response.json()
```

### Pattern 3: RAG-Enhanced Tool

```python
@mcp.tool()
async def rag_assisted_generation(input: RAGInput) -> str:
    # 1. Retrieve context
    context = await rag_query(input.query)

    # 2. Generate with context
    result = await llm_router.generate({
        "prompt": input.prompt,
        "context": context
    })

    return result
```

## Next Steps

1. **Review** existing MCP servers in repo root and `mcp/` directory
2. **Understand** FastMCP API and tool annotations
3. **Plan** new tools or resource endpoints needed
4. **Implement** following DevSkyy patterns
5. **Test** with MCP client or Claude Desktop
6. **Document** tool usage in `docs/mcp/`
7. **Deploy** via Docker or Vercel serverless functions

## References

See `references/` directory for:

- MCP specification deep dive
- Tool schema patterns
- Security best practices
- Performance optimization
- Claude Desktop integration
- Multi-server orchestration
