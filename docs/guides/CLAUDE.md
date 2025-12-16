# Claude Desktop Integration for DevSkyy Enterprise Platform

This document provides instructions for integrating DevSkyy's MCP server with
Claude Desktop for enhanced AI assistance and up-to-date documentation
retrieval.

## Auto-Invoke Instructions

When working with DevSkyy, Claude should automatically invoke the MCP server
for:

### 📚 Documentation Queries

- **Trigger phrases**: "documentation", "docs", "how to", "setup",
  "configuration", "guide"
- **Auto-invoke**: `capabilities_info` tool to get current documentation and
  examples
- **Context**: Always retrieve the latest documentation from the codebase

### 🔧 Code Generation & Examples

- **Trigger phrases**: "code example", "implementation", "generate code",
  "create function"
- **Auto-invoke**: `code_generation` tool with DevSkyy best practices
- **Context**: Use project-specific patterns and security requirements

### 🤖 Agent Capabilities

- **Trigger phrases**: "agent", "54 agents", "specialized task", "wordpress",
  "seo", "analytics"
- **Auto-invoke**: `agent_integration` tool to connect with appropriate DevSkyy
  agents
- **Context**: Route tasks to the most suitable agent from the 54-agent
  ecosystem

### 🔍 Vision Analysis

- **Trigger phrases**: "analyze image", "screenshot", "visual", "diagram"
- **Auto-invoke**: `vision_analysis` tool for image understanding
- **Context**: Provide detailed analysis relevant to DevSkyy platform needs

### ⚙️ API Reference

- **Trigger phrases**: "API", "endpoint", "function", "method", "parameters"
- **Auto-invoke**: `capabilities_info` with specific category filter
- **Context**: Retrieve current API documentation and usage examples

## MCP Server Configuration

Add this configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "devskyy-openai": {
      "command": "python",
      "args": ["mcp/openai_server.py"],
      "cwd": "/path/to/DevSkyy",
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key"
      }
    }
  }
}
```

## Context7 Integration

The DevSkyy MCP server provides Context7-style up-to-date documentation
retrieval:

### Automatic Context Retrieval

- **Sources**: `docs/`, `README.md`, `AGENTS.md`, `server.py`,
  `main_enterprise.py`
- **Similarity threshold**: 0.7 for relevant content matching
- **Max results**: 10 most relevant documentation pieces
- **Real-time**: Always reflects current codebase state

### Smart Auto-Invocation

The server automatically triggers when you mention:

- Documentation needs
- Code examples
- Agent capabilities
- API references
- Setup instructions

## Available Tools

### 1. `completion`

Generate text completions using OpenAI models (GPT-4o, GPT-4o-mini, o1-preview)

**Example usage**: "Complete this prompt using GPT-4o..."

### 2. `code_generation`

Generate code with DevSkyy best practices

**Example usage**: "Generate a FastAPI endpoint for user authentication..."

### 3. `vision_analysis`

Analyze images using GPT-4o vision capabilities

**Example usage**: "Analyze this screenshot of the dashboard..."

### 4. `function_calling`

Execute structured function calls

**Example usage**: "Call the user creation function with these parameters..."

### 5. `model_selection`

Get optimal model recommendations

**Example usage**: "Which model should I use for complex reasoning tasks?"

### 6. `agent_integration`

Connect with DevSkyy's 54-agent ecosystem

**Example usage**: "Use the WordPress agent to create a new post..."

### 7. `capabilities_info`

Get information about available capabilities

**Example usage**: "Show me all available agent types..."

## Best Practices

### 🎯 Efficient Queries

- Be specific about what you need
- Mention the context (development, production, testing)
- Include relevant technical details

### 🔄 Context Awareness

- The MCP server maintains context across conversations
- Reference previous discussions for continuity
- Use agent-specific terminology for better routing

### 🛡️ Security Considerations

- API keys are required for all operations
- Rate limiting: 60 requests/minute, 1000/hour
- Only allowed origins can access the server

### 📊 Monitoring

- Health checks available at `/health`
- Metrics available at `/metrics`
- Logs written to `logs/mcp_server.log`

## Troubleshooting

### Connection Issues

1. Verify API keys are set correctly
2. Check that Python dependencies are installed
3. Ensure the server.py file is executable

### Performance Issues

1. Check rate limiting status
2. Monitor server logs for errors
3. Verify network connectivity to OpenAI/Anthropic APIs

### Documentation Sync

1. The server automatically reflects current codebase state
2. No manual refresh needed - always up-to-date
3. Context retrieval happens in real-time

## Support

For issues with the MCP integration:

1. Check the server logs: `logs/mcp_server.log`
2. Verify configuration in `.mcp.json`
3. Test individual tools using the capabilities_info command
4. Review the comprehensive documentation in `docs/guides/SERVER_README.md`

---

**Note**: This integration provides seamless access to DevSkyy's enterprise
platform capabilities directly within Claude Desktop, ensuring you always have
the most current documentation and can leverage the full 54-agent ecosystem for
specialized tasks.
