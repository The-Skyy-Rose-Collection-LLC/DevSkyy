# F3 — catalog-retriever

**Entry:** `CatalogRetriever.index_catalog()` :161 / `.answer_question()` :352 — `orchestration/catalog_retriever.py`
**Store:** Voyage embeddings + Pinecone — collection `skyyrose-catalog-v1`, namespace `catalog`
**LLM:** `claude-haiku-4-5-20251001`
**Confidence:** HIGH (both production callers read; content composition traced to dossier_loader)

## Flowchart

```mermaid
flowchart TD
    subgraph index [index path]
      I1["index_catalog()<br/>catalog_retriever.py:161"] --> I2["catalog_loader.load CSV<br/>skyyrose/core/catalog_loader.py:33"]
      I2 --> I3["dossier_loader.get_product_with_dossier()<br/>name+collection+garment_type_lock+branding_block+scene_setting+description"]
      I3 --> I4["Voyage embed"]
      I4 --> I5["Pinecone upsert<br/>ns=catalog, coll=skyyrose-catalog-v1"]
    end

    subgraph query [query path]
      Q1["answer_question(q)<br/>catalog_retriever.py:352"] --> Q2["Voyage embed query"]
      Q2 --> Q3["Pinecone query ns=catalog"]
      Q3 --> Q4["claude-haiku-4-5 compose answer"]
      Q4 --> Q5["return answer"]
    end

    %% callers
    C1["scripts/index_skyyrose_catalog.py:67"] -.-> I1
    C2["api/v1/catalog.py:65<br/>CatalogRetriever.for_production(namespace=catalog)"] -.-> Q1
```

## Findings
- **Two production callers:** `scripts/index_skyyrose_catalog.py:67` (index) and `api/v1/catalog.py:65` via `CatalogRetriever.for_production(namespace="catalog")` (query) → the Voyage+Pinecone path.
- **Content composition** now via `dossier_loader.get_product_with_dossier()` = name + collection + garment_type_lock + branding_block + scene_setting + description. (00-features.md described an older composition — branding_spec+description+name — STALE; reconcile.)
- Source of truth: catalog CSV `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` loaded by `skyyrose/core/catalog_loader.py:33`.

## Gaps
- Overlap with F2's `skyyrose-catalog` collection (LightRAG) — same CSV feeding two different vector stores under near-identical collection names. Strong Phase 2 candidate.
