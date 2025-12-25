"""
DevSkyy Core Utilities
======================

Performance-optimized utilities following industry best practices from:
- FastAPI Best Practices (zhanymkanov/fastapi-best-practices)
- Python LLM Caching Strategies (instructor)
- Production-grade async patterns

Modules:
- performance: Caching, connection pooling, lazy imports
- constants: Application-wide constants
"""

from .performance import (
    AsyncConnectionPool,
    CacheMetrics,
    HierarchicalCache,
    LazyImport,
    async_lru_cache,
    cached_property,
    instructor_cache,
    timed_lru_cache,
)

__all__ = [
    "instructor_cache",
    "timed_lru_cache",
    "async_lru_cache",
    "cached_property",
    "CacheMetrics",
    "HierarchicalCache",
    "AsyncConnectionPool",
    "LazyImport",
]
