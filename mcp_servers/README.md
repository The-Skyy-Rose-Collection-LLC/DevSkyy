# DevSkyy MCP Servers

Model Context Protocol (MCP) servers for the DevSkyy Enterprise Platform.

## Overview

This directory contains MCP server implementations that expose DevSkyy's capabilities to AI assistants and other MCP-compatible clients.

## Available Servers

### 1. OpenAI MCP Server (`openai_server.py`)

**Purpose**: Integration with OpenAI models (GPT-4o, GPT-4o-mini, o1-preview)

**Features**:

- Text completion and generation
- Vision analysis (GPT-4o)
- Code generation with DevSkyy best practices
- Function calling and structured outputs
- Model selection recommendations
- Agent orchestration

**Usage**:

```bash
python openai_server.py
```

**Environment Variables**:

- `OPENAI_API_KEY` - OpenAI API key (required)
- `DEVSKYY_API_URL` - DevSkyy API endpoint (default: <http://localhost:8000>)
- `DEVSKYY_API_KEY` - DevSkyy API key

### 2. DevSkyy Main MCP Server (`../devskyy_mcp.py`)

**Purpose**: Access to DevSkyy's 54-agent ecosystem

**Features**:

- WordPress/WooCommerce automation
- SEO optimization
- Content generation
- Social media management
- Analytics and reporting
- Security scanning
- Database operations
- ML predictions

**Usage**:

```bash
python ../devskyy_mcp.py
```

**Environment Variables**:

- `DEVSKYY_API_URL` - DevSkyy API endpoint (required)
- `DEVSKYY_API_KEY` - DevSkyy API key (required)

## Installation

### Quick Setup

Run the automated setup script:

```bash
./scripts/setup_mcp.sh
```

### Manual Setup

1. **Install Python dependencies**:

```bash
pip install -r mcp/requirements.txt
```

1. **Configure environment variables**:

```bash
export OPENAI_API_KEY="sk-your-key"
export DEVSKYY_API_KEY="your-key"
```

1. **Test servers**:

```bash
python mcp/openai_server.py
python devskyy_mcp.py
```

## Claude Desktop Integration

### Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devskyy-openai": {
      "command": "python",
      "args": ["/absolute/path/to/DevSkyy/mcp/openai_server.py"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "DEVSKYY_API_URL": "http://localhost:8000",
        "DEVSKYY_API_KEY": "${DEVSKYY_API_KEY}"
      }
    },
    "devskyy-main": {
      "command": "python",
      "args": ["/absolute/path/to/DevSkyy/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_URL": "http://localhost:8000",
        "DEVSKYY_API_KEY": "${DEVSKYY_API_KEY}"
      }
    }
  }
}
```

### Restart Claude Desktop

After configuration, restart Claude Desktop to load the MCP servers.

## Development

### Creating Custom MCP Servers

Use FastMCP to create custom servers:

```python
from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("my_custom_server")

@mcp.tool()
async def my_tool(param: str = Field(description="Parameter")) -> str:
    """Tool description"""
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run()
```

### Testing

Test MCP servers manually:

```bash
# Test OpenAI server
python mcp/openai_server.py

# Test main server
python devskyy_mcp.py

# Test with MCP client
npx @modelcontextprotocol/inspector python mcp/openai_server.py
```

## Troubleshooting

### Server Not Starting

```bash
# Check Python version (3.11+ required)
python3 --version

# Install dependencies
pip install -r mcp/requirements.txt

# Check for errors
python mcp/openai_server.py --help
```

### Environment Variables Not Loading

```bash
# Verify variables are set
echo $OPENAI_API_KEY
echo $DEVSKYY_API_KEY

# Add to shell profile
echo 'export OPENAI_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

### Permission Errors

```bash
# Make scripts executable
chmod +x mcp/openai_server.py
chmod +x devskyy_mcp.py
```

## Documentation

- **Full Configuration Guide**: `../docs/MCP_CONFIGURATION_GUIDE.md`
- **MCP Specification**: <https://modelcontextprotocol.io/specification/2025-06-18>
- **FastMCP Documentation**: <https://gofastmcp.com>
- **DevSkyy Documentation**: `../docs/`

## Support

For issues or questions:

1. Check logs: `~/Library/Logs/Claude/mcp*.log`
2. Review documentation: `docs/MCP_CONFIGURATION_GUIDE.md`
3. Test servers manually
4. GitHub Issues: <https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues>

---

**Version**: 1.0.0
**Last Updated**: 2025-12-16
**Maintained by**: The Skyy Rose Collection LLC
