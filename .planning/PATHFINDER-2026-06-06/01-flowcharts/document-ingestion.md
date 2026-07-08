# F4 — document-ingestion (the WRITE side of devskyy_docs)

**Live entry:** `DocumentIngestionPipeline.ingest_directory()` :361 / `.ingest_file()` :319 — `orchestration/document_ingestion.py`
**Dead entry:** `AutoDocumentIngestion.ingest_all()` — `orchestration/auto_ingestion.py:78` (ZERO production callers)
**Store:** ChromaDB — collection `devskyy_docs` (`vector_store.py:222`)
**Confidence:** HIGH

## Flowchart

```mermaid
flowchart TD
    CLI["run_docs_pipeline.py::run_ingestion<br/>scripts/run_docs_pipeline.py:172"]
    MCP["rag_ingest MCP tool<br/>mcp_servers/rag_server.py:303"]

    ENTRY1["DocumentIngestionPipeline.ingest_directory<br/>document_ingestion.py:361"]
    ENTRY2["DocumentIngestionPipeline.ingest_file<br/>document_ingestion.py:319"]
    LOAD["DocumentLoader.load_file<br/>document_ingestion.py:262"]
    CHUNK["TextChunker.chunk_text<br/>document_ingestion.py:139"]
    EMBED["embed_batch<br/>document_ingestion.py:354"]
    ENGINE["create_embedding_engine → SentenceTransformer<br/>embedding_engine.py:685 (I1)"]
    UPSERT["add_documents<br/>document_ingestion.py:357"]
    CHROMA["ChromaVectorStore → coll devskyy_docs<br/>vector_store.py:365 (I2)"]

    CLI -.on-demand CLI.-> ENTRY1
    MCP -.on-demand tool.-> ENTRY1
    MCP -.single file.-> ENTRY2
    ENTRY1 -->|per file, semaphore=5| ENTRY2
    ENTRY2 --> LOAD --> CHUNK --> EMBED
    EMBED --- ENGINE
    EMBED --> UPSERT --> CHROMA

    DEAD["AutoDocumentIngestion.ingest_all<br/>auto_ingestion.py:78<br/>NO PROD CALLERS — inline SentenceTransformer:276-279"]
    style DEAD fill:#888,color:#fff,stroke:#555
```

## Findings
- **`AutoDocumentIngestion` is dead code** — no caller in api/, agents/, scripts/, main_enterprise.py, core/registry. It also re-implements embedding INLINE (`auto_ingestion.py:276-279`, `SentenceTransformer("all-MiniLM-L6-v2")`) instead of using I1 → a second embedding code path. (00-features.md's claim that AutoDocumentIngestion defines the scan scope is correct about the code, but that code is never run.)
- **Live writers** are CLI (`run_docs_pipeline.py:202`) and the MCP `rag_ingest` tool (`rag_server.py:326/336`). Both on-demand; **nothing ingests at FastAPI startup**.
- Scan dirs (in the dead class) = docs/, README.md, CLAUDE.md, .claude/ — confirmed NOT knowledge-base/ or graphify.
- **No write/read coordination on `devskyy_docs`.** Writer = sync `collection.add()`, readers (F1/F5) hold a 5-min `VectorSearchCache` TTL → up to 5-min stale window if ingest runs during serving.

## Gaps
- Whether AutoDocumentIngestion is invoked from a deploy script / worker container outside the repo tree.
- Actual prod `EMBEDDING_PROVIDER` env value (default sentence-transformers, 384-dim).
