"""
Performance Tests: API Endpoint Benchmarks
Tests to measure API endpoint performance and response times.
"""

import pytest
import time


@pytest.mark.performance
@pytest.mark.benchmark
def test_health_endpoint_performance(test_client, performance_timer):
    """Test health endpoint response time."""
    response = test_client.get("/health")
    elapsed = performance_timer()
    
    # Health endpoint should respond in under 100ms
    assert elapsed < 0.1, f"Health endpoint took {elapsed:.3f}s (should be < 0.1s)"
    assert response.status_code in [200, 503]  # OK or Service Unavailable


@pytest.mark.performance
@pytest.mark.benchmark
def test_root_endpoint_performance(test_client, performance_timer):
    """Test root endpoint response time."""
    response = test_client.get("/")
    elapsed = performance_timer()
    
    # Root endpoint should respond quickly
    assert elapsed < 0.2, f"Root endpoint took {elapsed:.3f}s (should be < 0.2s)"


@pytest.mark.performance
@pytest.mark.slow
def test_concurrent_requests_handling(test_client):
    """Test that API can handle concurrent requests."""
    import concurrent.futures
    
    def make_request():
        return test_client.get("/health")
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    elapsed = time.time() - start
    
    # Should handle 50 concurrent requests in reasonable time
    assert elapsed < 5.0, f"Concurrent requests took {elapsed:.3f}s (should be < 5.0s)"
    assert all(r.status_code in [200, 503] for r in results)


@pytest.mark.performance
@pytest.mark.benchmark
def test_registry_list_performance(test_client, performance_timer):
    """Test registry list endpoint performance."""
    response = test_client.get("/api/registry/list")
    elapsed = performance_timer()
    
    # Registry list should be fast (cached)
    assert elapsed < 0.5, f"Registry list took {elapsed:.3f}s (should be < 0.5s)"


@pytest.mark.performance
@pytest.mark.benchmark
def test_orchestrator_health_performance(test_client, performance_timer):
    """Test orchestrator health check performance."""
    response = test_client.get("/api/orchestrator/health")
    elapsed = performance_timer()
    
    # Orchestrator health should respond quickly
    assert elapsed < 0.3, f"Orchestrator health took {elapsed:.3f}s (should be < 0.3s)"
