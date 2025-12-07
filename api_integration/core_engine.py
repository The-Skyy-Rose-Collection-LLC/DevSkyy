from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
import logging
import time
from typing import Any
import uuid

import aiohttp
from aiohttp import ClientTimeout

from api_integration.auth_manager import auth_manager, rate_limit_manager
from infrastructure.elasticsearch_manager import elasticsearch_manager
from infrastructure.redis_manager import redis_manager


"""
Core API Integration Engine
Microservices architecture with API gateway pattern, event-driven communication,
data transformation pipelines, and circuit breaker patterns for fault tolerance
"""

from api_integration.discovery_engine import (
    api_discovery_engine,
)


logger = logging.getLogger(__name__)


class RequestStatus(Enum):
    """API request status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    CIRCUIT_OPEN = "circuit_open"


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class APIRequest:
    """API request data structure"""

    request_id: str
    api_id: str
    endpoint: str
    method: str
    headers: dict[str, str]
    params: dict[str, Any]
    data: Any
    timeout: int
    retry_count: int
    max_retries: int
    created_at: datetime
    status: RequestStatus
    response_data: Any = None
    error_message: str = None
    execution_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    name: str = "default"


class CircuitBreaker:
    """Circuit breaker implementation for API fault tolerance"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable[..., Awaitable], *args, **kwargs):
        """Execute function with circuit breaker protection"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker {self.config.name} is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.config.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        return self.last_failure_time and time.time() - self.last_failure_time >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful request"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN


class DataTransformer:
    """Data transformation pipeline for API responses"""

    def __init__(self):
        self.transformers: dict[str, Callable] = {}
        self.fashion_transformers = self._setup_fashion_transformers()

    def _setup_fashion_transformers(self) -> dict[str, Callable]:
        """Setup fashion-specific data transformers"""
        return {
            "product_catalog": self._transform_product_data,
            "fashion_trends": self._transform_trend_data,
            "inventory": self._transform_inventory_data,
            "customer_analytics": self._transform_analytics_data,
            "payment_data": self._transform_payment_data,
        }

    async def transform(self, data: Any, source_api: str, target_format: str = "standard") -> dict[str, Any]:
        """Transform API response data to standard format"""

        if not data:
            return {}

        # Determine transformation type based on API category
        api_endpoint = await api_discovery_engine.discovered_apis.get(source_api)
        if api_endpoint:
            category = api_endpoint.category.value
            transformer = self.fashion_transformers.get(category)

            if transformer:
                return await transformer(data, source_api)

        # Default transformation
        return await self._default_transform(data)

    async def _transform_product_data(self, data: Any, source_api: str) -> dict[str, Any]:
        """Transform product catalog data"""

        if isinstance(data, list):
            return {
                "products": [await self._normalize_product(item) for item in data],
                "total_count": len(data),
                "source_api": source_api,
                "transformed_at": datetime.now().isoformat(),
            }
        elif isinstance(data, dict):
            return {
                "product": await self._normalize_product(data),
                "source_api": source_api,
                "transformed_at": datetime.now().isoformat(),
            }

        return {"raw_data": data, "source_api": source_api}

    async def _normalize_product(self, product_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize product data to standard format"""

        return {
            "id": product_data.get("id") or product_data.get("product_id") or product_data.get("sku"),
            "name": product_data.get("name") or product_data.get("title"),
            "description": product_data.get("description"),
            "price": product_data.get("price") or product_data.get("cost"),
            "currency": product_data.get("currency", "USD"),
            "category": product_data.get("category") or product_data.get("type"),
            "brand": product_data.get("brand") or product_data.get("vendor"),
            "images": product_data.get("images") or product_data.get("image_urls", []),
            "availability": product_data.get("available") or product_data.get("in_stock", True),
            "sizes": product_data.get("sizes") or product_data.get("variants", []),
            "colors": product_data.get("colors") or [],
            "materials": product_data.get("materials") or [],
            "sustainability_score": product_data.get("sustainability_score", 0.0),
            "tags": product_data.get("tags") or [],
            "created_at": product_data.get("created_at"),
            "updated_at": product_data.get("updated_at"),
        }

    async def _transform_trend_data(self, data: Any, source_api: str) -> dict[str, Any]:
        """Transform fashion trend data"""

        if isinstance(data, list):
            return {
                "trends": [await self._normalize_trend(item) for item in data],
                "total_count": len(data),
                "source_api": source_api,
                "transformed_at": datetime.now().isoformat(),
            }
        elif isinstance(data, dict):
            return {
                "trend": await self._normalize_trend(data),
                "source_api": source_api,
                "transformed_at": datetime.now().isoformat(),
            }

        return {"raw_data": data, "source_api": source_api}

    async def _normalize_trend(self, trend_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize trend data to standard format"""

        return {
            "id": trend_data.get("id") or trend_data.get("trend_id"),
            "name": trend_data.get("name") or trend_data.get("title"),
            "description": trend_data.get("description"),
            "category": trend_data.get("category"),
            "season": trend_data.get("season"),
            "year": trend_data.get("year", datetime.now().year),
            "popularity_score": trend_data.get("popularity") or trend_data.get("score", 0.0),
            "colors": trend_data.get("colors") or trend_data.get("color_palette", []),
            "materials": trend_data.get("materials") or [],
            "target_demographics": trend_data.get("demographics") or [],
            "geographic_relevance": trend_data.get("regions") or [],
            "social_mentions": trend_data.get("social_mentions", 0),
            "created_at": trend_data.get("created_at"),
            "updated_at": trend_data.get("updated_at"),
        }

    async def _transform_inventory_data(self, data: Any, source_api: str) -> dict[str, Any]:
        """Transform inventory data"""

        return {
            "inventory_items": data if isinstance(data, list) else [data],
            "source_api": source_api,
            "transformed_at": datetime.now().isoformat(),
        }

    async def _transform_analytics_data(self, data: Any, source_api: str) -> dict[str, Any]:
        """Transform customer analytics data"""

        return {
            "analytics": data,
            "source_api": source_api,
            "transformed_at": datetime.now().isoformat(),
        }

    async def _transform_payment_data(self, data: Any, source_api: str) -> dict[str, Any]:
        """Transform payment data"""

        return {
            "payment_data": data,
            "source_api": source_api,
            "transformed_at": datetime.now().isoformat(),
        }

    async def _default_transform(self, data: Any) -> dict[str, Any]:
        """Default data transformation"""

        return {"data": data, "transformed_at": datetime.now().isoformat()}


class APIGateway:
    """API Gateway for managing all external API communications"""

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.data_transformer = DataTransformer()
        self.request_cache: dict[str, Any] = {}

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "requests_by_api": {},
            "last_updated": datetime.now(),
        }

        logger.info("API Gateway initialized")

    def _get_circuit_breaker(self, api_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for API"""

        if api_id not in self.circuit_breakers:
            config = CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                name=f"circuit_breaker_{api_id}",
            )
            self.circuit_breakers[api_id] = CircuitBreaker(config)

        return self.circuit_breakers[api_id]

    async def make_request(
        self,
        api_id: str,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
        use_cache: bool = True,
        transform_response: bool = True,
    ) -> dict[str, Any]:
        """Make API request with full integration features"""

        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Create request object
        api_request = APIRequest(
            request_id=request_id,
            api_id=api_id,
            endpoint=endpoint,
            method=method.upper(),
            headers=headers or {},
            params=params or {},
            data=data,
            timeout=timeout,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(),
            status=RequestStatus.PENDING,
        )

        try:
            # Check cache first
            if use_cache and method.upper() == "GET":
                cached_response = await self._get_cached_response(api_request)
                if cached_response:
                    logger.info(f"Cache hit for request {request_id}")
                    return cached_response

            # Check rate limits
            can_request, _rate_info = await rate_limit_manager.can_make_request(api_id)
            if not can_request:
                api_request.status = RequestStatus.RATE_LIMITED
                api_request.error_message = "Rate limit exceeded"
                await self._log_request(api_request)

                raise Exception(f"Rate limit exceeded for API {api_id}")

            # Get circuit breaker
            circuit_breaker = self._get_circuit_breaker(api_id)

            # Make request with circuit breaker protection
            response_data = await circuit_breaker.call(self._execute_request, api_request)

            # Record successful request
            await rate_limit_manager.record_request(api_id)

            # Transform response data
            if transform_response:
                response_data = await self.data_transformer.transform(response_data, api_id)

            # Cache response
            if use_cache and method.upper() == "GET":
                await self._cache_response(api_request, response_data)

            # Update metrics
            execution_time = time.time() - start_time
            await self._update_metrics(api_id, True, execution_time)

            # Log successful request
            api_request.status = RequestStatus.SUCCESS
            api_request.response_data = response_data
            api_request.execution_time = execution_time
            await self._log_request(api_request)

            logger.info(f"API request {request_id} completed successfully in {execution_time:.2f}s")

            return {
                "success": True,
                "data": response_data,
                "request_id": request_id,
                "execution_time": execution_time,
                "api_id": api_id,
            }

        except Exception as e:
            # Update metrics
            execution_time = time.time() - start_time
            await self._update_metrics(api_id, False, execution_time)

            # Log failed request
            api_request.status = RequestStatus.FAILED
            api_request.error_message = str(e)
            api_request.execution_time = execution_time
            await self._log_request(api_request)

            logger.error(f"API request {request_id} failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "request_id": request_id,
                "execution_time": execution_time,
                "api_id": api_id,
            }

    async def _execute_request(self, api_request: APIRequest) -> Any:
        """Execute the actual API request"""

        api_request.status = RequestStatus.IN_PROGRESS

        # Get API endpoint information
        api_endpoint = api_discovery_engine.discovered_apis.get(api_request.api_id)
        if not api_endpoint:
            raise Exception(f"API endpoint not found: {api_request.api_id}")

        # Get authentication headers
        auth_headers = await auth_manager.get_auth_headers(api_request.api_id)

        # Merge headers
        headers = {**api_request.headers, **auth_headers}

        # Build full URL
        base_url = api_endpoint.base_url.rstrip("/")
        endpoint = api_request.endpoint.lstrip("/")
        full_url = f"{base_url}/{endpoint}"

        # Configure timeout
        timeout = ClientTimeout(total=api_request.timeout)

        # Make HTTP request
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.request(
                method=api_request.method,
                url=full_url,
                params=api_request.params,
                json=(api_request.data if api_request.method in ["POST", "PUT", "PATCH"] else None),
                headers=headers,
            ) as response,
        ):

            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"HTTP {response.status}: {error_text}")

            # Parse response based on content type
            content_type = response.headers.get("content-type", "").lower()

            if "application/json" in content_type:
                return await response.json()
            elif "text/" in content_type:
                return await response.text()
            else:
                return await response.read()

    async def _get_cached_response(self, api_request: APIRequest) -> dict[str, Any] | None:
        """Get cached API response"""

        cache_key = self._generate_cache_key(api_request)

        try:
            cached_data = await redis_manager.get(cache_key, prefix="api_cache")
            if cached_data:
                return cached_data
        except Exception as e:
            logger.error(f"Error retrieving cached response: {e}")

        return None

    async def _cache_response(self, api_request: APIRequest, response_data: Any):
        """Cache API response"""

        cache_key = self._generate_cache_key(api_request)

        try:
            # Cache for 1 hour by default
            await redis_manager.set(cache_key, response_data, ttl=3600, prefix="api_cache")
        except Exception as e:
            logger.error(f"Error caching response: {e}")

    def _generate_cache_key(self, api_request: APIRequest) -> str:
        """Generate cache key for API request"""

        key_data = f"{api_request.api_id}:{api_request.endpoint}:{json.dumps(api_request.params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def _log_request(self, api_request: APIRequest):
        """Log API request to Elasticsearch"""

        try:
            log_data = api_request.to_dict()
            log_data["@timestamp"] = datetime.now().isoformat()

            await elasticsearch_manager.index_document("logs", log_data, doc_id=api_request.request_id)
        except Exception as e:
            logger.error(f"Error logging request: {e}")

    async def _update_metrics(self, api_id: str, success: bool, execution_time: float):
        """Update API gateway metrics"""

        self.metrics["total_requests"] += 1

        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        # Update average response time
        if self.metrics["average_response_time"] == 0:
            self.metrics["average_response_time"] = execution_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics["average_response_time"] = (
                alpha * execution_time + (1 - alpha) * self.metrics["average_response_time"]
            )

        # Update per-API metrics
        if api_id not in self.metrics["requests_by_api"]:
            self.metrics["requests_by_api"][api_id] = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "avg_response_time": 0.0,
            }

        api_metrics = self.metrics["requests_by_api"][api_id]
        api_metrics["total"] += 1

        if success:
            api_metrics["successful"] += 1
        else:
            api_metrics["failed"] += 1

        # Update API average response time
        if api_metrics["avg_response_time"] == 0:
            api_metrics["avg_response_time"] = execution_time
        else:
            api_metrics["avg_response_time"] = 0.1 * execution_time + 0.9 * api_metrics["avg_response_time"]

        self.metrics["last_updated"] = datetime.now()

    async def get_metrics(self) -> dict[str, Any]:
        """Get API gateway metrics"""

        return {
            "gateway_metrics": self.metrics,
            "circuit_breakers": {
                api_id: {
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "last_failure_time": cb.last_failure_time,
                }
                for api_id, cb in self.circuit_breakers.items()
            },
            "cache_stats": await redis_manager.get_metrics(),
            "rate_limit_status": await rate_limit_manager.get_all_rate_limit_status(),
        }

    async def health_check(self) -> dict[str, Any]:
        """Health check for API gateway"""

        try:
            metrics = await self.get_metrics()

            # Check if any circuit breakers are open
            open_circuits = [api_id for api_id, cb in self.circuit_breakers.items() if cb.state == CircuitState.OPEN]

            # Calculate success rate
            total_requests = self.metrics["total_requests"]
            success_rate = self.metrics["successful_requests"] / total_requests if total_requests > 0 else 1.0

            status = "healthy"
            if open_circuits or success_rate < 0.9:
                status = "degraded"

            return {
                "status": status,
                "total_requests": total_requests,
                "success_rate": success_rate,
                "average_response_time": self.metrics["average_response_time"],
                "open_circuit_breakers": open_circuits,
                "active_apis": len(self.metrics["requests_by_api"]),
                "cache_enabled": True,
                "rate_limiting_enabled": True,
                "metrics": metrics,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global API gateway instance
api_gateway = APIGateway()
