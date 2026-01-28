# DevSkyy Examples

> Runnable, documented, up-to-date | 10 files

## Examples
```
examples/
├── basic_query.py              # RAG query
├── claude_agent_sdk_demo.py    # Agent SDK
├── multi_agent_workflow.py     # Orchestration
├── security_alerting_demo.py   # Security
├── tool_registry_example.py    # Tool registration
└── wordpress_3d_sync_demo.py   # WP 3D sync
```

## Pattern
```python
"""
Example: Basic RAG Query
Prerequisites: pip install devskyy[rag]
Usage: python basic_query.py "query"
"""
async def main(query: str) -> None:
    orchestrator = RAGOrchestrator()
    result = await orchestrator.query(query)
    print(f"Response: {result.response}")
```

## Categories
| Category | Examples |
|----------|----------|
| RAG | basic_query, llamaindex |
| Agents | agent_sdk, multi_agent |
| Integration | webhook, wordpress_3d |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| RAG examples | **MCP** (rag_server): `rag_query` |
| Agent examples | **MCP**: `multi_agent_workflow` |
| Example testing | **Agent**: `tdd-guide` |

**"Every example should run on first try."**
