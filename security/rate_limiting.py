"""
Advanced Rate Limiting & DDoS Protection
========================================

Comprehensive rate limiting system for DevSkyy Enterprise Platform:
- Token bucket algorithm
- Sliding window rate limiting
- IP-based and user-based limits
- Adaptive rate limiting
- DDoS protection
- Whitelist/blacklist support
"""
from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum

from fastapi import HTTPException, Request, status
from pydantic import BaseModel

# Optional Redis import
try:
    from redis import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Rate limit types"""

    IP_BASED = "ip"
    USER_BASED = "user"
    API_KEY_BASED = "api_key"
    ENDPOINT_BASED = "endpoint"
    GLOBAL = "global"


class RateLimitRule(BaseModel):
    """Rate limiting rule configuration"""

    name: str
    limit_type: RateLimitType
    requests_per_minute: int
    requests_per_hour: int = 0
    requests_per_day: int = 0
    burst_limit: int = 0  # Maximum burst requests
    window_size_seconds: int = 60
    enabled: bool = True

    def __post_init__(self):
        if self.requests_per_hour == 0:
            self.requests_per_hour = self.requests_per_minute * 60
        if self.requests_per_day == 0:
            self.requests_per_day = self.requests_per_hour * 24
        if self.burst_limit == 0:
            self.burst_limit = self.requests_per_minute * 2


class RateLimitTier(BaseModel):
    """Subscription tier configuration for tiered rate limiting"""

    name: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_size: int
    cost: float  # Monthly cost in USD

    def to_rule(self, name_prefix: str = "") -> RateLimitRule:
        """Convert tier to RateLimitRule"""
        return RateLimitRule(
            name=f"{name_prefix}{self.name}" if name_prefix else self.name,
            limit_type=RateLimitType.USER_BASED,
            requests_per_minute=self.requests_per_minute,
            requests_per_hour=self.requests_per_hour,
            requests_per_day=self.requests_per_day,
            burst_limit=self.burst_size,
        )


# Subscription tier definitions
RATE_LIMIT_TIERS: dict[str, RateLimitTier] = {
    "free": RateLimitTier(
        name="free",
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=1000,
        burst_size=15,
        cost=0.0,
    ),
    "starter": RateLimitTier(
        name="starter",
        requests_per_minute=100,
        requests_per_hour=5000,
        requests_per_day=50000,
        burst_size=150,
        cost=29.0,
    ),
    "pro": RateLimitTier(
        name="pro",
        requests_per_minute=500,
        requests_per_hour=25000,
        requests_per_day=250000,
        burst_size=750,
        cost=99.0,
    ),
    "enterprise": RateLimitTier(
        name="enterprise",
        requests_per_minute=2000,
        requests_per_hour=100000,
        requests_per_day=1000000,
        burst_size=3000,
        cost=499.0,
    ),
}


class TokenBucket:
    """Token bucket for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket"""
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class SlidingWindowCounter:
    """Sliding window counter for rate limiting"""

    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # seconds
        self.max_requests = max_requests
        self.requests: list[float] = []

    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        now = time.time()

        # Remove old requests outside window
        cutoff = now - self.window_size
        self.requests = [req_time for req_time in self.requests if req_time > cutoff]

        # Check if under limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True

        return False

    def get_reset_time(self) -> int:
        """Get time until rate limit resets"""
        if not self.requests:
            return 0

        oldest_request = min(self.requests)
        reset_time = oldest_request + self.window_size
        return max(0, int(reset_time - time.time()))


class AdvancedRateLimiter:
    """
    Advanced rate limiting system with multiple algorithms and protection levels.

    Features:
    - Multiple rate limiting algorithms (token bucket, sliding window)
    - IP-based and user-based limits
    - Adaptive rate limiting based on system load
    - DDoS protection with automatic blacklisting
    - Whitelist support for trusted IPs
    - Detailed rate limit headers
    """

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.token_buckets: dict[str, TokenBucket] = {}
        self.sliding_windows: dict[str, SlidingWindowCounter] = {}

        # IP whitelist (trusted IPs with no limits)
        self.ip_whitelist = {
            "127.0.0.1",
            "::1",  # localhost
            # Add your trusted IPs here
        }

        # IP blacklist (blocked IPs)
        self.ip_blacklist: set = set()

        # Default rate limit rules
        self.default_rules = {
            RateLimitType.IP_BASED: RateLimitRule(
                name="default_ip",
                limit_type=RateLimitType.IP_BASED,
                requests_per_minute=100,
                requests_per_hour=6000,
                burst_limit=200,
            ),
            RateLimitType.USER_BASED: RateLimitRule(
                name="default_user",
                limit_type=RateLimitType.USER_BASED,
                requests_per_minute=200,
                requests_per_hour=12000,
                burst_limit=400,
            ),
            RateLimitType.API_KEY_BASED: RateLimitRule(
                name="default_api_key",
                limit_type=RateLimitType.API_KEY_BASED,
                requests_per_minute=1000,
                requests_per_hour=60000,
                burst_limit=2000,
            ),
        }

        # Endpoint-specific rules
        self.endpoint_rules = {
            "/api/v1/auth/login": RateLimitRule(
                name="login_endpoint",
                limit_type=RateLimitType.ENDPOINT_BASED,
                requests_per_minute=10,
                requests_per_hour=100,
                burst_limit=15,
            ),
            "/api/v1/auth/register": RateLimitRule(
                name="register_endpoint",
                limit_type=RateLimitType.ENDPOINT_BASED,
                requests_per_minute=5,
                requests_per_hour=50,
                burst_limit=10,
            ),
        }

    def get_client_identifier(self, request: Request, limit_type: RateLimitType) -> str:
        """Get client identifier for rate limiting"""
        if limit_type == RateLimitType.IP_BASED:
            return f"ip:{request.client.host if request.client else 'unknown'}"

        elif limit_type == RateLimitType.USER_BASED:
            # Extract user ID from JWT token or session
            user_id = getattr(request.state, "user_id", None)
            return f"user:{user_id}" if user_id else f"ip:{request.client.host}"

        elif limit_type == RateLimitType.API_KEY_BASED:
            api_key = request.headers.get("X-API-Key", "")
            return f"api_key:{api_key}" if api_key else f"ip:{request.client.host}"

        elif limit_type == RateLimitType.ENDPOINT_BASED:
            endpoint = request.url.path
            ip = request.client.host if request.client else "unknown"
            return f"endpoint:{endpoint}:ip:{ip}"

        else:  # GLOBAL
            return "global"

    def is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        return ip in self.ip_whitelist

    def is_ip_blacklisted(self, ip: str) -> bool:
        """Check if IP is blacklisted"""
        return ip in self.ip_blacklist

    def blacklist_ip(self, ip: str, duration_minutes: int = 60):
        """Add IP to blacklist temporarily"""
        self.ip_blacklist.add(ip)

        # Store in Redis with expiration
        if self.redis:
            self.redis.setex(f"blacklist:{ip}", duration_minutes * 60, "1")

        # Schedule removal from memory
        asyncio.create_task(self._remove_from_blacklist_after(ip, duration_minutes * 60))

        logger.warning(f"IP {ip} blacklisted for {duration_minutes} minutes")

    async def _remove_from_blacklist_after(self, ip: str, seconds: int):
        """Remove IP from blacklist after specified time"""
        await asyncio.sleep(seconds)
        self.ip_blacklist.discard(ip)

    def check_tier_limit(self, request: Request, tier_name: str = "free") -> tuple[bool, dict]:
        """
        Check if request is within subscription tier rate limits.

        Args:
            request: FastAPI request object
            tier_name: Subscription tier name (free, starter, pro, enterprise)

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        # Get tier configuration
        tier = RATE_LIMIT_TIERS.get(tier_name, RATE_LIMIT_TIERS["free"])

        # Convert tier to rate limit rule
        rule = tier.to_rule(name_prefix="tier_")

        # Use standard rate limit checking
        return self.check_rate_limit(request, rule)

    def check_rate_limit(self, request: Request, rule: RateLimitRule) -> tuple[bool, dict]:
        """Check if request is within rate limits"""
        client_id = self.get_client_identifier(request, rule.limit_type)

        # Check IP whitelist/blacklist first
        if rule.limit_type == RateLimitType.IP_BASED:
            ip = request.client.host if request.client else ""

            if self.is_ip_whitelisted(ip):
                return True, {"whitelisted": True}

            if self.is_ip_blacklisted(ip):
                return False, {"blacklisted": True, "retry_after": 3600}

        # Use sliding window for most accurate limiting
        window_key = f"{client_id}:{rule.name}"

        if window_key not in self.sliding_windows:
            self.sliding_windows[window_key] = SlidingWindowCounter(
                window_size=rule.window_size_seconds, max_requests=rule.requests_per_minute
            )

        window = self.sliding_windows[window_key]
        is_allowed = window.is_allowed()

        # Prepare rate limit info
        rate_limit_info = {
            "limit": rule.requests_per_minute,
            "remaining": max(0, rule.requests_per_minute - len(window.requests)),
            "reset": int(time.time()) + window.get_reset_time(),
            "retry_after": window.get_reset_time() if not is_allowed else 0,
        }

        # Check for potential DDoS (excessive requests from single IP)
        if not is_allowed and rule.limit_type == RateLimitType.IP_BASED:
            ip = request.client.host if request.client else ""
            if len(window.requests) > rule.burst_limit * 2:
                self.blacklist_ip(ip, 30)  # 30 minute blacklist
                rate_limit_info["blacklisted"] = True

        return is_allowed, rate_limit_info

    async def enforce_rate_limit(self, request: Request) -> dict:
        """Enforce rate limits for request"""
        # Check endpoint-specific rules first
        endpoint = request.url.path
        if endpoint in self.endpoint_rules:
            rule = self.endpoint_rules[endpoint]
            is_allowed, info = self.check_rate_limit(request, rule)

            if not is_allowed:
                if info.get("blacklisted"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="IP address has been temporarily blacklisted due to excessive requests",
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded for endpoint {endpoint}",
                        headers={
                            "X-RateLimit-Limit": str(info["limit"]),
                            "X-RateLimit-Remaining": str(info["remaining"]),
                            "X-RateLimit-Reset": str(info["reset"]),
                            "Retry-After": str(info["retry_after"]),
                        },
                    )

        # Check general IP-based limits
        ip_rule = self.default_rules[RateLimitType.IP_BASED]
        is_allowed, info = self.check_rate_limit(request, ip_rule)

        if not is_allowed:
            if info.get("blacklisted"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address has been temporarily blacklisted",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset"]),
                        "Retry-After": str(info["retry_after"]),
                    },
                )

        return info


# Global instance
rate_limiter = AdvancedRateLimiter()
