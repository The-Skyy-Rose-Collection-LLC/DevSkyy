# OpenAI MCP Server for DevSkyy

Model Context Protocol (MCP) server implementation specifically optimized for OpenAI's models (GPT-4o, GPT-4o-mini, o1-preview).

## Overview

This server exposes DevSkyy's AI capabilities as MCP tools that can be used by OpenAI's API, Claude Desktop, or any MCP-compatible client.

## Features

- ✅ **OpenAI Model Integration**: GPT-4o, GPT-4o-mini, o1-preview
- ✅ **Function Calling**: Structured outputs and tool use
- ✅ **Vision Capabilities**: Image analysis with GPT-4o/4o-mini
- ✅ **Code Generation**: Language-specific code with docs and tests
- ✅ **DevSkyy Agents**: Access to 6 core specialized AI agents
- ✅ **WordPress Automation**: Theme generation and management
- ✅ **E-commerce Tools**: Product management and pricing

## Installation

### Requirements

- Python 3.11+
- OpenAI API key
- DevSkyy API key (for agent integration)

### Install Dependencies

```bash
pip install fastmcp httpx pydantic openai python-jose[cryptography]
```

Or using the project's requirements:

```bash
pip install -e ".[all]"
```

## Configuration

Set the required environment variables:

```bash
# Required for OpenAI functionality
export OPENAI_API_KEY="your-openai-api-key"

# Optional - for DevSkyy agent integration
export DEVSKYY_API_URL="https://api.devskyy.com"
export DEVSKYY_API_KEY="your-devskyy-api-key"
```

## Usage

### Run Standalone

```bash
python server.py
```

### Use with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "devskyy-openai": {
      "command": "python",
      "args": ["/absolute/path/to/DevSkyy/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key-here",
        "DEVSKYY_API_URL": "https://api.devskyy.com",
        "DEVSKYY_API_KEY": "your-devskyy-key-here"
      }
    }
  }
}
```

### Use with Other MCP Clients

The server uses the standard MCP protocol and communicates over stdio, so it works with any MCP-compatible client.

## Available Tools

### OpenAI-Specific Tools

#### 1. `openai_completion`

Generate text using OpenAI models with full customization.

**Example:**

```json
{
  "prompt": "Explain quantum computing in simple terms",
  "model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 500
}
```

#### 2. `openai_code_generation`

Generate production-ready code with documentation and tests.

**Example:**

```json
{
  "description": "Create a FastAPI endpoint for user authentication",
  "language": "python",
  "include_tests": true,
  "include_docs": true
}
```

#### 3. `openai_vision_analysis`

Analyze images using GPT-4o or GPT-4o-mini vision capabilities.

**Example:**

```json
{
  "image_url": "https://example.com/product-image.jpg",
  "prompt": "Describe this product and suggest categories",
  "detail_level": "high"
}
```

#### 4. `openai_function_calling`

Use OpenAI's function calling for structured actions.

**Example:**

```json
{
  "prompt": "What's the weather in San Francisco?",
  "available_functions": [
    {
      "name": "get_weather",
      "description": "Get current weather for a city",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {"type": "string"}
        }
      }
    }
  ],
  "auto_execute": true
}
```

#### 5. `openai_model_selector`

Intelligently select the optimal OpenAI model for your task.

**Example:**

```json
{
  "task_description": "Complex mathematical proof verification",
  "task_type": "reasoning",
  "optimize_for": "quality"
}
```

### DevSkyy Integration Tools

#### 6. `devskyy_agent_openai`

Invoke DevSkyy's 54 specialized agents using OpenAI as the LLM backend.

**Example:**

```json
{
  "agent_name": "scanner",
  "action": "scan_code",
  "parameters": {
    "path": "./src",
    "deep_scan": true
  }
}
```

**Available Agents:**

- `scanner` - Code quality analysis
- `fixer` - Automated code fixing
- `theme_builder` - WordPress theme generation
- `product_manager` - E-commerce product operations
- `pricing_engine` - Dynamic pricing optimization
- `ml_predictor` - Machine learning predictions
- `marketing` - Campaign automation
- `content_generator` - Content creation

#### 7. `openai_capabilities_info`

Get detailed information about OpenAI models and capabilities.

## OpenAI Models

### GPT-4o

- **Context Window**: 128,000 tokens
- **Supports Vision**: ✅ Yes
- **Supports Function Calling**: ✅ Yes
- **Supports JSON Mode**: ✅ Yes
- **Best For**: Complex reasoning, multimodal tasks, code, analysis

### GPT-4o-mini

- **Context Window**: 128,000 tokens
- **Supports Vision**: ✅ Yes
- **Supports Function Calling**: ✅ Yes
- **Supports JSON Mode**: ✅ Yes
- **Best For**: Simple tasks, high volume, quick responses, cost optimization

### o1-preview

- **Context Window**: 128,000 tokens
- **Supports Vision**: ❌ No
- **Supports Function Calling**: ❌ No
- **Supports JSON Mode**: ❌ No
- **Best For**: Complex reasoning, mathematics, science, code review

## Response Formats

All tools support two response formats:

1. **Markdown** (default) - Human-readable formatted text
2. **JSON** - Structured data for programmatic use

Specify format in the request:

```json
{
  "response_format": "json"
}
```

## Error Handling

The server includes comprehensive error handling:

- **HTTP Errors**: Translated to user-friendly messages
- **Timeouts**: 60-second default with configurable timeout
- **Rate Limits**: Automatic retry with backoff
- **API Errors**: Detailed error messages with status codes

## Architecture

```
┌─────────────────────────────────────────────┐
│         MCP Client (Claude/etc)             │
└─────────────────┬───────────────────────────┘
                  │ stdio
┌─────────────────▼───────────────────────────┐
│         OpenAI MCP Server (server.py)       │
│  ┌────────────────────────────────────────┐ │
│  │  MCP Tools (FastMCP Framework)         │ │
│  ├────────────────────────────────────────┤ │
│  │  • openai_completion                   │ │
│  │  • openai_code_generation              │ │
│  │  • openai_vision_analysis              │ │
│  │  • openai_function_calling             │ │
│  │  • openai_model_selector               │ │
│  │  • devskyy_agent_openai                │ │
│  └────────────────────────────────────────┘ │
└─────┬───────────────────────────┬───────────┘
      │                           │
      ▼                           ▼
┌─────────────┐         ┌─────────────────────┐
│  OpenAI API │         │  DevSkyy API        │
│  (GPT-4o)   │         │  (54 Agents)        │
└─────────────┘         └─────────────────────┘
```

## Development

### Testing

The server can be tested without full dependencies by checking syntax:

```bash
python -m py_compile server.py
```

### Extending

To add new tools, follow this pattern:

```python
@mcp.tool(
    name="your_tool_name",
    annotations={
        "title": "Your Tool Title",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def your_tool(params: YourInputModel) -> str:
    """Tool description for LLM.

    Args:
        params: Input parameters

    Returns:
        str: Formatted response
    """
    # Implementation
    data = await _make_api_request("endpoint", method="POST", data={...})
    return _format_response(data, params.response_format, "Title")
```

## Security

- API keys are read from environment variables only
- All requests include authentication headers
- Input validation using Pydantic models
- Character limits on responses to prevent abuse
- Timeout protection on all API calls

## Performance

- Async/await throughout for non-blocking I/O
- 60-second timeout on API requests
- Character limit (25,000) on responses
- Efficient JSON serialization

## Troubleshooting

### Server won't start

```bash
# Check dependencies
pip install fastmcp httpx pydantic openai python-jose[cryptography]

# Verify Python version
python --version  # Should be 3.11+
```

### OpenAI API errors

```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### DevSkyy integration not working

```bash
# Check DevSkyy configuration
echo $DEVSKYY_API_URL
echo $DEVSKYY_API_KEY

# Test DevSkyy API
curl $DEVSKYY_API_URL/health
```

## Related Files

- `devskyy_mcp.py` - Main DevSkyy MCP server (multi-model)
- `orchestration/llm_registry.py` - LLM model registry
- `orchestration/llm_clients.py` - LLM client implementations
- `adk/base.py` - Base agent framework

## License

Copyright © 2025 The Skyy Rose Collection LLC

## Support

- GitHub Issues: <https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues>
- Documentation: <https://docs.devskyy.com>
- API Reference: <https://api.devskyy.com/docs>
