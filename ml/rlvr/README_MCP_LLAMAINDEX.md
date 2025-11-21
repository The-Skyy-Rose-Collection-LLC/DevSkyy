# MCP + LlamaIndex Integration for Enterprise Fine-Tuning

## Overview

This integration combines the **best of both worlds**:

- **MCP (Model Context Protocol)**: Enterprise database infrastructure, transaction management, distributed access
- **LlamaIndex**: Intelligent RAG (Retrieval-Augmented Generation), vector search, semantic similarity

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Client Layer                               │
│  - API endpoints (FastAPI)                                   │
│  - Agent management UI                                       │
│  - CLI tools                                                 │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│            MCPLlamaIndexOrchestrator (Hybrid Layer)          │
│                                                              │
│  ┌─────────────────────┐      ┌────────────────────────┐   │
│  │   MCP Gateway       │  ←→  │   LlamaIndex RAG       │   │
│  │                     │      │                        │   │
│  │ - SQL queries       │      │ - Vector embeddings    │   │
│  │ - ACID transactions │      │ - Semantic search      │   │
│  │ - Metadata storage  │      │ - Similarity ranking   │   │
│  └─────────────────────┘      └────────────────────────┘   │
│              ↓                           ↓                   │
│  ┌─────────────────────┐      ┌────────────────────────┐   │
│  │ Neon PostgreSQL     │      │ Vector Store (Disk)    │   │
│  │ - Training examples │      │ - Embeddings cache     │   │
│  │ - Agent configs     │      │ - Index persistence    │   │
│  │ - Fine-tuning runs  │      │ - Fast retrieval       │   │
│  └─────────────────────┘      └────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│              AI Model Providers                              │
│  - OpenAI (fine-tuning, embeddings)                         │
│  - Anthropic Claude (prompt optimization)                   │
│  - Local models (LoRA, PEFT)                                │
└──────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Hybrid Retrieval Strategy

**Problem**: Pure SQL is rigid, pure vector search lacks precision

**Solution**: Combine both!

```python
async def hybrid_retrieve_best_examples(
    agent_id: UUID,
    query: str,           # Vector search query
    min_score: float,     # SQL filter
    top_k: int
):
    # Step 1: SQL filtering (exact matches)
    - Filter by agent_id (exact)
    - Filter by min_score threshold
    - Filter by example_type (positive/negative)

    # Step 2: Vector search (semantic similarity)
    - Embed the query
    - Find semantically similar examples
    - Rank by cosine similarity

    # Step 3: Hybrid ranking
    hybrid_score = (similarity * 0.6) + (reward_score * 0.4)

    # Result: Best examples that are both relevant AND high-quality
```

### 2. Automatic Sync from MCP to Vector Store

```python
# Training examples stored in Neon (via MCP)
await orchestrator.sync_training_data_to_vector_store(agent_id)

# Creates:
# 1. Embeddings for each example
# 2. Vector index for fast search
# 3. Persisted cache on disk
```

### 3. Claude Prompt Optimization with RAG

```python
# Retrieves best examples using hybrid search
result = await orchestrator.optimize_prompt_with_mcp_rag(agent_id)

# Process:
# 1. Query current prompt from Neon (MCP)
# 2. Hybrid search for best examples (MCP + LlamaIndex)
# 3. Format with XML for Claude
# 4. Call Claude API for optimization
# 5. Update prompt in Neon (MCP transaction)
```

## Installation

```bash
# Already installed llama-index
pip install llama-index

# Verify MCP gateway is running
curl http://localhost:3000/mcp/neon

# Set environment variables
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DATABASE_URL="postgresql+asyncpg://user:pass@host/db"
```

## Usage Examples

### Example 1: Sync Training Data

```python
from ml.rlvr.mcp_llamaindex_integration import MCPLlamaIndexOrchestrator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import uuid
import os

# Setup database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession)

async with async_session() as session:
    orchestrator = MCPLlamaIndexOrchestrator(
        session=session,
        index_dir="./vector_indexes"
    )

    agent_id = uuid.UUID("your-agent-id")

    # Sync from Neon to vector store
    index = await orchestrator.sync_training_data_to_vector_store(
        agent_id,
        force_rebuild=True  # Rebuild index from scratch
    )

    print(f"Indexed {len(index.docstore.docs)} examples")
```

### Example 2: Hybrid Search

```python
# Hybrid retrieval: SQL filters + vector similarity
examples = await orchestrator.hybrid_retrieve_best_examples(
    agent_id=agent_id,
    query="high quality code generation examples",
    min_score=0.8,        # SQL filter: score >= 0.8
    top_k=10,             # Return top 10 results
    example_type="positive"  # SQL filter: positive examples only
)

for ex in examples:
    print(f"Score: {ex['score']:.2f}, Similarity: {ex['similarity']:.2f}")
    print(f"Hybrid Rank: {ex['hybrid_rank']:.2f}")
    print(f"Input: {ex['input'][:100]}...")
```

### Example 3: End-to-End Prompt Optimization

```python
# Complete workflow: MCP + LlamaIndex + Claude
result = await orchestrator.optimize_prompt_with_mcp_rag(
    agent_id=agent_id,
    top_k_examples=10
)

print(f"Agent: {result['agent_name']}")
print(f"Method: {result['method']}")
print(f"Examples used: {result['examples_used']}")
print(f"Retrieval: {result['retrieval_strategy']}")
print(f"\nOptimized Prompt:\n{result['optimized_prompt']}")
```

## Benefits of Integration

### 1. **Performance**
- Vector search: O(log n) similarity lookup
- SQL indexes: O(log n) exact filtering
- Combined: Fast hybrid queries
- Disk persistence: No re-embedding on restart

### 2. **Scalability**
- MCP Gateway: Horizontal scaling
- LlamaIndex: Distributed vector stores
- Neon: Serverless PostgreSQL auto-scaling
- Cache: Reduce API calls to OpenAI embeddings

### 3. **Accuracy**
- Hybrid ranking: Combines semantic + metric scores
- SQL filters: Exact constraints (score thresholds, types)
- Vector search: Semantic relevance
- Result: Best quality examples for fine-tuning

### 4. **Observability**
- MCP: Query logging, transaction tracking
- LlamaIndex: Retrieval metrics, similarity scores
- Database: Full audit trail
- Monitoring: Track example quality over time

## Comparison: Standalone vs MCP Integration

| Feature | Standalone LlamaIndex | MCP + LlamaIndex |
|---------|----------------------|------------------|
| **Data Storage** | Local files/JSON | Neon PostgreSQL (distributed) |
| **Transactions** | ❌ None | ✅ ACID transactions via MCP |
| **Scalability** | Single machine | Horizontal (MCP gateway cluster) |
| **Vector Search** | ✅ Yes | ✅ Yes |
| **SQL Filtering** | ❌ Limited | ✅ Full PostgreSQL queries |
| **Hybrid Queries** | ❌ No | ✅ Yes |
| **Audit Trail** | ❌ No | ✅ Full database logs |
| **Multi-tenancy** | Manual | ✅ Built-in (agent_id isolation) |
| **Backup/Recovery** | Manual | ✅ Neon automatic backups |
| **Real-time Sync** | ❌ Manual | ✅ Automatic (trigger-based) |

## Technical Details

### Hybrid Ranking Formula

```python
# Weighted combination of vector similarity and reward score
hybrid_score = (vector_similarity * α) + (reward_score * β)

# Default weights (tunable):
α = 0.6  # Semantic relevance weight
β = 0.4  # Quality metric weight

# Example:
similarity = 0.85  # Vector cosine similarity
reward = 0.92      # Human/RLVR reward score
hybrid = (0.85 * 0.6) + (0.92 * 0.4) = 0.51 + 0.368 = 0.878
```

### Vector Store Persistence

```
./mcp_llamaindex_storage/
├── <agent_id_1>/
│   ├── docstore.json           # Document metadata
│   ├── index_store.json        # Index structure
│   ├── vector_store.json       # Embeddings
│   └── graph_store.json        # Relationships
├── <agent_id_2>/
│   └── ...
```

### Database Schema (MCP/Neon)

```sql
-- Training examples table (source of truth)
CREATE TABLE training_examples (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL,
    prompt TEXT NOT NULL,
    completion TEXT NOT NULL,
    reward_score DECIMAL(5,4),
    example_type VARCHAR(20),  -- positive/negative
    created_at TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Indexes for hybrid queries
CREATE INDEX idx_training_agent_score
    ON training_examples(agent_id, reward_score DESC);
CREATE INDEX idx_training_type
    ON training_examples(example_type);
```

## Advanced Usage

### Custom Retrieval Strategies

```python
# Strategy 1: Diversity sampling
examples = await orchestrator.hybrid_retrieve_best_examples(
    agent_id=agent_id,
    query="diverse coding examples",  # Broad query for diversity
    min_score=0.7,
    top_k=20  # Over-sample, then deduplicate
)

# Strategy 2: Focused expertise
examples = await orchestrator.hybrid_retrieve_best_examples(
    agent_id=agent_id,
    query="async Python error handling",  # Specific query
    min_score=0.9,  # High quality only
    top_k=5
)

# Strategy 3: Balanced coverage
positive = await orchestrator.hybrid_retrieve_best_examples(
    agent_id=agent_id,
    example_type="positive",
    top_k=7
)
negative = await orchestrator.hybrid_retrieve_best_examples(
    agent_id=agent_id,
    example_type="negative",
    top_k=3
)
```

### Performance Tuning

```python
# Tune hybrid ranking weights
orchestrator.similarity_weight = 0.7  # Emphasize semantic match
orchestrator.score_weight = 0.3

# Adjust embedding model
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-large",  # Higher quality, slower
    api_key=openai_key
)

# Enable caching
Settings.cache = SimpleCache()
```

## Troubleshooting

### Issue: Index out of sync with database

```python
# Force rebuild from Neon
await orchestrator.sync_training_data_to_vector_store(
    agent_id,
    force_rebuild=True
)
```

### Issue: Slow vector search

```python
# Check index size
index = orchestrator.indexes[str(agent_id)]
print(f"Documents: {len(index.docstore.docs)}")

# If too large (>10k docs), consider:
# 1. Filtering by time range (recent examples only)
# 2. Using hierarchical indexes
# 3. Increasing top_k for retriever, then re-rank
```

### Issue: Low quality retrieved examples

```python
# Inspect similarity scores
for ex in examples:
    print(f"Similarity: {ex['similarity']:.3f}")
    print(f"Score: {ex['score']:.3f}")

# Adjust thresholds:
examples = await orchestrator.hybrid_retrieve_best_examples(
    agent_id=agent_id,
    min_score=0.85,  # Increase quality threshold
    top_k=15         # Retrieve more, take best
)
```

## Future Enhancements

1. **Multi-modal embeddings**: Support code + documentation + images
2. **Incremental sync**: Only sync new examples (not full rebuild)
3. **Distributed vector stores**: ChromaDB, Pinecone, Weaviate
4. **Query optimization**: Automatic weight tuning via A/B tests
5. **Real-time updates**: Trigger-based sync from Neon to vector store

## References

- LlamaIndex Docs: https://docs.llamaindex.ai/
- MCP Specification: https://modelcontextprotocol.io/
- Neon PostgreSQL: https://neon.tech/docs
- Claude Prompt Engineering: https://docs.anthropic.com/claude/docs/prompt-engineering
- RLVR System: See `ml/rlvr/README.md`

## Support

For questions or issues:
- MCP Gateway: See `NEON_MCP_SETUP.md`
- LlamaIndex: GitHub issues or documentation
- Fine-tuning: See `ml/rlvr/fine_tuning_orchestrator.py`
