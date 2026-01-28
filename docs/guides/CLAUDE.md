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

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change
