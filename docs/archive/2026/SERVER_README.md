# DevSkyy OpenAI MCP Server

A Model Context Protocol (MCP) server that integrates OpenAI's GPT-4o, GPT-4o-mini, and o1-preview models with DevSkyy's 6-agent platform.

## Features

### 7 MCP Tools

1. **openai_completion** - Text generation with all OpenAI models
2. **openai_code_generation** - Code generation with tests and documentation
3. **openai_vision_analysis** - Image analysis using GPT-4o vision
4. **openai_function_calling** - Structured function calls and JSON outputs
5. **openai_model_selector** - Intelligent model selection based on task
6. **devskyy_agent_openai** - Integration with DevSkyy's agent ecosystem
7. **openai_capabilities_info** - Model capabilities and integration info

### Model Support

- **GPT-4o**: 128K context, vision, function calling, JSON mode
- **GPT-4o-mini**: 128K context, faster/cheaper, vision, function calling
- **o1-preview**: 128K context, advanced reasoning (no vision/functions)

## Quick Start

### 1. Environment Setup

```bash
export OPENAI_API_KEY="sk-your-key-here"
export DEVSKYY_API_KEY="your-devskyy-key"  # Optional
```

### 2. Install Dependencies

```bash
pip install openai mcp pydantic
```

### 3. Run Server

```bash
python server.py
```

### 4. Claude Desktop Integration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devskyy-openai": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here",
        "DEVSKYY_API_KEY": "your-devskyy-key"
      }
    }
  }
}
```

## Tool Usage Examples

### Text Completion

```json
{
  "tool": "openai_completion",
  "arguments": {
    "prompt": "Explain quantum computing in simple terms",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

### Code Generation

```json
{
  "tool": "openai_code_generation",
  "arguments": {
    "description": "FastAPI endpoint for user authentication with JWT",
    "language": "python",
    "include_tests": true,
    "include_docs": true
  }
}
```

### Vision Analysis

```json
{
  "tool": "openai_vision_analysis",
  "arguments": {
    "image_url": "https://example.com/product.jpg",
    "prompt": "Analyze this product image for e-commerce listing",
    "detail_level": "high"
  }
}
```

### Function Calling

```json
{
  "tool": "openai_function_calling",
  "arguments": {
    "prompt": "Get the weather for San Francisco",
    "functions": [
      {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          }
        }
      }
    ]
  }
}
```

### Model Selection

```json
{
  "tool": "openai_model_selector",
  "arguments": {
    "task_description": "Complex mathematical reasoning problem",
    "priority": "quality"
  }
}
```

### DevSkyy Agent Integration

```json
{
  "tool": "devskyy_agent_openai",
  "arguments": {
    "agent_name": "scanner",
    "action": "scan_code",
    "parameters": {
      "path": "./src",
      "deep_scan": true
    }
  }
}
```

### Capabilities Info

```json
{
  "tool": "openai_capabilities_info",
  "arguments": {
    "model": "gpt-4o"
  }
}
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│  DevSkyy MCP     │◄──►│   OpenAI API    │
│  (Claude, etc)  │    │     Server       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  DevSkyy Agents  │
                       │   (54 agents)    │
                       └──────────────────┘
```

## Error Handling

- **Missing API Key**: Returns error message with setup instructions
- **Invalid Parameters**: Pydantic validation with detailed error messages
- **API Failures**: Graceful error handling with retry logic
- **Timeout Protection**: 60-second timeout on all API calls
- **Rate Limiting**: Respects OpenAI rate limits

## Security

- Environment variable-based API key management
- Input validation using Pydantic models
- No API keys logged or exposed in responses
- Secure stdio transport protocol

## Performance

- **Async/await**: Non-blocking operations throughout
- **Connection pooling**: Reuses OpenAI client connections
- **Response streaming**: Large responses streamed efficiently
- **Memory management**: Automatic cleanup of large objects

## Troubleshooting

### Common Issues

1. **"OpenAI client not initialized"**
   - Set `OPENAI_API_KEY` environment variable
   - Verify API key is valid and has credits

2. **"Model not found"**
   - Check model name spelling
   - Verify model access in your OpenAI account

3. **"Function calling failed"**
   - Ensure functions array is properly formatted
   - Use GPT-4o or GPT-4o-mini (not o1-preview)

4. **"Vision analysis failed"**
   - Verify image URL is accessible
   - Use GPT-4o model (only model with vision)

### Debug Mode

```bash
export PYTHONPATH=.
export MCP_DEBUG=1
python server.py
```

## Integration with DevSkyy Platform

This MCP server seamlessly integrates with DevSkyy's existing infrastructure:

- **LLM Registry**: Registers OpenAI models in DevSkyy's model registry
- **Agent Orchestration**: Routes requests through DevSkyy's orchestration layer
- **Security**: Inherits DevSkyy's security and authentication systems
- **Monitoring**: Integrates with DevSkyy's performance tracking and logging

## License

Proprietary - The Skyy Rose Collection LLC
