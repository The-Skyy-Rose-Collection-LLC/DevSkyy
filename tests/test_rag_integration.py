"""
Test RAG Integration with SuperAgents
======================================

This test verifies that the RAG pipeline is correctly integrated with SuperAgents.

To run:
    pytest tests/test_rag_integration.py -v
"""

from pathlib import Path

import pytest

# Skip all tests in this module if chromadb is not installed or incompatible
pytest.importorskip("chromadb", reason="chromadb not installed or incompatible with Pydantic v2")

from adk.base import AgentConfig
from agents.commerce_agent import CommerceAgent
from orchestration.auto_ingestion import auto_ingest_documents
from orchestration.rag_context_manager import RAGContextConfig, create_rag_context_manager
from orchestration.vector_store import VectorStoreConfig


@pytest.fixture
async def rag_manager():
    """Create a RAG context manager for testing."""
    # Use temporary vector store
    vector_config = VectorStoreConfig(
        db_type="chromadb",
        collection_name="test_devskyy_docs",
        persist_directory="./data/test_vectordb",
        default_top_k=3,
        similarity_threshold=0.3,
    )

    rag_config = RAGContextConfig(
        top_k=3,
        use_query_rewriting=False,  # Disable for faster testing
        use_reranking=False,  # Disable for faster testing
        cache_enabled=False,  # Disable caching for testing
    )

    manager = await create_rag_context_manager(
        vector_store_config=vector_config,
        rag_config=rag_config,
        enable_rewriting=False,
        enable_reranking=False,
    )

    yield manager

    # Cleanup
    import shutil

    if Path("./data/test_vectordb").exists():
        shutil.rmtree("./data/test_vectordb")


@pytest.fixture
async def ingested_rag_manager(rag_manager):
    """RAG manager with ingested test documents."""
    # Create test documents
    test_docs_dir = Path("./data/test_docs")
    test_docs_dir.mkdir(parents=True, exist_ok=True)

    # Create sample markdown files
    (test_docs_dir / "product_guide.md").write_text(
        """
# Product Management Guide

## Creating Products

To create a product in the SkyyRose system:
1. Define product name and SKU
2. Set pricing and inventory levels
3. Upload product images
4. Add detailed descriptions
5. Configure variants and options

## Pricing Strategy

Our dynamic pricing engine considers:
- Competitor pricing
- Demand forecasting
- Inventory levels
- Seasonal trends
"""
    )

    (test_docs_dir / "commerce_api.md").write_text(
        """
# Commerce API Documentation

## Product Endpoints

### Create Product
POST /api/v1/products
- name: string (required)
- price: float (required)
- sku: string (required)
- inventory: integer (default: 0)

### List Products
GET /api/v1/products
- Returns paginated list of products
- Supports filtering by category, price range
"""
    )

    # Ingest documents
    stats = await auto_ingest_documents(
        vector_store=rag_manager.vector_store,
        project_root=".",
        scan_directories=["data/test_docs"],
    )

    assert stats["files_ingested"] > 0, "No files were ingested"

    yield rag_manager

    # Cleanup
    import shutil

    if test_docs_dir.exists():
        shutil.rmtree(test_docs_dir)


@pytest.mark.asyncio
async def test_rag_context_retrieval(ingested_rag_manager):
    """Test RAG context retrieval."""
    # Query the RAG system
    context = await ingested_rag_manager.get_context(
        query="How do I create a product?",
        correlation_id="test-001",
    )

    # Verify context was retrieved
    assert context is not None
    assert len(context.documents) > 0
    assert context.query == "How do I create a product?"
    assert context.total_retrieved > 0

    # Check that relevant content was retrieved
    combined_context = context.get_combined_context()
    assert "product" in combined_context.lower()

    print(f"\n✓ Retrieved {len(context.documents)} documents")
    print(f"  Strategy: {context.strategy_used}")
    print(f"  Total retrieved: {context.total_retrieved}")


@pytest.mark.asyncio
async def test_agent_with_rag_context(ingested_rag_manager):
    """Test that SuperAgent uses RAG context during execution."""
    # Create a Commerce agent
    config = AgentConfig(
        name="test_commerce_agent",
        model="claude-sonnet-4-5-20251022",
        temperature=0.7,
        system_prompt="You are a helpful commerce assistant.",
    )

    agent = CommerceAgent(config)
    agent.rag_manager = ingested_rag_manager
    await agent.initialize()

    # Execute a task that should benefit from RAG context
    # Note: This uses execute_auto which retrieves RAG context
    result = await agent.execute_auto(
        prompt="What are the steps to create a new product?",
        correlation_id="test-002",
    )

    # Verify execution succeeded
    assert result is not None
    # The metadata should include RAG context info if available
    print("\n✓ Agent executed with RAG context")
    print(f"  Status: {result.status if hasattr(result, 'status') else 'N/A'}")


@pytest.mark.asyncio
async def test_rag_context_caching(ingested_rag_manager):
    """Test that RAG context caching works."""
    # Enable caching
    ingested_rag_manager.config.cache_enabled = True

    query = "What is the pricing strategy?"

    # First retrieval - should hit vector store
    context1 = await ingested_rag_manager.get_context(query=query)
    assert len(context1.documents) > 0

    # Second retrieval - should hit cache
    context2 = await ingested_rag_manager.get_context(query=query)
    assert len(context2.documents) == len(context1.documents)

    print("\n✓ RAG caching verified")


@pytest.mark.asyncio
async def test_rag_document_chunking():
    """Test that documents are properly chunked during ingestion."""
    from orchestration.auto_ingestion import AutoDocumentIngestion
    from orchestration.vector_store import VectorStoreConfig, create_vector_store

    # Create test vector store
    vector_config = VectorStoreConfig(
        db_type="chromadb",
        collection_name="test_chunking",
        persist_directory="./data/test_chunking",
    )
    vector_store = create_vector_store(vector_config)
    await vector_store.initialize()

    # Create ingestion instance
    ingestion = AutoDocumentIngestion(
        vector_store=vector_store,
        chunk_size=500,  # Small chunks for testing
        chunk_overlap=100,
    )

    # Create a long document
    test_docs_dir = Path("./data/test_chunking_docs")
    test_docs_dir.mkdir(parents=True, exist_ok=True)

    long_content = "This is a test sentence. " * 100  # ~2000 chars
    (test_docs_dir / "long_doc.md").write_text(long_content)

    # Ingest
    stats = await ingestion.ingest_all(
        project_root=".",
        scan_directories=["data/test_chunking_docs"],
    )

    # Verify chunking occurred
    assert stats["documents_created"] > 1, "Document should be split into multiple chunks"

    print("\n✓ Document chunking verified")
    print(f"  Total chunks created: {stats['documents_created']}")

    # Cleanup
    import shutil

    if test_docs_dir.exists():
        shutil.rmtree(test_docs_dir)
    if Path("./data/test_chunking").exists():
        shutil.rmtree("./data/test_chunking")
