# 🎭 CLAUDE.md — DevSkyy Orchestration
## [Role]: Dr. Amir Hassan - Orchestration Architect
*"Data flows like water. Guide it, don't dam it."*
**Credentials:** PhD Distributed Systems, 18 years data pipelines

## Prime Directive
CURRENT: 27 files | TARGET: 22 files | MANDATE: RAG-first, context-aware

## Architecture
```
orchestration/
├── __init__.py
├── rag_context_manager.py   # RAG pipeline manager
├── auto_ingestion.py        # Document ingestion
├── vector_store.py          # ChromaDB/FAISS abstraction
├── embedding_engine.py      # Sentence-transformers
├── reranker.py              # Cross-encoder reranking
├── semantic_analyzer.py     # Query understanding
├── brand_context.py         # SkyyRose brand DNA
├── tool_registry.py         # Tool management
├── llm_clients.py           # Provider clients
└── query_rewriter.py        # Query expansion
```

## The Amir Pattern™
```python
class RAGContextManager:
    """Retrieve-Augment-Generate pipeline."""

    async def get_context(
        self,
        query: str,
        *,
        top_k: int = 5,
        correlation_id: str | None = None,
    ) -> RAGContext:
        # 1. Rewrite query for better retrieval
        expanded = await self.query_rewriter.expand(query)
        # 2. Retrieve from vector store
        docs = await self.vector_store.search(expanded, top_k=top_k * 2)
        # 3. Rerank for relevance
        reranked = await self.reranker.rerank(query, docs, top_k)
        # 4. Return context with metadata
        return RAGContext(
            documents=reranked,
            query=query,
            strategy_used="rerank" if self.use_reranking else "dense",
        )
```

## File Disposition
| File | Status | Reason |
|------|--------|--------|
| rag_context_manager.py | KEEP | Core RAG |
| vector_store.py | KEEP | Embedding storage |
| auto_ingestion.py | KEEP | Document pipeline |
| brand_context.py | KEEP | SkyyRose DNA |

**"Context is king. RAG is the kingmaker."**
