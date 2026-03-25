# DevSkyy MCP - Critical Fuchsia Ape Backend Setup

This guide covers setting up `devskyy_mcp.py` to connect to the critical-fuchsia-ape MCP server.

## Quick Start

### 1. Environment Configuration

Create or update `.env` in the project root with your critical-fuchsia-ape credentials:

```bash
# Backend selection
MCP_BACKEND=critical-fuchsia-ape

# Critical Fuchsia Ape Configuration
CRITICAL_FUCHSIA_APE_URL=http://critical-fuchsia-ape:8000
CRITICAL_FUCHSIA_APE_KEY=your-api-key-here
```

### 2. Start DevSkyy MCP Server

```bash
# Install dependencies (if not already done)
pip install -r mcp/requirements.txt

# Start the MCP server pointing to critical-fuchsia-ape
export MCP_BACKEND=critical-fuchsia-ape
export CRITICAL_FUCHSIA_APE_URL="http://critical-fuchsia-ape:8000"
export CRITICAL_FUCHSIA_APE_KEY="your-key"

python devskyy_mcp.py
```

### 3. Claude Desktop Integration

Update `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devskyy-critical-fuchsia-ape": {
      "command": "python",
      "args": ["/absolute/path/to/DevSkyy/devskyy_mcp.py"],
      "env": {
        "MCP_BACKEND": "critical-fuchsia-ape",
        "CRITICAL_FUCHSIA_APE_URL": "http://critical-fuchsia-ape:8000",
        "CRITICAL_FUCHSIA_APE_KEY": "${CRITICAL_FUCHSIA_APE_KEY}"
      }
    }
  }
}
```

## Configuration Details

### Backend Modes

The MCP server supports two backend modes:

| Backend | URL Env Variable | Key Env Variable | Default URL |
|---------|------------------|------------------|-------------|
| `devskyy` (default) | `DEVSKYY_API_URL` | `DEVSKYY_API_KEY` | `http://localhost:8000` |
| `critical-fuchsia-ape` | `CRITICAL_FUCHSIA_APE_URL` | `CRITICAL_FUCHSIA_APE_KEY` | `http://critical-fuchsia-ape:8000` |

### Environment Variables

#### To use critical-fuchsia-ape

```bash
export MCP_BACKEND=critical-fuchsia-ape
export CRITICAL_FUCHSIA_APE_URL=http://critical-fuchsia-ape:8000
export CRITICAL_FUCHSIA_APE_KEY=sk-your-key-here
```

#### To use default DevSkyy backend

```bash
export MCP_BACKEND=devskyy
export DEVSKYY_API_URL=http://localhost:8000
export DEVSKYY_API_KEY=your-key
```

## MCP Configuration Files

### `.mcp.json` Server Entry

The MCP server configuration is defined in `.mcp.json`:

```json
{
  "devskyy-critical-fuchsia-ape": {
    "command": "python",
    "args": ["devskyy_mcp.py"],
    "env": {
      "DEVSKYY_API_URL": "${CRITICAL_FUCHSIA_APE_URL}",
      "DEVSKYY_API_KEY": "${CRITICAL_FUCHSIA_APE_KEY}"
    },
    "description": "DevSkyy MCP Server integrated with critical-fuchsia-ape backend",
    "capabilities": [
      "devskyy_scan_code",
      "devskyy_fix_code",
      "devskyy_self_healing",
      "devskyy_generate_wordpress_theme",
      "devskyy_ml_prediction",
      "devskyy_manage_products",
      "devskyy_dynamic_pricing",
      "devskyy_generate_3d_from_description",
      "devskyy_generate_3d_from_image",
      "devskyy_marketing_campaign",
      "devskyy_multi_agent_workflow",
      "devskyy_system_monitoring",
      "devskyy_list_agents"
    ]
  }
}
```

### Environment Template (mcp/.env.example)

Template variables for critical-fuchsia-ape:

```bash
# Critical Fuchsia Ape Integration (Alternative Backend)
CRITICAL_FUCHSIA_APE_URL=http://critical-fuchsia-ape:8000
CRITICAL_FUCHSIA_APE_KEY=your-critical-fuchsia-ape-key
MCP_BACKEND=devskyy  # Set to 'critical-fuchsia-ape' to use that backend instead
```

## Tools Available

All 13 DevSkyy MCP tools are available when using critical-fuchsia-ape:

1. **devskyy_scan_code** - Code analysis and quality checking
2. **devskyy_fix_code** - Automated code fixing
3. **devskyy_self_healing** - System health monitoring and auto-repair
4. **devskyy_generate_wordpress_theme** - WordPress theme generation
5. **devskyy_ml_prediction** - Machine learning predictions
6. **devskyy_manage_products** - E-commerce product management
7. **devskyy_dynamic_pricing** - ML-powered price optimization
8. **devskyy_generate_3d_from_description** - 3D generation (text-to-3D)
9. **devskyy_generate_3d_from_image** - 3D generation (image-to-3D)
10. **devskyy_marketing_campaign** - Multi-channel marketing automation
11. **devskyy_multi_agent_workflow** - Complex workflow orchestration
12. **devskyy_system_monitoring** - Real-time platform monitoring
13. **devskyy_list_agents** - View all 54 agents

## Switching Between Backends

### Method 1: Environment Variable

```bash
# Switch to critical-fuchsia-ape
export MCP_BACKEND=critical-fuchsia-ape
python devskyy_mcp.py

# Switch back to default
export MCP_BACKEND=devskyy
python devskyy_mcp.py
```

### Method 2: Shell Alias

Add to `~/.zshrc` or `~/.bashrc`:

```bash
alias devskyy-mcp="python /path/to/devskyy_mcp.py"
alias devskyy-mcp-fuchsia="MCP_BACKEND=critical-fuchsia-ape python /path/to/devskyy_mcp.py"
```

### Method 3: Docker Environment

```bash
docker run -e MCP_BACKEND=critical-fuchsia-ape \
           -e CRITICAL_FUCHSIA_APE_URL=http://critical-fuchsia-ape:8000 \
           -e CRITICAL_FUCHSIA_APE_KEY=your-key \
           devskyy-mcp
```

## Troubleshooting

### Connection Issues

If the MCP server cannot connect to critical-fuchsia-ape:

```bash
# 1. Verify environment variables
echo "Backend: $MCP_BACKEND"
echo "URL: $CRITICAL_FUCHSIA_APE_URL"
echo "Key: ${CRITICAL_FUCHSIA_APE_KEY:0:10}..."

# 2. Test connectivity
curl -H "Authorization: Bearer $CRITICAL_FUCHSIA_APE_KEY" \
     "$CRITICAL_FUCHSIA_APE_URL/health"

# 3. Check MCP server logs
python devskyy_mcp.py 2>&1 | grep -i "error\|connect"
```

### API Key Issues

```bash
# Verify API key is set
if [ -z "$CRITICAL_FUCHSIA_APE_KEY" ]; then
  echo "CRITICAL_FUCHSIA_APE_KEY not set"
  export CRITICAL_FUCHSIA_APE_KEY="your-key"
fi
```

### Port/URL Issues

```bash
# Verify the URL is accessible
curl -v "$CRITICAL_FUCHSIA_APE_URL/health"

# Check if port is open
lsof -i :8000  # or your custom port
```

## API Compatibility

The critical-fuchsia-ape backend must support the DevSkyy MCP API contract:

- **Base endpoints**: `/api/v1/*`
- **Authentication**: Bearer token in `Authorization` header
- **Response format**: JSON
- **Error handling**: HTTP status codes + JSON error messages

## Examples

### Switch Backend and Start Server

```bash
#!/bin/bash
# Start with critical-fuchsia-ape
export MCP_BACKEND=critical-fuchsia-ape
export CRITICAL_FUCHSIA_APE_URL="http://critical-fuchsia-ape:8000"
export CRITICAL_FUCHSIA_APE_KEY="$1"  # Pass key as argument

python devskyy_mcp.py
```

### Use with Claude CLI

```bash
# Start MCP server
python devskyy_mcp.py &

# Use with Claude
claude interact --mcp devskyy_mcp
```

## Performance Tuning

### Adjust Timeouts

```bash
# Increase timeout for slow backends
export REQUEST_TIMEOUT=120
python devskyy_mcp.py
```

### Parallel Requests

```bash
# Adjust max concurrent requests
export MAX_CONCURRENT_REQUESTS=10
python devskyy_mcp.py
```

## Documentation

- **MCP Specification**: <https://modelcontextprotocol.io>
- **FastMCP Guide**: <https://gofastmcp.com>
- **DevSkyy Docs**: [See main documentation](../docs/)

## Support

For issues or questions:

1. Check environment variables are set correctly
2. Verify connectivity to critical-fuchsia-ape
3. Review MCP server logs
4. Check the critical-fuchsia-ape API status
5. Open a GitHub issue with error logs

---

**Last Updated**: 2025-12-24
**Version**: 1.0.0
