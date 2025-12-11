"""
Simplified test suite for performance optimizations
Tests only the RAG optimizations which don't require additional dependencies
"""

import sys
sys.path.insert(0, '.')

import time
import numpy as np
from rag_mcp_hybrid import QueryCache, RetrievalStrategy


def test_query_cache():
    """Test RAG query cache functionality"""
    print("\n1. Testing Query Cache...")
    
    cache = QueryCache(max_size=10)
    
    # Test empty cache
    stats = cache.stats()
    assert stats['size'] == 0, "Cache should be empty"
    assert stats['max_size'] == 10, "Max size should be 10"
    assert stats['hit_rate'] == 0.0, "Hit rate should be 0"
    
    # Test cache miss
    result = cache.get("test query", 5, RetrievalStrategy.SIMILARITY)
    assert result is None, "Should return None on miss"
    assert cache._misses == 1, "Should track misses"
    
    # Test cache put
    cache.put("test query", 5, RetrievalStrategy.SIMILARITY, [])
    assert cache.stats()['size'] == 1, "Cache size should be 1"
    
    # Test cache hit
    result = cache.get("test query", 5, RetrievalStrategy.SIMILARITY)
    assert result is not None, "Should return result on hit"
    assert cache._hits == 1, "Should track hits"
    
    # Test hit rate calculation
    stats = cache.stats()
    assert stats['hit_rate'] == 0.5, f"Hit rate should be 0.5, got {stats['hit_rate']}"
    
    # Test cache size limit
    for i in range(15):
        cache.put(f"query_{i}", 5, RetrievalStrategy.SIMILARITY, [])
    
    stats = cache.stats()
    assert stats['size'] <= 10, f"Cache should not exceed max_size, got {stats['size']}"
    
    # Test cache clear
    cache.clear()
    assert cache.stats()['size'] == 0, "Cache should be empty after clear"
    assert cache._hits == 0, "Hits should be reset"
    assert cache._misses == 0, "Misses should be reset"
    
    print("   ✓ Query cache tests passed")


def test_vectorized_mmr_performance():
    """Test that vectorized MMR operations work correctly"""
    print("\n2. Testing Vectorized MMR Performance...")
    
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
    
    # Calculate similarities
    query_sims = np.dot(normalized_candidates, normalized_query)
    
    # Select first document
    selected_indices = [0]
    selected_mask = np.zeros(n_candidates, dtype=bool)
    selected_mask[0] = True
    
    # Calculate similarity to selected
    selected_embs = normalized_candidates[selected_indices]
    sim_to_selected = np.dot(normalized_candidates, selected_embs.T)
    max_sim_to_selected = np.max(sim_to_selected, axis=1)
    
    # Calculate MMR scores
    lambda_mult = 0.5
    mmr_scores = lambda_mult * query_sims - (1 - lambda_mult) * max_sim_to_selected
    mmr_scores[selected_mask] = -float('inf')
    
    # Select best
    best_idx = np.argmax(mmr_scores)
    
    vectorized_time = time.time() - start
    
    # Verify it completes quickly
    assert vectorized_time < 0.05, f"Should be fast, took {vectorized_time*1000}ms"
    assert best_idx >= 0, "Should find a valid index"
    assert mmr_scores[best_idx] > -float('inf'), "Best score should be valid"
    
    print(f"   ✓ Vectorized MMR completed in {vectorized_time*1000:.2f}ms")


def test_cache_key_generation():
    """Test cache key generation is consistent"""
    print("\n3. Testing Cache Key Generation...")
    
    cache = QueryCache(max_size=10)
    
    # Same parameters should generate same key
    key1 = cache._make_key("test query", 5, RetrievalStrategy.SIMILARITY)
    key2 = cache._make_key("test query", 5, RetrievalStrategy.SIMILARITY)
    assert key1 == key2, "Same parameters should generate same key"
    
    # Different parameters should generate different keys
    key3 = cache._make_key("different query", 5, RetrievalStrategy.SIMILARITY)
    assert key1 != key3, "Different queries should generate different keys"
    
    key4 = cache._make_key("test query", 10, RetrievalStrategy.SIMILARITY)
    assert key1 != key4, "Different k values should generate different keys"
    
    key5 = cache._make_key("test query", 5, RetrievalStrategy.MMR)
    assert key1 != key5, "Different strategies should generate different keys"
    
    print("   ✓ Cache key generation tests passed")


def test_lru_ordering():
    """Test that cache maintains LRU order"""
    print("\n4. Testing LRU Ordering...")
    
    cache = QueryCache(max_size=3)
    
    # Fill cache
    cache.put("query1", 5, RetrievalStrategy.SIMILARITY, ["result1"])
    cache.put("query2", 5, RetrievalStrategy.SIMILARITY, ["result2"])
    cache.put("query3", 5, RetrievalStrategy.SIMILARITY, ["result3"])
    
    assert cache.stats()['size'] == 3, "Cache should be full"
    
    # Access query1 (moves to end)
    cache.get("query1", 5, RetrievalStrategy.SIMILARITY)
    
    # Add new item (should evict query2, the least recently used)
    cache.put("query4", 5, RetrievalStrategy.SIMILARITY, ["result4"])
    
    assert cache.stats()['size'] == 3, "Cache should still be at max size"
    
    # query1 should still be there (was accessed recently)
    result = cache.get("query1", 5, RetrievalStrategy.SIMILARITY)
    assert result is not None, "query1 should still be cached"
    
    # query2 should have been evicted
    result = cache.get("query2", 5, RetrievalStrategy.SIMILARITY)
    assert result is None, "query2 should have been evicted"
    
    print("   ✓ LRU ordering tests passed")


def benchmark_cache_performance():
    """Benchmark cache vs no-cache performance"""
    print("\n5. Benchmarking Cache Performance...")
    
    cache = QueryCache(max_size=100)
    
    # Simulate queries
    queries = [f"query_{i % 20}" for i in range(100)]  # 20 unique queries, repeated
    
    # First pass - populate cache (all misses)
    start = time.time()
    for query in queries:
        result = cache.get(query, 5, RetrievalStrategy.SIMILARITY)
        if result is None:
            cache.put(query, 5, RetrievalStrategy.SIMILARITY, [f"result for {query}"])
    first_pass_time = time.time() - start
    
    # Second pass - should have high cache hit rate
    cache._hits = 0
    cache._misses = 0
    
    start = time.time()
    for query in queries:
        result = cache.get(query, 5, RetrievalStrategy.SIMILARITY)
    second_pass_time = time.time() - start
    
    stats = cache.stats()
    
    print(f"   First pass (cache misses): {first_pass_time*1000:.2f}ms")
    print(f"   Second pass (cache hits):  {second_pass_time*1000:.2f}ms")
    print(f"   Cache hit rate: {stats['hit_rate']:.1%}")
    print(f"   Speedup: {first_pass_time/second_pass_time:.1f}x")
    
    # Cache hits should be faster (even if minimal)
    assert second_pass_time <= first_pass_time, "Cache hits should be at least as fast"
    assert stats['hit_rate'] > 0.8, f"Should have high hit rate, got {stats['hit_rate']}"
    
    print("   ✓ Cache performance benchmark passed")


if __name__ == "__main__":
    print("=" * 70)
    print("Performance Optimization Tests - RAG/MCP System")
    print("=" * 70)
    
    try:
        test_query_cache()
        test_vectorized_mmr_performance()
        test_cache_key_generation()
        test_lru_ordering()
        benchmark_cache_performance()
        
        print("\n" + "=" * 70)
        print("✅ All RAG optimization tests passed!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
