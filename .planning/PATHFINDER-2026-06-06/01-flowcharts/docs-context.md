# F5 — docs-context

**Entry:** `get_docs_context()` — `orchestration/docs_context.py:62`
**Call site:** `agents/base_super_agent/agent.py:562-574` (all 6 SuperAgents, when technique == RAG)
**Store:** ChromaDB — collection `devskyy_docs` (SAME as F1 reader / F4 writer)
**Confidence:** HIGH (call site + collection target confirmed)

## Flowchart

```mermaid
flowchart TD
    A["SuperAgent.run(), technique==RAG<br/>agents/base_super_agent/agent.py:562-574"] --> B["get_docs_context(query)<br/>orchestration/docs_context.py:62"]
    B --> C["embed query<br/>(I1 embedding-engine)"]
    C --> D["vector search devskyy_docs<br/>(I2 vector-store, ChromaDB)"]
    D --> E["return raw top-k context"]
    E --> A

    %% the overlap
    W["F4 document-ingestion<br/>WRITES devskyy_docs"] -.writes.-> D
    R1["F1 RAGContextManager<br/>READS devskyy_docs (w/ rewrite+rerank)"] -.reads.-> D
    R2["F5 get_docs_context<br/>READS devskyy_docs (NO rewrite/rerank)"] -.reads.-> D
```

## Findings
- **CRITICAL OVERLAP CONFIRMED:** F4 (writer), F5 (reader), F1 (reader) all target the SAME `devskyy_docs` ChromaDB collection with **no coordination / no locking**.
- **F5 bypasses F1's pipeline** — no query rewriting, no reranking, no caching. A SuperAgent on the RAG technique gets raw top-k, while the "richer" F1 path exists but is barely wired (see F1's no-arg ctor bug).
- Two readers of one collection with divergent quality = the central duplication thesis.

## Gaps
- Whether any agent ever routes through F1 instead of F5 in production — F1 looks effectively dead, F5 is the live reader. Confirm in Phase 2.
