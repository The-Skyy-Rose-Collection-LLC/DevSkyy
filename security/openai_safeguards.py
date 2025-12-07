"""
OpenAI API Safeguards and Guardrails
Comprehensive safety system for all OpenAI API interactions

Per Truth Protocol:
- Rule #1: Never guess - Verify all operations
- Rule #5: No secrets in code
- Rule #7: Input validation and sanitization
- Rule #8: Test coverage ≥90%
- Rule #13: Security baseline - AES-256-GCM, Argon2id, OAuth2+JWT

Features:
- Configuration validation and enforcement
- Audit logging for all consequential operations
- Production environment safeguards
- Rate limiting and throttling
- Circuit breaker pattern for fault tolerance
- Request validation and sanitization
- Monitoring and alerting hooks
- Error tracking and reporting
"""

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import logging
from pathlib import Path
import time
from typing import Any

from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND MODELS
# ============================================================================


class SafeguardLevel(str, Enum):
    """Safeguard enforcement levels"""

    STRICT = "strict"  # Maximum safety, production default
    MODERATE = "moderate"  # Balanced safety
    PERMISSIVE = "permissive"  # Development/testing only


class OperationType(str, Enum):
    """Types of operations requiring safeguards"""

    CONTENT_GENERATION = "content_generation"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    CUSTOMER_INTERACTION = "customer_interaction"
    SYSTEM_MODIFICATION = "system_modification"
    FINANCIAL_OPERATION = "financial_operation"


class SafeguardViolation(BaseModel):
    """Record of a safeguard violation"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    violation_type: str
    severity: str  # critical, high, medium, low
    operation_type: OperationType
    is_consequential: bool
    details: dict[str, Any]
    stack_trace: str | None = None
    resolved: bool = False


class AuditLogEntry(BaseModel):
    """Audit log entry for consequential operations"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    operation_id: str
    operation_type: OperationType
    is_consequential: bool
    user_id: str | None = None
    ip_address: str | None = None
    request_params: dict[str, Any] = Field(default_factory=dict)
    response_summary: str | None = None
    success: bool
    error_message: str | None = None
    execution_time_ms: float
    cost_estimate_usd: float | None = None


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================


class SafeguardConfig(BaseModel):
    """Configuration for OpenAI safeguards"""

    # Enforcement level
    level: SafeguardLevel = Field(default=SafeguardLevel.STRICT)

    # Production enforcement
    enforce_consequential_in_production: bool = Field(default=True)
    require_audit_logging: bool = Field(default=True)

    # Rate limiting
    enable_rate_limiting: bool = Field(default=True)
    max_requests_per_minute: int = Field(default=60, ge=1, le=1000)
    max_consequential_per_hour: int = Field(default=100, ge=1, le=10000)

    # Circuit breaker
    enable_circuit_breaker: bool = Field(default=True)
    failure_threshold: int = Field(default=5, ge=1, le=100)
    recovery_timeout_seconds: int = Field(default=60, ge=10, le=3600)

    # Validation
    enable_request_validation: bool = Field(default=True)
    max_prompt_length: int = Field(default=100000, ge=1000, le=1000000)
    blocked_keywords: list[str] = Field(default_factory=list)

    # Monitoring
    enable_monitoring: bool = Field(default=True)
    alert_on_violations: bool = Field(default=True)

    # Audit logging
    audit_log_path: Path = Field(default=Path("logs/openai_audit.jsonl"))
    violation_log_path: Path = Field(default=Path("logs/openai_violations.jsonl"))

    @validator("level")
    def validate_level(cls, v, values):
        """Ensure production uses STRICT level"""
        import os

        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production" and v != SafeguardLevel.STRICT:
            logger.warning(
                f"⚠️  Production environment detected but safeguard level is '{v}'. "
                f"Forcing STRICT level for production safety."
            )
            return SafeguardLevel.STRICT
        return v

    class Config:
        frozen = True


# ============================================================================
# RATE LIMITER
# ============================================================================


class RateLimiter:
    """Token bucket rate limiter for API requests"""

    def __init__(self, max_per_minute: int = 60, max_consequential_per_hour: int = 100):
        self.max_per_minute = max_per_minute
        self.max_consequential_per_hour = max_consequential_per_hour

        self.requests: list[float] = []
        self.consequential_requests: list[float] = []
        self.lock = asyncio.Lock()

    async def check_rate_limit(self, is_consequential: bool = False) -> tuple[bool, str | None]:
        """
        Check if request is within rate limits

        Returns:
            (allowed, reason) - True if allowed, False with reason if denied
        """
        async with self.lock:
            now = time.time()

            # Clean old requests (older than 1 hour)
            self.requests = [ts for ts in self.requests if now - ts < 3600]
            self.consequential_requests = [ts for ts in self.consequential_requests if now - ts < 3600]

            # Check per-minute rate
            recent_requests = [ts for ts in self.requests if now - ts < 60]
            if len(recent_requests) >= self.max_per_minute:
                return False, f"Rate limit exceeded: {self.max_per_minute} requests per minute"

            # Check consequential rate if applicable
            if is_consequential:
                if len(self.consequential_requests) >= self.max_consequential_per_hour:
                    return False, f"Consequential operation limit exceeded: {self.max_consequential_per_hour} per hour"

            # Record request
            self.requests.append(now)
            if is_consequential:
                self.consequential_requests.append(now)

            return True, None


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state = CircuitBreakerState.CLOSED
        self.failures = 0
        self.last_failure_time: float | None = None
        self.lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self.lock:
            # Check if circuit is open
            if self.state == CircuitBreakerState.OPEN:
                if self.last_failure_time and time.time() - self.last_failure_time > self.recovery_timeout:
                    # Try recovery
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("🔄 Circuit breaker entering HALF_OPEN state for recovery test")
                else:
                    raise Exception("Circuit breaker is OPEN - requests are blocked")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # Success - reset or close circuit
            async with self.lock:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.CLOSED
                    self.failures = 0
                    logger.info("✅ Circuit breaker CLOSED - service recovered")

            return result

        except Exception:
            async with self.lock:
                self.failures += 1
                self.last_failure_time = time.time()

                if self.failures >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    logger.error(
                        f"🚨 Circuit breaker OPEN after {self.failures} failures. "
                        f"Blocking requests for {self.recovery_timeout}s"
                    )
            raise


# ============================================================================
# AUDIT LOGGER
# ============================================================================


class AuditLogger:
    """Comprehensive audit logging for consequential operations"""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    async def log(self, entry: AuditLogEntry):
        """Write audit log entry"""
        try:
            with open(self.log_path, "a") as f:
                f.write(entry.json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_recent_logs(self, hours: int = 24) -> list[AuditLogEntry]:
        """Retrieve recent audit logs"""
        if not self.log_path.exists():
            return []

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        logs = []

        try:
            with open(self.log_path, "r") as f:
                for line in f:
                    entry = AuditLogEntry.parse_raw(line)
                    if entry.timestamp >= cutoff:
                        logs.append(entry)
        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}")

        return logs


# ============================================================================
# REQUEST VALIDATOR
# ============================================================================


class RequestValidator:
    """Validate and sanitize OpenAI API requests"""

    def __init__(self, config: SafeguardConfig):
        self.config = config

    def validate_prompt(self, prompt: str) -> tuple[bool, str | None]:
        """Validate prompt content"""
        # Length check
        if len(prompt) > self.config.max_prompt_length:
            return False, f"Prompt exceeds maximum length of {self.config.max_prompt_length}"

        # Blocked keywords
        prompt_lower = prompt.lower()
        for keyword in self.config.blocked_keywords:
            if keyword.lower() in prompt_lower:
                return False, f"Prompt contains blocked keyword: {keyword}"

        # Empty check
        if not prompt.strip():
            return False, "Prompt cannot be empty"

        return True, None

    def sanitize_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Sanitize request parameters"""
        sanitized = params.copy()

        # Remove potentially sensitive keys
        sensitive_keys = ["api_key", "secret", "password", "token"]
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "[REDACTED]"

        return sanitized


# ============================================================================
# SAFEGUARD MANAGER
# ============================================================================


class OpenAISafeguardManager:
    """Central manager for all OpenAI API safeguards"""

    def __init__(self, config: SafeguardConfig | None = None):
        self.config = config or SafeguardConfig()

        # Initialize components
        self.rate_limiter = (
            RateLimiter(
                max_per_minute=self.config.max_requests_per_minute,
                max_consequential_per_hour=self.config.max_consequential_per_hour,
            )
            if self.config.enable_rate_limiting
            else None
        )

        self.circuit_breaker = (
            CircuitBreaker(
                failure_threshold=self.config.failure_threshold,
                recovery_timeout_seconds=self.config.recovery_timeout_seconds,
            )
            if self.config.enable_circuit_breaker
            else None
        )

        self.audit_logger = (
            AuditLogger(log_path=self.config.audit_log_path) if self.config.require_audit_logging else None
        )

        self.validator = RequestValidator(self.config)

        self.violations: list[SafeguardViolation] = []

        logger.info(
            f"🛡️  OpenAI Safeguard Manager initialized - Level: {self.config.level}, "
            f"Rate Limiting: {self.config.enable_rate_limiting}, "
            f"Circuit Breaker: {self.config.enable_circuit_breaker}, "
            f"Audit Logging: {self.config.require_audit_logging}"
        )

    async def validate_request(
        self,
        operation_type: OperationType,
        is_consequential: bool,
        prompt: str | None = None,
        params: dict[str, Any] | None = None
    ) -> tuple[bool, str | None]:
        """
        Validate request before sending to OpenAI API

        Returns:
            (allowed, reason) - True if allowed, False with reason if denied
        """
        # Check rate limits
        if self.rate_limiter:
            allowed, reason = await self.rate_limiter.check_rate_limit(is_consequential)
            if not allowed:
                await self._record_violation(
                    violation_type="rate_limit_exceeded",
                    severity="high",
                    operation_type=operation_type,
                    is_consequential=is_consequential,
                    details={"reason": reason},
                )
                return False, reason

        # Validate prompt
        if prompt and self.config.enable_request_validation:
            valid, reason = self.validator.validate_prompt(prompt)
            if not valid:
                await self._record_violation(
                    violation_type="invalid_prompt",
                    severity="medium",
                    operation_type=operation_type,
                    is_consequential=is_consequential,
                    details={"reason": reason},
                )
                return False, reason

        # Production safeguards
        if self.config.enforce_consequential_in_production:
            from config.unified_config import get_config

            config = get_config()

            if config.is_production() and not is_consequential:
                reason = "Production environment requires is_consequential=True for all operations"
                await self._record_violation(
                    violation_type="production_safeguard_violation",
                    severity="critical",
                    operation_type=operation_type,
                    is_consequential=is_consequential,
                    details={"reason": reason},
                )
                return False, reason

        return True, None

    async def execute_with_safeguards(
        self,
        func: Callable,
        operation_type: OperationType,
        is_consequential: bool,
        prompt: str | None = None,
        params: dict[str, Any] | None = None,
        *args,
        **kwargs,
    ) -> Any:
        """Execute OpenAI API call with all safeguards"""
        import uuid

        operation_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Validate request
            allowed, reason = await self.validate_request(
                operation_type=operation_type, is_consequential=is_consequential, prompt=prompt, params=params
            )

            if not allowed:
                raise ValueError(f"Request blocked by safeguards: {reason}")

            # Execute with circuit breaker
            if self.circuit_breaker:
                result = await self.circuit_breaker.call(func, *args, **kwargs)
            else:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # Log successful operation
            execution_time = (time.time() - start_time) * 1000
            if self.audit_logger:
                await self.audit_logger.log(
                    AuditLogEntry(
                        operation_id=operation_id,
                        operation_type=operation_type,
                        is_consequential=is_consequential,
                        request_params=self.validator.sanitize_params(params or {}),
                        success=True,
                        execution_time_ms=execution_time,
                    )
                )

            return result

        except Exception as e:
            # Log failed operation
            execution_time = (time.time() - start_time) * 1000
            if self.audit_logger:
                await self.audit_logger.log(
                    AuditLogEntry(
                        operation_id=operation_id,
                        operation_type=operation_type,
                        is_consequential=is_consequential,
                        request_params=self.validator.sanitize_params(params or {}),
                        success=False,
                        error_message=str(e),
                        execution_time_ms=execution_time,
                    )
                )

            raise

    async def _record_violation(
        self,
        violation_type: str,
        severity: str,
        operation_type: OperationType,
        is_consequential: bool,
        details: dict[str, Any]
    ):
        """Record safeguard violation"""
        violation = SafeguardViolation(
            violation_type=violation_type,
            severity=severity,
            operation_type=operation_type,
            is_consequential=is_consequential,
            details=details,
        )

        self.violations.append(violation)

        # Write to violation log
        try:
            self.config.violation_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config.violation_log_path, "a") as f:
                f.write(violation.json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write violation log: {e}")

        # Alert if enabled
        if self.config.alert_on_violations and severity in ["critical", "high"]:
            logger.error(
                f"🚨 SAFEGUARD VIOLATION - {severity.upper()}: {violation_type} "
                f"Operation: {operation_type}, Consequential: {is_consequential}, "
                f"Details: {details}"
            )

    def get_statistics(self) -> dict[str, Any]:
        """Get safeguard statistics"""
        recent_violations = [v for v in self.violations if (datetime.utcnow() - v.timestamp).total_seconds() < 3600]

        return {
            "total_violations": len(self.violations),
            "recent_violations_1h": len(recent_violations),
            "violations_by_severity": {
                "critical": len([v for v in recent_violations if v.severity == "critical"]),
                "high": len([v for v in recent_violations if v.severity == "high"]),
                "medium": len([v for v in recent_violations if v.severity == "medium"]),
                "low": len([v for v in recent_violations if v.severity == "low"]),
            },
            "circuit_breaker_state": self.circuit_breaker.state.value if self.circuit_breaker else None,
            "rate_limiter_active": self.rate_limiter is not None,
            "config_level": self.config.level.value,
        }


# ============================================================================
# DECORATOR FOR EASY INTEGRATION
# ============================================================================


def with_safeguards(operation_type: OperationType, is_consequential: bool = True):
    """Decorator to apply safeguards to OpenAI API calls"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = get_safeguard_manager()
            return await manager.execute_with_safeguards(
                func=func, operation_type=operation_type, is_consequential=is_consequential, *args, **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = get_safeguard_manager()
            import asyncio

            return asyncio.run(
                manager.execute_with_safeguards(
                    func=func, operation_type=operation_type, is_consequential=is_consequential, *args, **kwargs
                )
            )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# ============================================================================
# GLOBAL MANAGER INSTANCE
# ============================================================================

_safeguard_manager: OpenAISafeguardManager | None = None


def get_safeguard_manager(config: SafeguardConfig | None = None) -> OpenAISafeguardManager:
    """Get or create global safeguard manager instance"""
    global _safeguard_manager

    if _safeguard_manager is None:
        _safeguard_manager = OpenAISafeguardManager(config)

    return _safeguard_manager


def reload_safeguard_manager(config: SafeguardConfig | None = None) -> OpenAISafeguardManager:
    """Reload safeguard manager with new configuration"""
    global _safeguard_manager
    _safeguard_manager = OpenAISafeguardManager(config)
    return _safeguard_manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "AuditLogEntry",
    "OpenAISafeguardManager",
    "OperationType",
    "SafeguardConfig",
    "SafeguardLevel",
    "SafeguardViolation",
    "get_safeguard_manager",
    "reload_safeguard_manager",
    "with_safeguards",
]
