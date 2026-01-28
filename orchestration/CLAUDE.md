# DevSkyy Orchestration

> RAG-first, context-aware | 27 files

## Architecture
```
orchestration/
├── rag_context_manager.py   # RAG pipeline
├── auto_ingestion.py        # Document ingestion
├── vector_store.py          # ChromaDB/FAISS
├── reranker.py              # Cross-encoder reranking
├── brand_context.py         # SkyyRose brand DNA
└── tool_registry.py         # Tool management
```

## Pattern
```python
class RAGContextManager:
    async def get_context(self, query: str, *, top_k: int = 5) -> RAGContext:
        expanded = await self.query_rewriter.expand(query)
        docs = await self.vector_store.search(expanded, top_k=top_k * 2)
        reranked = await self.reranker.rerank(query, docs, top_k)
        return RAGContext(documents=reranked, query=query)
```

## Components
| Component | Purpose |
|-----------|---------|
| Vector Store | ChromaDB/FAISS embeddings |
| Reranker | Cross-encoder relevance |
| Query Rewriter | Query expansion |
| Brand Context | SkyyRose DNA |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
- **MCP** (rag_server): `rag_query`, `rag_ingest`, `rag_get_context`

**"Context is king. RAG is the kingmaker."**
