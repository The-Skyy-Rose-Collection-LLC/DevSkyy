# Claude Desktop Integration

## Auto-Invoke Triggers
- **Docs**: "documentation", "how to", "guide" → `capabilities_info`
- **Code**: "code example", "generate" → `code_generation`
- **Agents**: "agent", "wordpress", "seo" → `agent_integration`
- **Vision**: "analyze image", "screenshot" → `vision_analysis`
- **API**: "endpoint", "function" → `capabilities_info`

## MCP Config
```json
{"mcpServers": {"devskyy-openai": {"command": "python", "args": ["mcp/openai_server.py"]}}}
```

## Available Tools
| Tool | Purpose |
|------|---------|
| `completion` | GPT-4o text generation |
| `code_generation` | DevSkyy best practices |
| `vision_analysis` | Image understanding |
| `agent_integration` | 54-agent ecosystem |
| `capabilities_info` | API documentation |

## Context7 Integration
- **Sources**: `docs/`, `README.md`, `AGENTS.md`, `server.py`
- **Threshold**: 0.7 similarity | **Max**: 10 results | **Real-time**: Always current

## Best Practices
- Be specific, mention context (dev/prod/test)
- Rate limit: 60/min, 1000/hr
- Health: `/health` | Logs: `logs/mcp_server.log`
