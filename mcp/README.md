# DevSkyy MCP Subproject

## Overview

This directory contains the Model Context Protocol (MCP) server implementation for the DevSkyy platform. MCP enables advanced agent-to-agent communication and context sharing across the AI ecosystem.

## Structure

```
mcp/
├── requirements.txt          # MCP-specific Python dependencies (isolated)
└── README.md                # This file
```

Additional MCP-related files in root:
- `requirements_mcp.txt` (legacy - being consolidated)
- `Dockerfile.mcp` (MCP-specific Docker image)
- `docker-compose.mcp.yml` (MCP deployment)
- `devskyy_mcp.py` (MCP server implementation)
- `.mcp.json` (MCP configuration)

## Dependencies

The `requirements.txt` file contains MCP-specific dependencies:

### MCP Framework
- **fastmcp**: >=0.1.0 (FastMCP framework)
- **mcp**: 1.21.0 (Model Context Protocol core)
- **claude-agent-sdk**: 0.1.6 (Anthropic Agent SDK)

### Core Infrastructure
- **FastAPI**: 0.119.0
- **Uvicorn**: 0.38.0
- **Pydantic**: >=2.7.0

### AI Integration
- **Anthropic**: 0.69.0 (Claude API)
- **OpenAI**: 2.7.2 (GPT API)

### Observability
- **logfire[fastapi]**: 4.14.2 (OpenTelemetry)
- **rich**: >=13.0.0 (Enhanced console)
- **structlog**: 24.4.0 (Structured logging)

### Security
- **python-jose[cryptography]**: >=3.3.0 (JWT)
- **PyJWT**: 2.10.1
- **cryptography**: 46.0.3

**Excluded**: Heavy ML libraries (torch, transformers) - use AI API endpoints instead

## What is MCP?

Model Context Protocol (MCP) is an open standard that enables:
- **Context Sharing**: Share context between AI agents and applications
- **Tool Integration**: Expose tools and capabilities to LLMs
- **Resource Access**: Provide structured access to data sources
- **Agent Communication**: Enable multi-agent collaboration

## MCP Server Features

### 1. Context Management
```python
# Share context across agents
await mcp_server.add_context(
    context_id="user_session_123",
    data={"preferences": {...}, "history": [...]}
)
```

### 2. Tool Registration
```python
# Register tools for LLM access
@mcp_server.tool()
async def search_products(query: str, filters: dict):
    """Search fashion products with advanced filters"""
    return await product_search(query, filters)
```

### 3. Resource Providers
```python
# Provide structured data access
@mcp_server.resource("products")
async def get_products():
    """Fetch product catalog"""
    return await database.get_all_products()
```

### 4. Agent Orchestration
```python
# Coordinate multiple AI agents
orchestrator = MCPOrchestrator()
result = await orchestrator.execute_workflow(
    agents=["product_analyzer", "pricing_optimizer"],
    task="optimize_product_listing",
    context=product_data
)
```

## Installation

### For MCP Development
```bash
# Install MCP dependencies
pip install -r mcp/requirements.txt
```

### Using Docker
```bash
# Build MCP server container
docker build -t devskyy-mcp:latest -f Dockerfile.mcp .

# Run MCP server
docker run -p 8000:8000 -p 3000:3000 devskyy-mcp:latest
```

### Using Docker Compose
```bash
# Start MCP services
docker-compose -f docker-compose.mcp.yml up -d
```

## Configuration

### MCP Configuration File (`.mcp.json`)
```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python",
      "args": ["devskyy_mcp.py"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key

# Optional
MCP_PORT=3000
MCP_HOST=0.0.0.0
LOG_LEVEL=INFO
```

## Usage

### Starting the MCP Server
```bash
# Run directly
python devskyy_mcp.py

# Or via uvicorn
uvicorn devskyy_mcp:app --host 0.0.0.0 --port 3000
```

### Connecting to MCP Server

#### From Claude Desktop
1. Copy `.mcp.json` to Claude Desktop config directory
2. Restart Claude Desktop
3. MCP tools will appear in Claude interface

#### From Python Code
```python
from mcp import Client

client = Client("http://localhost:3000")

# Use MCP tools
result = await client.call_tool(
    "search_products",
    query="luxury dresses",
    filters={"price_min": 100}
)

# Access resources
products = await client.get_resource("products")
```

#### From Claude Agent SDK
```python
from claude_agent_sdk import Agent

agent = Agent(
    mcp_servers=["http://localhost:3000"],
    tools=["search_products", "optimize_pricing"]
)

response = await agent.execute(
    prompt="Find and optimize pricing for luxury evening dresses"
)
```

## MCP Server Endpoints

### Tools
- `search_products`: Search product catalog
- `optimize_pricing`: Dynamic pricing optimization
- `analyze_trends`: Fashion trend analysis
- `generate_content`: AI content generation
- `customer_segment`: Customer segmentation

### Resources
- `products`: Product catalog
- `customers`: Customer database
- `orders`: Order history
- `analytics`: Business analytics
- `inventory`: Inventory levels

### Context
- User sessions
- Shopping cart state
- Recommendation history
- A/B test assignments

## Testing

### Run MCP Tests
```bash
# Test MCP server
pytest tests/mcp/ -v

# Test with coverage
pytest tests/mcp/ --cov=mcp --cov-report=html
```

### Manual Testing
```bash
# Health check
curl http://localhost:3000/health

# List available tools
curl http://localhost:3000/tools

# List resources
curl http://localhost:3000/resources
```

## CI/CD Integration

MCP workflows are automated via GitHub Actions:
- Workflow: `.github/workflows/mcp.yml`
- Tests: Automated on push/PR
- Deployment: Docker image builds
- Monitoring: Health checks and metrics

## Deployment

### Production Deployment
```bash
# Build production image
docker build -t devskyy-mcp:prod -f Dockerfile.mcp .

# Deploy to cloud
docker push devskyy-mcp:prod

# Run in production
docker run -d \
  -p 3000:3000 \
  -e DEVSKYY_ENV=production \
  -e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
  devskyy-mcp:prod
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devskyy-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: devskyy-mcp
  template:
    spec:
      containers:
      - name: mcp-server
        image: devskyy-mcp:prod
        ports:
        - containerPort: 3000
        env:
        - name: DEVSKYY_ENV
          value: production
```

## Monitoring

### Health Checks
```bash
# MCP server health
curl http://localhost:3000/health

# Prometheus metrics
curl http://localhost:3000/metrics
```

### Observability
- OpenTelemetry traces (via logfire)
- Structured logs (via structlog)
- Prometheus metrics
- Health status monitoring

## Security

### Authentication
```python
# API key authentication
headers = {
    "Authorization": f"Bearer {MCP_API_KEY}"
}
```

### Rate Limiting
```python
# Async throttle for API calls
from asyncio_throttle import Throttler

throttler = Throttler(rate_limit=10, period=1.0)
```

### Encryption
- TLS/SSL for API communication
- JWT tokens for session management
- Encrypted context storage

## Best Practices

1. **Tool Design**: Make tools atomic and composable
2. **Context Management**: Clear context scope and lifecycle
3. **Error Handling**: Graceful degradation on failures
4. **Rate Limiting**: Respect API rate limits
5. **Caching**: Cache expensive operations
6. **Logging**: Structured logs for debugging
7. **Monitoring**: Track tool usage and performance
8. **Security**: Validate all inputs, sanitize outputs

## Troubleshooting

### MCP Server Not Starting
```bash
# Check port availability
lsof -i :3000

# Check logs
docker logs <container-id>

# Verify dependencies
pip check
```

### Connection Issues
```bash
# Test connectivity
curl http://localhost:3000/health

# Check firewall rules
sudo ufw status

# Verify environment variables
env | grep MCP
```

### Tool Execution Failures
```bash
# Check tool registration
curl http://localhost:3000/tools

# Verify API keys
echo $ANTHROPIC_API_KEY

# Enable debug logging
export LOG_LEVEL=DEBUG
```

## Related Documentation

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- [DevSkyy MCP Guide](/MCP_ENHANCED_GUIDE.md)
- [MCP Deployment](/MCP_DEPLOYMENT_SUCCESS.md)
- [MCP Configuration](/MCP_CONFIGURATION_GUIDE.md)

## Examples

See the `/examples` directory for:
- Tool implementation examples
- Resource provider examples
- Agent orchestration patterns
- Integration samples
