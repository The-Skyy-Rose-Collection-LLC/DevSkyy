# DevSkyy Unified Configuration System

Enterprise-grade configuration management for the DevSkyy Platform.

## Features

- ✅ **Unified Configuration** - Single source of truth for all configuration
- ✅ **Clear Precedence** - Environment variables → .env → defaults
- ✅ **Validation** - Pydantic models with type checking and constraints
- ✅ **Security** - No secrets in code, environment variables only
- ✅ **Type Safety** - Full type hints and IDE autocomplete
- ✅ **Immutability** - Configurations are frozen after creation
- ✅ **Documentation** - Self-documenting with clear field descriptions

## Configuration Precedence

Configurations are loaded in this order (highest to lowest priority):

1. **Environment Variables** (highest priority)
2. **.env File**
3. **Config Class Defaults**
4. **Runtime Overrides** (lowest priority)

## Usage

### Basic Usage

```python
from config import get_config

# Get configuration instance
config = get_config()

# Access configuration values
db_url = config.database.url
secret_key = config.security.secret_key
log_level = config.logging.level

# Check environment
if config.is_production():
    # Production-specific logic
    pass
```

### Environment-Specific Configuration

```python
from config import get_config

# Development
dev_config = get_config("development")

# Production
prod_config = get_config("production")

# Testing
test_config = get_config("testing")
```

### Validation

```python
from config import get_config, validate_production_config

config = get_config("production")

# Validate production configuration
errors = validate_production_config(config)

if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Configuration is valid for production")
```

### Export Configuration

```python
from config import get_config

config = get_config()

# Export as dictionary (sensitive data excluded)
config_dict = config.to_dict()
print(config_dict)
```

## Configuration Sections

### Database Configuration

```python
config.database.url              # Database URL
config.database.pool_size        # Connection pool size
config.database.max_overflow     # Max overflow connections
config.database.pool_timeout     # Connection timeout
config.database.pool_recycle     # Connection recycle time
config.database.pool_pre_ping    # Pre-ping before using connection
```

**Environment Variables:**
- `DATABASE_URL` - Full database URL (highest priority)
- `NEON_DATABASE_URL` - Neon serverless PostgreSQL URL
- `SUPABASE_DATABASE_URL` - Supabase PostgreSQL URL
- `PLANETSCALE_DATABASE_URL` - PlanetScale MySQL URL
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Individual credentials
- `DB_POOL_SIZE` - Connection pool size (default: 5)
- `DB_MAX_OVERFLOW` - Max overflow connections (default: 10)

### Security Configuration

```python
config.security.secret_key                    # JWT secret key
config.security.algorithm                     # JWT algorithm
config.security.access_token_expire_minutes   # Access token expiry
config.security.refresh_token_expire_days     # Refresh token expiry
config.security.password_hash_algorithm       # Password hashing algorithm
config.security.min_password_length           # Minimum password length
config.security.max_login_attempts            # Max login attempts before lockout
```

**Environment Variables:**
- `SECRET_KEY` - **REQUIRED in production** - JWT secret key (min 32 chars)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiry (default: 30)
- `PASSWORD_HASH_ALGORITHM` - Hashing algorithm (default: argon2id)
- `MIN_PASSWORD_LENGTH` - Min password length (default: 12)

### Logging Configuration

```python
config.logging.level                   # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
config.logging.format                  # Log format (json, console)
config.logging.enable_console          # Enable console logging
config.logging.enable_file             # Enable file logging
config.logging.log_dir                 # Log directory
config.logging.max_file_size_mb        # Max log file size
config.logging.backup_count            # Number of backup log files
config.logging.enable_correlation_id   # Enable correlation IDs
config.logging.sanitize_sensitive_data # Sanitize sensitive data in logs
```

**Environment Variables:**
- `LOG_LEVEL` - Log level (default: INFO)
- `LOG_FORMAT` - Log format (default: json)
- `LOG_ENABLE_CONSOLE` - Enable console (default: true)
- `LOG_ENABLE_FILE` - Enable file logging (default: true)
- `LOG_DIR` - Log directory (default: logs)

### Redis Configuration

```python
config.redis.url                    # Redis URL
config.redis.max_connections        # Max connections
config.redis.socket_timeout         # Socket timeout
config.redis.default_ttl            # Default TTL for cached items
```

**Environment Variables:**
- `REDIS_URL` - Redis URL (default: redis://localhost:6379)
- `REDIS_MAX_CONNECTIONS` - Max connections (default: 50)
- `REDIS_DEFAULT_TTL` - Default TTL in seconds (default: 3600)

### CORS Configuration

```python
config.cors.origins              # Allowed origins
config.cors.allow_credentials    # Allow credentials
config.cors.allow_methods        # Allowed HTTP methods
config.cors.allow_headers        # Allowed headers
```

**Environment Variables:**
- `CORS_ORIGINS` - Comma-separated origins (default: http://localhost:3000,http://localhost:5173)
- `CORS_ALLOW_CREDENTIALS` - Allow credentials (default: true)
- `CORS_METHODS` - Allowed methods (default: GET,POST,PUT,DELETE,OPTIONS)
- `CORS_HEADERS` - Allowed headers (default: Content-Type,Authorization,X-Requested-With)

### Performance Configuration

```python
config.performance.max_content_length_mb  # Max request size
config.performance.request_timeout_seconds # Request timeout
config.performance.worker_count            # Worker processes
config.performance.enable_gzip             # Enable GZIP compression
```

**Environment Variables:**
- `MAX_CONTENT_LENGTH_MB` - Max content length (default: 16)
- `REQUEST_TIMEOUT_SECONDS` - Request timeout (default: 300)
- `WORKER_COUNT` - Worker count (default: 4)
- `ENABLE_GZIP` - Enable GZIP (default: true)

### AI Configuration

```python
config.ai.openai_api_key      # OpenAI API key
config.ai.anthropic_api_key   # Anthropic API key
config.ai.default_model       # Default AI model
config.ai.max_tokens          # Max tokens per request
config.ai.temperature         # Model temperature
```

**Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `AI_DEFAULT_MODEL` - Default model (default: claude-sonnet-4-5)
- `AI_MAX_TOKENS` - Max tokens (default: 4096)
- `AI_TEMPERATURE` - Temperature (default: 0.7)

## Environment Variables Quick Reference

### Required in Production

```bash
SECRET_KEY="your-secure-secret-key-min-32-chars"
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"
```

### Recommended

```bash
# Environment
ENVIRONMENT=production

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30
PASSWORD_HASH_ALGORITHM=argon2id

# Database
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Optional

```bash
# Redis
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=50

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Performance
WORKER_COUNT=4
ENABLE_GZIP=true
```

## Security Best Practices

1. ✅ **Never commit secrets to git** - Use `.env` file (add to `.gitignore`)
2. ✅ **Use strong SECRET_KEY** - Min 32 chars, generated with `secrets.token_urlsafe(32)`
3. ✅ **Rotate secrets regularly** - Change SECRET_KEY periodically
4. ✅ **Use environment-specific configs** - Different secrets for dev/staging/prod
5. ✅ **Validate production config** - Run `validate_production_config()` before deployment
6. ✅ **Enable sensitive data sanitization** - Keep `LOG_SANITIZE_SENSITIVE=true`
7. ✅ **Use secure password hashing** - Argon2id is recommended (default)

## Migration from Old Config Files

### Before (Multiple Config Files)

```python
# Old way - scattered configuration
from config import Config
from database_config import DATABASE_URL
from logging_config import setup_logging

config = Config()
db_url = DATABASE_URL
logger = setup_logging()
```

### After (Unified Config)

```python
# New way - unified configuration
from config import get_config

config = get_config()
db_url = config.database.url
log_level = config.logging.level
```

## Testing

```python
from config import get_config, reload_config

# Get test configuration
config = get_config("testing")

# Reload configuration (useful for testing different scenarios)
config = reload_config("testing")

# Validate
errors = validate_production_config(config)
assert len(errors) == 0
```

## Troubleshooting

### Error: SECRET_KEY must be at least 32 characters

**Solution:**
```bash
# Generate a secure key
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Set in environment
export SECRET_KEY="generated-key-here"
```

### Error: Invalid environment

**Solution:**
Environment must be one of: `development`, `production`, `testing`

```bash
export ENVIRONMENT=production
```

### Warning: Using auto-generated SECRET_KEY for development

This is normal in development. Set `SECRET_KEY` environment variable to suppress warning.

## Truth Protocol Compliance

This configuration system follows the DevSkyy Truth Protocol:

- ✅ **Rule #1** - Never guess: All configurations have explicit defaults and validation
- ✅ **Rule #5** - No secrets in code: All secrets must be in environment variables
- ✅ **Rule #9** - Document all: Comprehensive documentation with examples
- ✅ **Rule #11** - Verified languages: Python 3.11.* only
- ✅ **Rule #12** - Performance SLOs: Configuration optimized for P95 < 200ms

## Support

For issues or questions, refer to:
- Main documentation: `/CLAUDE.md`
- Truth Protocol: `/CLAUDE.md#truth-protocol`
- Security guide: `/SECURITY_CONFIGURATION_GUIDE.md`
