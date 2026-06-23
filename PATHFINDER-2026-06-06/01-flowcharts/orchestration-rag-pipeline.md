# F1 — orchestration-rag-pipeline

**Entry:** `RAGContextManager.get_context()` — `orchestration/rag_context_manager.py:296`
**Store:** ChromaDB (default) / Pinecone — collection `devskyy_docs`
**Confidence:** HIGH (read all call sites + the pipeline body)

## Flowchart

```mermaid
flowchart TD
    A["get_context(query)<br/>rag_context_manager.py:296"] --> B{"cache hit?<br/>rag_context_manager.py:329"}
    B -->|yes| H["return cached context<br/>rag_context_manager.py:329"]
    B -->|no| C["query rewrite (HyDE / sub-q / step-back)<br/>rag_context_manager.py:345"]
    C --> D["embed query<br/>rag_context_manager.py:463"]
    D --> E["vector search devskyy_docs<br/>(I2 vector-store)"]
    E --> F["rerank candidates<br/>rag_context_manager.py:392"]
    F --> G["assemble context window<br/>rag_context_manager.py:424"]
    G --> I["cache write<br/>rag_context_manager.py:438"]
    I --> H

    %% callers
    P["core/registry/registrations.py:90-92<br/>RAGContextManager() — NO ARGS"] -.latent TypeError.-> A
    T["tests/test_rag_integration.py:31,57<br/>factory (test-only)"] -.-> A
```

## Findings
- **Only production caller** is `core/registry/registrations.py:90-92`, which instantiates `RAGContextManager()` with **no args** → latent `TypeError` (the factory that injects deps is exercised only in tests).
- Pipeline = rewrite → embed → search → rerank → assemble → cache, gated by a front cache check.
- Depends on shared infra: I1 embedding-engine, I2 vector-store, I3 query-rewriter, I4 reranker.

## Gaps
- Whether the no-arg ctor path is ever hit at runtime (registry may be lazy / unused in prod) — not proven from code alone.
