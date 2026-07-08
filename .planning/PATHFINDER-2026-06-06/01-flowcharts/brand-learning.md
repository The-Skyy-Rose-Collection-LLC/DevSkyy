# F6 — brand-learning (SQLite feedback loop, NOT vector RAG)

**Entry class:** `BrandLearningLoop` — `orchestration/brand_learning.py:948`; factory `create_brand_learning_loop()` :1310; wiring `wire_brand_learning()` — `orchestration/brand_integration.py:38`
**Storage:** SQLite — `./data/brand_learning.db` (3 tables). NO embeddings, NO vector store.
**Confidence:** HIGH (full file read + bi-directional grep vs I1/I2)

## Flowchart

```mermaid
flowchart TD
    subgraph WRITERS [write path: observe BrandSignal]
        SM["SocialMediaSubAgent<br/>social_media.py:436"]
        BI["BrandIntelAgent<br/>brand_intel_agent.py:786"]
        AA["AlgorithmAgent<br/>algorithm_agent.py:674"]
        EB["EventBus auto-observe<br/>brand_learning.py:1271"]
        FT["FeedbackTracker seed (one-time)<br/>brand_integration.py:145"]
    end
    OBS["observe()<br/>brand_learning.py:1031"]
    CYCLE["run_cycle()<br/>brand_learning.py:1059"]
    EXT["PatternExtractor<br/>brand_learning.py:537"]
    ADT["BrandAdaptor (mutates SKYYROSE_BRAND)<br/>brand_learning.py:787"]
    subgraph STORE [BrandMemory — SQLite data/brand_learning.db]
        SIG["brand_signals<br/>brand_learning.py:181"]
        INS["brand_insights<br/>brand_learning.py:198"]
        ADP["brand_adaptations<br/>brand_learning.py:215"]
    end
    BIC["get_brand_context_with_learning()<br/>brand_integration.py:215"]
    ALG["AlgorithmAgent scoring penalty<br/>algorithm_agent.py:618"]

    SM & BI & AA --> OBS
    EB -.events.-> OBS
    FT -.seed.-> OBS
    OBS --> SIG
    CYCLE -->|get_signals| SIG --> EXT --> INS
    CYCLE --> ADT --> ADP
    INS -->|get_active_insights| BIC -.augments prompt.-> ALG
```

## Findings
- **SQLite, not vector RAG — CONFIRMED.** Only stdlib `sqlite3` imported; no chromadb/pinecone/embedding import. 3 tables: brand_signals (raw agent outputs + accept/reject), brand_insights (statistical patterns in 8 categories), brand_adaptations (mutations to live `SKYYROSE_BRAND` dict).
- It learns **acceptance-rate patterns** (which provider/agent produces accepted brand copy), NOT semantic similarity. No ML inference at store or read time.
- **ZERO shared infra with I1/I2** (bi-directional grep clean). **F6 does NOT belong in a unified RAG proposal** — it is an orthogonal feedback loop. List as out-of-scope-for-merge in Phase 3.

## Gaps
- `main_enterprise.py` has no direct `brand_learning` ref; `on_startup()` wiring not observed there (may be wired via a separate module or not yet).
- `on_cycle_check()` periodic trigger defined (`brand_integration.py:280`) but no scheduler/cron call site found.
