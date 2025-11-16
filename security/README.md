# OpenAI API Safeguards and Guardrails

Comprehensive safety system for all OpenAI API interactions in the DevSkyy platform.

## Overview

This module implements enterprise-grade safeguards and guardrails for OpenAI API usage, ensuring:
- **Rate limiting** to prevent API abuse
- **Circuit breakers** for fault tolerance
- **Audit logging** for compliance and monitoring
- **Request validation** to block malicious inputs
- **Production enforcement** of safety standards
- **Monitoring and alerting** for violations

## Features

### 1. Configuration-Driven Safety
```python
from security.openai_safeguards import SafeguardConfig, SafeguardLevel

config = SafeguardConfig(
    level=SafeguardLevel.STRICT,
    enable_rate_limiting=True,
    max_requests_per_minute=60,
    max_consequential_per_hour=100,
    enable_circuit_breaker=True,
    enable_audit_logging=True,
    enforce_consequential_in_production=True
)
```

### 2. Multi-Layer Protection

#### Rate Limiting
- Per-minute request limits
- Separate limits for consequential operations
- Automatic cleanup of old records

#### Circuit Breaker
- Automatically opens after failure threshold
- Prevents cascading failures
- Self-healing with configurable recovery timeout

#### Audit Logging
- JSON-formatted logs for all operations
- Sanitized parameter logging (no secrets)
- Retrievable for compliance and analysis

#### Request Validation
- Prompt length limits
- Blocked keyword detection
- Empty prompt rejection
- Parameter sanitization

### 3. Production Safeguards
- Enforces `is_consequential=True` in production
- Forces STRICT safeguard level
- Alerts on violations
- Comprehensive monitoring

## Usage

### Basic Integration

```python
from security.openai_safeguard_integration import (
    execute_with_safeguards,
    validate_openai_request,
)
from security.openai_safeguards import OperationType

# Validate before execution
allowed, reason = validate_openai_request(
    operation_type=OperationType.CONTENT_GENERATION,
    is_consequential=True,
    prompt="Generate product description"
)

if not allowed:
    print(f"Request blocked: {reason}")
    return

# Execute with full safeguards
result = execute_with_safeguards(
    func=openai_api_call,
    operation_type=OperationType.CONTENT_GENERATION,
    is_consequential=True,
    prompt="Generate product description",
    params={"model": "gpt-4", "max_tokens": 500}
)
```

### Decorator Pattern

```python
from security.openai_safeguards import with_safeguards, OperationType

@with_safeguards(
    operation_type=OperationType.CODE_GENERATION,
    is_consequential=True
)
async def generate_code(prompt: str):
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### Manual Manager Usage

```python
from security.openai_safeguards import OpenAISafeguardManager, SafeguardConfig

manager = OpenAISafeguardManager(SafeguardConfig())

# Execute with safeguards
result = await manager.execute_with_safeguards(
    func=my_api_call,
    operation_type=OperationType.CUSTOMER_INTERACTION,
    is_consequential=True,
    prompt=user_input,
    params={"model": "gpt-4"}
)

# Get statistics
stats = manager.get_statistics()
print(f"Total violations: {stats['total_violations']}")
print(f"Circuit breaker state: {stats['circuit_breaker_state']}")
```

## Configuration

### Environment Variables

```bash
# Enable/disable safeguards
OPENAI_ENABLE_SAFEGUARDS=true

# Safeguard level (strict, moderate, permissive)
OPENAI_SAFEGUARD_LEVEL=strict

# Rate limiting
OPENAI_ENABLE_RATE_LIMITING=true
OPENAI_MAX_REQUESTS_PER_MINUTE=60
OPENAI_MAX_CONSEQUENTIAL_PER_HOUR=100

# Circuit breaker
OPENAI_ENABLE_CIRCUIT_BREAKER=true

# Audit logging
OPENAI_ENABLE_AUDIT_LOGGING=true

# Production enforcement
OPENAI_ENFORCE_PRODUCTION_SAFEGUARDS=true
```

### Safeguard Levels

- **STRICT** (Production default)
  - Maximum safety enforcement
  - All validations enabled
  - Production safeguards enforced
  - Alerts on all violations

- **MODERATE** (Staging)
  - Balanced safety
  - Some validations relaxed
  - Warnings instead of alerts

- **PERMISSIVE** (Development only)
  - Minimal restrictions
  - Logging only, no blocking
  - Never use in production

## Operation Types

```python
class OperationType(str, Enum):
    CONTENT_GENERATION = "content_generation"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    CUSTOMER_INTERACTION = "customer_interaction"
    SYSTEM_MODIFICATION = "system_modification"
    FINANCIAL_OPERATION = "financial_operation"
```

## Monitoring

### Get Statistics

```python
from security.openai_safeguard_integration import get_safeguard_statistics

stats = get_safeguard_statistics()
print(stats)
```

Output:
```json
{
  "enabled": true,
  "total_violations": 12,
  "recent_violations_1h": 3,
  "violations_by_severity": {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 0
  },
  "circuit_breaker_state": "closed",
  "rate_limiter_active": true,
  "config_level": "strict"
}
```

### Check Production Configuration

```python
from security.openai_safeguard_integration import check_production_safeguards

valid, warnings = check_production_safeguards()

if not valid:
    print("CRITICAL: Production safeguards misconfigured!")
    for warning in warnings:
        print(f"  - {warning}")
```

## Audit Logs

Audit logs are written to `logs/openai_audit.jsonl` in JSON Lines format:

```json
{
  "timestamp": "2025-11-13T02:30:45.123456",
  "operation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "operation_type": "content_generation",
  "is_consequential": true,
  "user_id": "user_123",
  "request_params": {
    "model": "gpt-4",
    "max_tokens": 500
  },
  "success": true,
  "execution_time_ms": 1250.5,
  "cost_estimate_usd": 0.015
}
```

## Violation Logs

Safeguard violations are logged to `logs/openai_violations.jsonl`:

```json
{
  "timestamp": "2025-11-13T02:35:12.654321",
  "violation_type": "rate_limit_exceeded",
  "severity": "high",
  "operation_type": "content_generation",
  "is_consequential": true,
  "details": {
    "reason": "Rate limit exceeded: 60 requests per minute"
  },
  "resolved": false
}
```

## Testing

Comprehensive test suite with 90%+ coverage:

```bash
# Run all safeguard tests
pytest tests/unit/test_openai_safeguards.py -v

# Run specific test class
pytest tests/unit/test_openai_safeguards.py::TestRateLimiter -v

# Run with coverage
pytest tests/unit/test_openai_safeguards.py --cov=security.openai_safeguards --cov-report=html
```

## Truth Protocol Compliance

✅ **Rule #1**: Never guess - All operations verified
✅ **Rule #5**: No secrets in code - Environment variables only
✅ **Rule #7**: Input validation and sanitization enforced
✅ **Rule #8**: Test coverage ≥90%
✅ **Rule #13**: Security baseline - AES-256-GCM, Argon2id, OAuth2+JWT

## Security Features

- ✅ No hardcoded credentials
- ✅ Sensitive data sanitization
- ✅ Rate limiting and throttling
- ✅ Circuit breaker for fault tolerance
- ✅ Comprehensive audit logging
- ✅ Production safeguard enforcement
- ✅ Request validation and sanitization
- ✅ Monitoring and alerting
- ✅ Type-safe configuration (Pydantic)
- ✅ Immutable configuration (frozen)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenAI API Request                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Safeguard Manager                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Rate Limiter                                     │   │
│  │     - Check per-minute limits                        │   │
│  │     - Check consequential limits                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  2. Request Validator                                │   │
│  │     - Validate prompt length                         │   │
│  │     - Check blocked keywords                         │   │
│  │     - Sanitize parameters                            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  3. Production Enforcer                              │   │
│  │     - Enforce consequential flag                     │   │
│  │     - Check environment                              │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  4. Circuit Breaker                                  │   │
│  │     - Execute API call                               │   │
│  │     - Track failures                                 │   │
│  │     - Automatic recovery                             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  5. Audit Logger                                     │   │
│  │     - Log all operations                             │   │
│  │     - Record violations                              │   │
│  │     - Generate metrics                               │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     OpenAI API Response                      │
└─────────────────────────────────────────────────────────────┘
```

## Best Practices

1. **Always use safeguards in production**
   ```bash
   ENVIRONMENT=production
   OPENAI_ENABLE_SAFEGUARDS=true
   OPENAI_SAFEGUARD_LEVEL=strict
   ```

2. **Set appropriate rate limits**
   - Base on your OpenAI tier limits
   - Consider your application's needs
   - Monitor and adjust as needed

3. **Monitor safeguard statistics**
   - Check violation logs regularly
   - Alert on critical violations
   - Review circuit breaker state

4. **Test with safeguards enabled**
   - Include safeguards in integration tests
   - Test rate limit handling
   - Verify circuit breaker recovery

5. **Use appropriate operation types**
   - Classify operations correctly
   - Mark consequential operations
   - Consider real-world impact

## Support

For issues or questions:
1. Check logs: `logs/openai_audit.jsonl` and `logs/openai_violations.jsonl`
2. Review configuration: `config/unified_config.py`
3. Run tests: `pytest tests/unit/test_openai_safeguards.py`
4. Check statistics: `get_safeguard_statistics()`

## License

Copyright © 2025 The Skyy Rose Collection LLC. All rights reserved.
