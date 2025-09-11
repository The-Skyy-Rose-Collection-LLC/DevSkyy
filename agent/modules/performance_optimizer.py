import asyncio
import redis
import logging
from typing import Dict, Any, Optional
from functools import wraps
import json
import time
from datetime import datetime, timedelta
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Advanced performance optimization system with caching and connection pooling."""
    
    def __init__(self):
        self.redis_client = None
        self.cache_ttl = 300  # 5 minutes default TTL
        self.connection_pool = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using in-memory cache: {e}")
            self.redis_client = None
            self._memory_cache = {}
    
    def cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key for function call."""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.redis_client:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            else:
                # Fallback to memory cache
                if key in self._memory_cache:
                    cached_data = self._memory_cache[key]
                    if cached_data['expires'] > time.time():
                        return cached_data['value']
                    else:
                        del self._memory_cache[key]
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def set_cache(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self.cache_ttl
            if self.redis_client:
                return self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                # Fallback to memory cache
                self._memory_cache[key] = {
                    'value': value,
                    'expires': time.time() + ttl
                }
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def cached(self, ttl: int = None, key_prefix: str = ""):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = f"{key_prefix}:{self.cache_key(func.__name__, *args, **kwargs)}"
                
                # Try to get from cache
                cached_result = self.get_from_cache(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                self.set_cache(cache_key, result, ttl)
                logger.debug(f"Cached result for {func.__name__}")
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                cache_key = f"{key_prefix}:{self.cache_key(func.__name__, *args, **kwargs)}"
                
                # Try to get from cache
                cached_result = self.get_from_cache(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set_cache(cache_key, result, ttl)
                logger.debug(f"Cached result for {func.__name__}")
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def rate_limit(self, max_calls: int = 100, time_window: int = 60):
        """Rate limiting decorator."""
        def decorator(func):
            call_counts = {}
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                now = time.time()
                key = f"rate_limit:{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Clean old entries
                call_counts[key] = [call_time for call_time in call_counts.get(key, []) 
                                  if now - call_time < time_window]
                
                if len(call_counts[key]) >= max_calls:
                    raise Exception(f"Rate limit exceeded for {func.__name__}")
                
                call_counts[key].append(now)
                return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                now = time.time()
                key = f"rate_limit:{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Clean old entries
                call_counts[key] = [call_time for call_time in call_counts.get(key, []) 
                                  if now - call_time < time_window]
                
                if len(call_counts[key]) >= max_calls:
                    raise Exception(f"Rate limit exceeded for {func.__name__}")
                
                call_counts[key].append(now)
                return func(*args, **kwargs)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def connection_pool(self, max_connections: int = 10):
        """Connection pooling decorator."""
        def decorator(func):
            pool = asyncio.Semaphore(max_connections)
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with pool:
                    return await func(*args, **kwargs)
            
            return async_wrapper
        return decorator
    
    def performance_monitor(self):
        """Performance monitoring decorator."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache entries matching pattern."""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # Clear memory cache
                if pattern == "*":
                    self._memory_cache.clear()
                    return len(self._memory_cache)
                else:
                    keys_to_delete = [k for k in self._memory_cache.keys() if pattern.replace("*", "") in k]
                    for key in keys_to_delete:
                        del self._memory_cache[key]
                    return len(keys_to_delete)
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
        return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    "type": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1)
                }
            else:
                return {
                    "type": "memory",
                    "cached_items": len(self._memory_cache),
                    "memory_usage": "unknown"
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

# Convenience decorators
def cached(ttl: int = None, key_prefix: str = ""):
    return performance_optimizer.cached(ttl, key_prefix)

def rate_limited(max_calls: int = 100, time_window: int = 60):
    return performance_optimizer.rate_limit(max_calls, time_window)

def connection_pooled(max_connections: int = 10):
    return performance_optimizer.connection_pool(max_connections)

def performance_monitored():
    return performance_optimizer.performance_monitor()