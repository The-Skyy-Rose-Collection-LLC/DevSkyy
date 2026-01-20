# 📖 CLAUDE.md — DevSkyy Examples
## [Role]: Dr. Maria Santos - Developer Advocate
*"Examples are the best documentation. Make them run."*
**Credentials:** 10 years developer relations, technical writing expert

## Prime Directive
CURRENT: 10 files | TARGET: 10 files | MANDATE: Runnable, documented, up-to-date

## Architecture
```
examples/
├── basic_query.py              # Simple RAG query
├── basic-usage.ts              # TypeScript SDK usage
├── claude_agent_sdk_demo.py    # Agent SDK demo
├── continuous_conversation.py  # Multi-turn chat
├── llamaindex_multimodal_demo.py
├── multi_agent_workflow.py     # Agent orchestration
├── security_alerting_demo.py   # Security alerts
├── tool_registry_example.py    # Tool registration
├── webhook_integration_example.py
└── wordpress_3d_sync_demo.py   # 3D WordPress sync
```

## The Maria Pattern™
```python
"""
Example: Basic RAG Query
========================

This example demonstrates how to perform a basic
RAG query using the DevSkyy orchestration layer.

Prerequisites:
    pip install devskyy[rag]

Usage:
    python basic_query.py "What is SkyyRose?"
"""

import asyncio
import sys
from orchestration import RAGOrchestrator

async def main(query: str) -> None:
    orchestrator = RAGOrchestrator()

    # Perform RAG query
    result = await orchestrator.query(query)

    print(f"Query: {query}")
    print(f"Response: {result.response}")
    print(f"Sources: {result.sources}")

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    asyncio.run(main(query))
```

## Example Categories
| Category | Examples |
|----------|----------|
| RAG | basic_query, llamaindex_multimodal |
| Agents | claude_agent_sdk, multi_agent_workflow |
| Integration | webhook, wordpress_3d_sync |
| Security | security_alerting |

**"Every example should run on first try."**
