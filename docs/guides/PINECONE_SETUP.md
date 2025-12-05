# Pinecone Vector Database Setup for DevSkyy

**Version:** 5.2.0
**Date:** 2025-11-20
**Status:** ✅ Configured and Ready

---

## Overview

Pinecone is now configured in DevSkyy for production-grade vector search and semantic similarity operations.

**What is Pinecone?**
- Managed vector database (no infrastructure to manage)
- Serverless architecture (scales automatically)
- Low latency (< 100ms queries)
- Production-ready for RAG (Retrieval-Augmented Generation)

---

## Configuration Status

### ✅ Completed

- [x] **Pinecone SDK installed** - `pinecone-client~=5.0.1`
- [x] **API key configured** - Added to `.env` (not committed)
- [x] **Management script created** - `scripts/pinecone_setup.py`
- [x] **Environment configured** - GCP Starter (free tier)
- [x] **Default index name** - `devskyy`

### Current Configuration

```bash
# From .env file
PINECONE_API_KEY=pcsk_***************  # ✅ Configured
PINECONE_ENVIRONMENT=gcp-starter       # ✅ Free tier
PINECONE_INDEX_NAME=devskyy            # ✅ Default index
```

---

## Quick Start

### 1. Verify Connection

```bash
# Test Pinecone API connection
python scripts/pinecone_setup.py verify
```

**Expected Output:**
```
✅ Successfully connected to Pinecone!
📊 API Key: ***********
🌍 Environment: gcp-starter
📁 Default Index Name: devskyy
📋 Total Indexes: 0
```

### 2. Create Index

```bash
# Create a vector index for DevSkyy
python scripts/pinecone_setup.py create-index
```

**Configuration:**
- **Name:** `devskyy`
- **Dimension:** 1536 (OpenAI `text-embedding-ada-002`)
- **Metric:** Cosine similarity
- **Cloud:** GCP (Google Cloud Platform)
- **Region:** us-central1

### 3. Test Operations

```bash
# Test vector upsert, query, and delete
python scripts/pinecone_setup.py test
```

**Tests:**
1. Upsert test vectors
2. Query for similar vectors
3. Verify results
4. Delete test data

### 4. List Indexes

```bash
# View all Pinecone indexes
python scripts/pinecone_setup.py list-indexes
```

### 5. Get Statistics

```bash
# View usage stats
python scripts/pinecone_setup.py stats
```

---

## Integration with DevSkyy

### Example 1: Semantic Search

```python
# ml/embeddings/pinecone_rag.py
import os
from pinecone import Pinecone
from openai import OpenAI

# Initialize clients
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get or create index
index = pc.Index("devskyy")

def semantic_search(query: str, top_k: int = 5):
    """
    Perform semantic search using Pinecone.

    Args:
        query: Search query text
        top_k: Number of results to return

    Returns:
        List of matching documents with scores
    """
    # Generate embedding for query
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding

    # Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    return [
        {
            "id": match.id,
            "score": match.score,
            "text": match.metadata.get("text", ""),
            "source": match.metadata.get("source", "")
        }
        for match in results.matches
    ]

# Usage
results = semantic_search("How do I deploy DevSkyy?")
for result in results:
    print(f"Score: {result['score']:.4f} - {result['text']}")
```

### Example 2: Document Indexing

```python
# ml/embeddings/document_indexer.py
from typing import List, Dict
from pinecone import Pinecone
from openai import OpenAI
import os

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
index = pc.Index("devskyy")

def index_documents(documents: List[Dict[str, str]], namespace: str = "docs"):
    """
    Index documents in Pinecone.

    Args:
        documents: List of dicts with 'id', 'text', and optional metadata
        namespace: Pinecone namespace for organization
    """
    vectors = []

    for doc in documents:
        # Generate embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=doc["text"]
        )
        embedding = response.data[0].embedding

        # Prepare vector
        vectors.append({
            "id": doc["id"],
            "values": embedding,
            "metadata": {
                "text": doc["text"],
                "source": doc.get("source", "unknown"),
                "timestamp": doc.get("timestamp", "")
            }
        })

    # Upsert to Pinecone
    index.upsert(vectors=vectors, namespace=namespace)
    print(f"✅ Indexed {len(vectors)} documents to namespace '{namespace}'")

# Usage
documents = [
    {
        "id": "doc-1",
        "text": "DevSkyy is an enterprise multi-agent platform",
        "source": "README.md"
    },
    {
        "id": "doc-2",
        "text": "Docker deployment with Neon PostgreSQL",
        "source": "DOCKER_DEPLOYMENT_GUIDE.md"
    }
]
index_documents(documents)
```

### Example 3: RAG with LangChain

```python
# agent/rag_agent.py
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA
import os

# Initialize components
embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

vectorstore = PineconeVectorStore(
    index_name="devskyy",
    embedding=embeddings,
    pinecone_api_key=os.getenv("PINECONE_API_KEY")
)

llm = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Create RAG chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

# Usage
response = qa_chain.run("How do I configure Neon database?")
print(response)
```

---

## Pinecone Free Tier

### What's Included (FREE)

- **1 pod** - Serverless index
- **100,000 vectors** - Storage capacity
- **2 million queries/month** - Read operations
- **GCP or AWS** - Cloud provider choice
- **No credit card required** - For starter tier

### Pricing (If You Scale)

- **Starter:** Free (1 pod, 100K vectors)
- **Standard:** ~$70/month (1 pod, unlimited vectors)
- **Enterprise:** Custom pricing (multi-pod, high availability)

**Current Usage:** Free tier is sufficient for development and small-scale production.

---

## Pinecone vs ChromaDB

**You already have ChromaDB** - Here's when to use each:

### Use ChromaDB (Current)

- ✅ **Local development** - No network required
- ✅ **Quick prototyping** - No setup needed
- ✅ **Small datasets** - < 100K vectors
- ✅ **Self-hosted** - Full control
- ✅ **Open-source** - No vendor lock-in

### Use Pinecone (New)

- ✅ **Production workloads** - High availability
- ✅ **Large scale** - Millions of vectors
- ✅ **Low latency** - < 100ms queries
- ✅ **Managed service** - No infrastructure
- ✅ **Auto-scaling** - Handles traffic spikes
- ✅ **Better filtering** - Advanced metadata queries

**Recommendation:** Use **both**
- **Development:** ChromaDB (local, fast iteration)
- **Production:** Pinecone (managed, scalable)

---

## Embeddings Compatibility

Pinecone works with any embedding model. Common choices:

### OpenAI Embeddings (Recommended)

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# text-embedding-ada-002 (1536 dimensions)
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="Your text here"
)
embedding = response.data[0].embedding  # 1536-dim vector
```

**Cost:** $0.0001 / 1K tokens (~$0.10 per 1M tokens)

### Sentence Transformers (Open Source)

```python
from sentence_transformers import SentenceTransformer

# all-MiniLM-L6-v2 (384 dimensions) - FREE
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("Your text here")
```

**Cost:** Free (runs locally)

### Anthropic (Claude)

Anthropic doesn't provide embeddings API yet. Use OpenAI or Sentence Transformers.

---

## Use Cases for DevSkyy

### 1. Code Search

Index all your codebase for semantic code search:

```python
# Index Python files
index_documents([
    {"id": "api-v1-agents.py", "text": open("api/v1/agents.py").read()},
    {"id": "agent-orchestrator.py", "text": open("agent/orchestrator.py").read()}
])

# Search for code
results = semantic_search("How to create a new agent?")
```

### 2. Documentation Search

Index all markdown docs:

```python
# Index documentation
index_documents([
    {"id": "docker-guide", "text": open("DOCKER_DEPLOYMENT_GUIDE.md").read()},
    {"id": "neon-guide", "text": open("NEON_INTEGRATION_GUIDE.md").read()}
])

# Search docs
results = semantic_search("How to deploy to production?")
```

### 3. Conversational AI

RAG-enhanced chatbot:

```python
# User asks a question
user_question = "How do I configure Neon database?"

# Retrieve relevant context from Pinecone
context = semantic_search(user_question, top_k=3)

# Generate answer with Claude
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

prompt = f"""
Context from documentation:
{chr(10).join([c['text'] for c in context])}

User question: {user_question}

Answer based on the context above:
"""

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)

print(response.content[0].text)
```

### 4. Duplicate Detection

Find similar documents:

```python
# Check if document is duplicate
def is_duplicate(text: str, threshold: float = 0.95) -> bool:
    results = semantic_search(text, top_k=1)
    if results and results[0]['score'] > threshold:
        return True
    return False

# Usage
if is_duplicate("New document text"):
    print("⚠️  This document already exists!")
```

---

## Best Practices

### 1. Namespaces

Organize vectors by category:

```python
# Use namespaces for organization
index.upsert(vectors=docs_vectors, namespace="documentation")
index.upsert(vectors=code_vectors, namespace="code")
index.upsert(vectors=chat_vectors, namespace="chat-history")

# Query specific namespace
results = index.query(
    vector=query_embedding,
    namespace="documentation",
    top_k=5
)
```

### 2. Metadata Filtering

Filter results by metadata:

```python
# Add rich metadata
index.upsert(vectors=[{
    "id": "doc-1",
    "values": embedding,
    "metadata": {
        "text": "...",
        "type": "documentation",
        "language": "python",
        "created": "2025-11-20",
        "author": "DevSkyy"
    }
}])

# Filter query
results = index.query(
    vector=query_embedding,
    filter={"type": "documentation", "language": "python"},
    top_k=5
)
```

### 3. Batch Operations

Process in batches for efficiency:

```python
# Batch upsert (100 vectors at a time)
batch_size = 100
for i in range(0, len(vectors), batch_size):
    batch = vectors[i:i+batch_size]
    index.upsert(vectors=batch)
```

### 4. Error Handling

```python
from pinecone.exceptions import PineconeException

try:
    results = index.query(vector=embedding, top_k=5)
except PineconeException as e:
    # Log error, use fallback (ChromaDB)
    print(f"Pinecone error: {e}")
    # Fallback to ChromaDB or local cache
```

---

## Monitoring

### Check Index Stats

```bash
# View vector count, namespaces, storage
python scripts/pinecone_setup.py stats
```

### Pinecone Dashboard

Monitor usage in real-time:
- **URL:** https://app.pinecone.io/
- **Metrics:** Queries/sec, vector count, storage
- **Logs:** Query history, errors

---

## Security

### ✅ API Key Management

```bash
# ✅ CORRECT - Use environment variables
PINECONE_API_KEY=pcsk_***  # In .env (gitignored)

# ❌ WRONG - Never hardcode
pc = Pinecone(api_key="pcsk_abc123...")  # NEVER DO THIS
```

### ✅ Access Control

```python
# Restrict Pinecone operations to admin users
from security.jwt_auth import require_admin
from fastapi import Depends

@router.post("/api/v1/vectors/search")
async def search_vectors(
    query: str,
    current_user = Depends(require_admin)  # Only admins
):
    # Only admins can search vectors
    results = semantic_search(query)
    return results
```

### ✅ Input Validation

```python
from pydantic import BaseModel, validator

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

    @validator('query')
    def validate_query(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Query cannot be empty")
        if len(v) > 1000:
            raise ValueError("Query too long (max 1000 chars)")
        return v.strip()

    @validator('top_k')
    def validate_top_k(cls, v):
        if v < 1 or v > 100:
            raise ValueError("top_k must be between 1 and 100")
        return v
```

---

## Troubleshooting

### Issue: Connection Failed

**Symptoms:**
```
❌ Connection failed: Max retries exceeded
```

**Solutions:**
1. Check API key is correct: https://app.pinecone.io/
2. Verify internet connection
3. Check Pinecone status: https://status.pinecone.io/

### Issue: Index Not Found

**Symptoms:**
```
❌ Index 'devskyy' does not exist
```

**Solution:**
```bash
# Create index
python scripts/pinecone_setup.py create-index
```

### Issue: Dimension Mismatch

**Symptoms:**
```
❌ Vector dimension 768 does not match index dimension 1536
```

**Solution:**
- Ensure all embeddings use same model
- OpenAI ada-002: 1536 dimensions
- Sentence Transformers (MiniLM): 384 dimensions
- Create separate indexes for different dimensions

### Issue: Rate Limit Exceeded

**Symptoms:**
```
❌ Rate limit exceeded
```

**Solution:**
- Free tier: 2M queries/month
- Implement caching (Redis)
- Batch operations
- Upgrade to paid plan

---

## Migration from ChromaDB

### Step 1: Export from ChromaDB

```python
import chromadb

# Connect to ChromaDB
chroma_client = chromadb.Client()
collection = chroma_client.get_collection("devskyy")

# Get all vectors
results = collection.get(include=["embeddings", "metadatas", "documents"])

vectors = []
for i in range(len(results["ids"])):
    vectors.append({
        "id": results["ids"][i],
        "values": results["embeddings"][i],
        "metadata": {
            "text": results["documents"][i],
            **results["metadatas"][i]
        }
    })
```

### Step 2: Import to Pinecone

```python
from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("devskyy")

# Batch upsert
batch_size = 100
for i in range(0, len(vectors), batch_size):
    batch = vectors[i:i+batch_size]
    index.upsert(vectors=batch)

print(f"✅ Migrated {len(vectors)} vectors to Pinecone")
```

---

## Cost Optimization

### 1. Use Namespaces

Organize data to avoid unnecessary indexes:

```python
# One index, multiple namespaces
index.upsert(vectors=docs, namespace="docs")
index.upsert(vectors=code, namespace="code")
index.upsert(vectors=chat, namespace="chat")
```

**Savings:** 1 index instead of 3 ($0 vs $140/month)

### 2. Cache Popular Queries

```python
from cachetools import TTLCache

# Cache results for 1 hour
cache = TTLCache(maxsize=1000, ttl=3600)

def cached_search(query: str):
    if query in cache:
        return cache[query]

    results = semantic_search(query)
    cache[query] = results
    return results
```

**Savings:** Reduce query count by 50-70%

### 3. Batch Operations

```python
# ❌ BAD - 100 API calls
for doc in documents:
    index.upsert(vectors=[doc])

# ✅ GOOD - 1 API call
index.upsert(vectors=documents)
```

**Savings:** Faster + less network overhead

---

## Next Steps

1. **Create Index:**
   ```bash
   python scripts/pinecone_setup.py create-index
   ```

2. **Test Operations:**
   ```bash
   python scripts/pinecone_setup.py test
   ```

3. **Index Documentation:**
   ```python
   # Create script: scripts/index_documentation.py
   from ml.embeddings.document_indexer import index_documents
   import glob

   docs = []
   for md_file in glob.glob("*.md"):
       with open(md_file) as f:
           docs.append({
               "id": md_file,
               "text": f.read(),
               "source": md_file
           })

   index_documents(docs, namespace="docs")
   ```

4. **Build RAG Agent:**
   - See examples in Integration section
   - Use LangChain + Pinecone + Claude
   - Deploy to production

5. **Monitor Usage:**
   ```bash
   python scripts/pinecone_setup.py stats
   ```

---

## Resources

- **Pinecone Dashboard:** https://app.pinecone.io/
- **Pinecone Docs:** https://docs.pinecone.io/
- **Python SDK:** https://github.com/pinecone-io/pinecone-python-client
- **Status Page:** https://status.pinecone.io/
- **Pricing:** https://www.pinecone.io/pricing/

---

**Status:** ✅ Configured and Ready
**Free Tier:** Active (100K vectors, 2M queries/month)
**Next Step:** Create index and test operations

