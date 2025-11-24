"""
OpenAI Safeguard Integration Helper
Easy integration of safeguards with existing OpenAI services

Per Truth Protocol:
- Rule #1: Never guess - Verify all operations
- Rule #8: Test coverage ≥90%
- Rule #13: Security baseline enforcement
"""

from collections.abc import Callable
import logging
from typing import Any

from config.unified_config import get_config
from security.openai_safeguards import (
    OpenAISafeguardManager,
    OperationType,
    SafeguardConfig,
    SafeguardLevel,
    get_safeguard_manager,
)


logger = logging.getLogger(__name__)


def create_safeguard_config_from_app_config() -> SafeguardConfig:
    """Create SafeguardConfig from application configuration"""
    config = get_config()

    # Map string level to enum
    level_mapping = {
        "strict": SafeguardLevel.STRICT,
        "moderate": SafeguardLevel.MODERATE,
        "permissive": SafeguardLevel.PERMISSIVE,
    }

    safeguard_level = level_mapping.get(config.ai.safeguard_level.lower(), SafeguardLevel.STRICT)

    return SafeguardConfig(
        level=safeguard_level,
        enforce_consequential_in_production=config.ai.enforce_production_safeguards,
        require_audit_logging=config.ai.enable_audit_logging,
        enable_rate_limiting=config.ai.enable_rate_limiting,
        max_requests_per_minute=config.ai.max_requests_per_minute,
        max_consequential_per_hour=config.ai.max_consequential_per_hour,
        enable_circuit_breaker=config.ai.enable_circuit_breaker,
        enable_request_validation=True,
        enable_monitoring=True,
        alert_on_violations=config.is_production(),
    )


def initialize_safeguards() -> OpenAISafeguardManager:
    """
    Initialize safeguard manager with application configuration

    Returns:
        Configured OpenAISafeguardManager instance
    """
    app_config = get_config()

    if not app_config.ai.enable_safeguards:
        logger.warning("⚠️  OpenAI safeguards are DISABLED. This should only be done in development.")
        return None

    safeguard_config = create_safeguard_config_from_app_config()
    manager = get_safeguard_manager(safeguard_config)

    logger.info(
        f"✅ OpenAI safeguards initialized - Level: {safeguard_config.level.value}, "
        f"Production: {app_config.is_production()}"
    )

    return manager


def validate_openai_request(
    operation_type: OperationType,
    is_consequential: bool,
    prompt: str | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    """
    Validate OpenAI API request before execution

    Args:
        operation_type: Type of operation being performed
        is_consequential: Whether operation has real-world consequences
        prompt: Optional prompt text to validate
        params: Optional request parameters

    Returns:
        (allowed, reason) - True if allowed, False with reason if denied
    """
    config = get_config()

    if not config.ai.enable_safeguards:
        return True, None

    manager = get_safeguard_manager()

    # Run async validation in sync context
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        manager.validate_request(
            operation_type=operation_type, is_consequential=is_consequential, prompt=prompt, params=params
        )
    )


def execute_with_safeguards(
    func: Callable,
    operation_type: OperationType,
    is_consequential: bool,
    prompt: str | None = None,
    params: dict[str, Any] | None = None,
    *args,
    **kwargs,
) -> Any:
    """
    Execute OpenAI API call with full safeguard protection

    Args:
        func: Function to execute
        operation_type: Type of operation
        is_consequential: Whether operation has real-world consequences
        prompt: Optional prompt text
        params: Optional request parameters
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result from func execution

    Raises:
        ValueError: If request is blocked by safeguards
        Exception: Any exception from func execution
    """
    config = get_config()

    if not config.ai.enable_safeguards:
        logger.warning("⚠️  Executing OpenAI request WITHOUT safeguards")
        return func(*args, **kwargs)

    manager = get_safeguard_manager()

    # Run async execution in sync context
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        manager.execute_with_safeguards(
            func=func,
            operation_type=operation_type,
            is_consequential=is_consequential,
            prompt=prompt,
            params=params,
            *args,
            **kwargs,
        )
    )


def get_safeguard_statistics() -> dict[str, Any]:
    """
    Get current safeguard statistics

    Returns:
        Dictionary with statistics
    """
    config = get_config()

    if not config.ai.enable_safeguards:
        return {"enabled": False}

    manager = get_safeguard_manager()
    stats = manager.get_statistics()
    stats["enabled"] = True

    return stats


def check_production_safeguards() -> tuple[bool, list[str]]:
    """
    Check if production safeguards are properly configured

    Returns:
        (valid, warnings) - True if valid, list of warning messages
    """
    config = get_config()
    warnings = []

    if not config.is_production():
        return True, []

    # Production safeguard checks
    if not config.ai.enable_safeguards:
        warnings.append("CRITICAL: Safeguards are disabled in production")

    if not config.ai.openai_is_consequential:
        warnings.append("WARNING: Consequential flag is disabled in production")

    if config.ai.safeguard_level != "strict":
        warnings.append(f"WARNING: Safeguard level is '{config.ai.safeguard_level}', should be 'strict' in production")

    if not config.ai.enable_rate_limiting:
        warnings.append("WARNING: Rate limiting is disabled in production")

    if not config.ai.enable_circuit_breaker:
        warnings.append("WARNING: Circuit breaker is disabled in production")

    if not config.ai.enable_audit_logging:
        warnings.append("WARNING: Audit logging is disabled in production")

    if not config.ai.enforce_production_safeguards:
        warnings.append("CRITICAL: Production safeguard enforcement is disabled")

    is_valid = len([w for w in warnings if w.startswith("CRITICAL")]) == 0

    if warnings:
        for warning in warnings:
            if warning.startswith("CRITICAL"):
                logger.error(f"🚨 {warning}")
            else:
                logger.warning(f"⚠️  {warning}")

    return is_valid, warnings


# Initialize safeguards on module import
_manager = initialize_safeguards()

# Check production configuration on import
if _manager:
    valid, warnings = check_production_safeguards()
    if not valid:
        logger.error("🚨 CRITICAL PRODUCTION SAFEGUARD ISSUES DETECTED - " "Review configuration immediately")


__all__ = [
    "check_production_safeguards",
    "create_safeguard_config_from_app_config",
    "execute_with_safeguards",
    "get_safeguard_statistics",
    "initialize_safeguards",
    "validate_openai_request",
]
