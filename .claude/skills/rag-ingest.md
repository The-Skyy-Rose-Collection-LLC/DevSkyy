---
name: rag-ingest
description: Batch document ingestion into RAG knowledge base.
---

# RAG Batch Ingestion

## Pipeline
```
Discover → Validate → Chunk → Embed → Ingest → Verify
```

## Document Types
- Markdown (`.md`), Text (`.txt`), PDF (`.pdf`)

## Configuration
- Chunk size: 512 tokens
- Overlap: 50 tokens
- Embedding: sentence-transformers/all-MiniLM-L6-v2
- Backend: ChromaDB

## Ingestion Methods
```python
# MCP Tool
mcp__devskyy_rag__rag_ingest({
  "documents": ["path/to/file.md"]
})

# Direct API
await pipeline.ingest_file("path/to/file.md")
```

## Verification
```python
# Check stats
mcp__devskyy_rag__rag_stats()

# Test query
mcp__devskyy_rag__rag_query({"query": "test", "top_k": 5})
```

## Related Tools
- **MCP**: `rag_query`, `rag_ingest`, `rag_stats`
- **Skill**: `mcp-health` for server status
- **Command**: `/rag-ingest` for batch ingestion
