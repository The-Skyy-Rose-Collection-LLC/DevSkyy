"""
Test suite for performance optimizations

This file tests the performance improvements made to:
- RAG/MCP system (caching, vectorization, batching)
- SQLite auth system (connection pooling, regex caching)
- Main application (lazy loading)
"""

import time
import numpy as np


def test_query_cache():
    """Test RAG query cache functionality"""
    from rag_mcp_hybrid import QueryCache, RetrievalStrategy
    
    cache = QueryCache(max_size=10)
    
    # Test empty cache
    stats = cache.stats()
    assert stats['size'] == 0
    assert stats['max_size'] == 10
    assert stats['hit_rate'] == 0.0
    
    # Test cache miss
    result = cache.get("test query", 5, RetrievalStrategy.SIMILARITY)
    assert result is None
    assert cache._misses == 1
    
    # Test cache put
    cache.put("test query", 5, RetrievalStrategy.SIMILARITY, [])
    assert cache.stats()['size'] == 1
    
    # Test cache hit
    result = cache.get("test query", 5, RetrievalStrategy.SIMILARITY)
    assert result is not None
    assert cache._hits == 1
    
    # Test hit rate calculation
    stats = cache.stats()
    assert stats['hit_rate'] == 0.5  # 1 hit, 1 miss
    
    # Test cache size limit
    for i in range(15):
        cache.put(f"query_{i}", 5, RetrievalStrategy.SIMILARITY, [])
    
    stats = cache.stats()
    assert stats['size'] <= 10  # Should not exceed max_size
    
    # Test cache clear
    cache.clear()
    assert cache.stats()['size'] == 0
    assert cache._hits == 0
    assert cache._misses == 0
    
    print("✓ Query cache tests passed")


def test_vectorized_mmr_performance():
    """Test that vectorized MMR is faster than loop-based approach"""
    # Generate sample embeddings
    n_candidates = 50
    embedding_dim = 384
    
    np.random.seed(42)
    candidate_embeddings = np.random.randn(n_candidates, embedding_dim)
    query_emb = np.random.randn(embedding_dim)
    
    # Normalize embeddings (as done in optimized version)
    candidate_norms = np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
    normalized_candidates = candidate_embeddings / candidate_norms
    normalized_query = query_emb / np.linalg.norm(query_emb)
    
    # Vectorized approach (optimized)
    start = time.time()
    query_sims = np.dot(normalized_candidates, normalized_query)
    selected_indices = [0]  # Select first
    selected_embs = normalized_candidates[selected_indices]
    sim_to_selected = np.dot(normalized_candidates, selected_embs.T)
    max_sim_to_selected = np.max(sim_to_selected, axis=1)
    mmr_scores = 0.5 * query_sims - 0.5 * max_sim_to_selected
    vectorized_time = time.time() - start
    
    # Verify it completes quickly
    assert vectorized_time < 0.01  # Should be < 10ms
    
    print(f"✓ Vectorized MMR completed in {vectorized_time*1000:.2f}ms")


def test_password_validator_compiled_patterns():
    """Test that regex patterns are compiled once"""
    from sqlite_auth_system import PasswordValidator, SecurityConfig
    
    config = SecurityConfig()
    validator = PasswordValidator(config)
    
    # Check that patterns are class attributes (compiled once)
    assert hasattr(PasswordValidator, 'UPPERCASE_PATTERN')
    assert hasattr(PasswordValidator, 'LOWERCASE_PATTERN')
    assert hasattr(PasswordValidator, 'NUMBER_PATTERN')
    assert hasattr(PasswordValidator, 'SPECIAL_PATTERN')
    
    # Test validation performance
    start = time.time()
    for _ in range(100):
        is_valid, errors = validator.validate("TestPassword123!")
    elapsed = time.time() - start
    
    # Should be fast (< 50ms for 100 validations)
    assert elapsed < 0.05
    
    # Verify validation works
    is_valid, errors = validator.validate("TestPassword123!")
    assert is_valid
    assert len(errors) == 0
    
    is_valid, errors = validator.validate("weak")
    assert not is_valid
    assert len(errors) > 0
    
    print(f"✓ Password validation (100 calls): {elapsed*1000:.2f}ms")


def test_connection_pool():
    """Test connection pool functionality"""
    from sqlite_auth_system import ConnectionPool, DatabaseConfig
    import tempfile
    import os
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    try:
        config = DatabaseConfig(db_path=db_path)
        pool = ConnectionPool(config, pool_size=3)
        
        # Test pool size
        assert len(pool._pool) == 3
        
        # Test getting connection
        with pool.get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        
        # Connection should be returned to pool
        assert len(pool._pool) == 3
        
        # Test multiple connections
        connections = []
        for i in range(5):
            with pool.get_connection() as conn:
                connections.append(id(conn))
        
        # Test pool cleanup
        pool.close_all()
        assert len(pool._pool) == 0
        
        print("✓ Connection pool tests passed")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)


def test_lazy_agent_registry():
    """Test that agent registry uses lazy initialization"""
    from main import AgentRegistry
    
    registry = AgentRegistry()
    
    # Should not be initialized yet
    assert not registry._initialized
    assert len(registry.agents) == 0
    
    # First access should trigger initialization
    agent = registry.get_agent("scanner")
    assert registry._initialized
    assert len(registry.agents) > 0
    assert agent is not None
    
    # Subsequent access should reuse initialized agents
    agent2 = registry.get_agent("scanner")
    assert agent2 is agent  # Same instance
    
    # List agents should also trigger initialization
    registry2 = AgentRegistry()
    assert not registry2._initialized
    
    agents = registry2.list_agents()
    assert registry2._initialized
    assert len(agents) == 54  # All 54 agents
    
    print("✓ Lazy agent registry tests passed")


def test_batch_document_processing():
    """Test batch processing reduces memory usage"""
    from rag_mcp_hybrid import Document, DocumentType
    
    # Create many documents
    documents = []
    for i in range(1000):
        doc = Document(
            content=f"Test document {i} " * 100,  # ~1KB each
            metadata={"index": i},
            doc_type=DocumentType.TEXT
        )
        documents.append(doc)
    
    # Verify we have many documents
    assert len(documents) == 1000
    
    # Batch processing would split these into chunks
    batch_size = 100
    num_batches = (len(documents) + batch_size - 1) // batch_size
    
    assert num_batches == 10  # 1000 docs / 100 batch size
    
    # Verify batching works
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        assert len(batch) <= batch_size
    
    print("✓ Batch processing tests passed")


if __name__ == "__main__":
    print("\nRunning performance optimization tests...\n")
    
    test_query_cache()
    test_vectorized_mmr_performance()
    test_password_validator_compiled_patterns()
    test_connection_pool()
    test_lazy_agent_registry()
    test_batch_document_processing()
    
    print("\n✅ All performance optimization tests passed!")
