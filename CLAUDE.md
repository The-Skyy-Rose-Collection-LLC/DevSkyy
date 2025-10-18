# CLAUDE.md

This file provides strategic guidance to Claude Code when working with the DevSkyy repository.

---

## Context & Scope

The DevSkyy project is an AI-driven platform written in **Python 3.11+** with a **FastAPI backend** and a **Node.js frontend**. It currently scores around **B/B+** in enterprise readiness. Several agents and modules are stubbed or incomplete, and critical enterprise features—such as API versioning, robust security, webhook management, monitoring, and GDPR compliance—are missing. Python 3.11 introduces performance improvements and new features like finer-grained error locations and up to 10–60% speed increases over Python 3.10; use these capabilities to improve the codebase.

---

## Guiding Principles (Truth Protocol)

1. **Never guess syntax or APIs.** Base all code on verifiable, tested implementations and official documentation.
2. **Specify exact versions** for language, frameworks, and dependencies. E.g. Python 3.11+, FastAPI 0.104, Node.js 18.x.
3. **Cite authoritative sources** (e.g., RFC 7519 for JWT, NIST SP 800-38D for AES-GCM, Microsoft API design guidelines for REST versioning).
4. **State uncertainty clearly.** Use "I cannot confirm without testing" where needed.
5. **Prioritize security and maintainability.** Avoid hard-coded secrets, enforce RBAC, and implement comprehensive input validation.
6. **Document and test thoroughly.** Provide unit tests and integration tests covering edge cases, and generate OpenAPI schemas.

---

## Completion Plan

### 1. Audit the Current Codebase

- Decompress the repository, identify all `TODO` and `FIXME` markers, and catalogue incomplete agents (e.g., `cache_manager.py`, `blockchain_nft_luxury_assets.py`, `database_optimizer.py`).
- Generate a checklist of unimplemented methods and missing endpoints. Document assumptions and potential risks.

### 2. Implement API Versioning & Naming

- Create a structured `/api/v1/` namespace and migrate existing endpoints. Follow Microsoft's guidance: "A web API that implements versioning can indicate the features and resources that it exposes, and a client application can submit requests that are directed to a specific version". Use URI versioning (`/api/v1/users`, `/api/v2/users`), and maintain backward compatibility.
- Provide clear deprecation policies and migration paths for future versions.

### 3. Integrate Enterprise-Grade Security

- **Authentication**: Implement JWT/OAuth2 with access tokens (30 min expiry) and refresh tokens (7 day expiry). Use well-maintained libraries like `pyjwt` and `fastapi-users`. Cite RFC 7519 when implementing JWT.
- **Authorization**: Define RBAC roles (Super Admin, Admin, Developer, API User, Read-Only) and enforce them across all endpoints.
- **Encryption**: Replace any insecure XOR schemes with AES-256-GCM (see NIST SP 800-38D) for data at rest. Use PBKDF2 or Argon2 for key derivation and password hashing.
- **Input Validation & Sanitization**: Incorporate SQL injection prevention, XSS filtering, and command/path traversal protection. Implement Content Security Policy headers.
- **Secrets Management**: Load API keys and secrets from environment variables; never commit sensitive data.

### 4. Complete and Expose All Agents

- For each backend and frontend agent, implement missing methods with full docstrings, type hints, and error handling. Provide descriptive logs and return structured errors.
- Develop REST endpoints for each agent (e.g., `brand_intelligence`, `social_media_automation`, `email_sms_automation`, `customer_service`, `blockchain_nft_assets`), ensuring consistent request/response patterns and authentication.
- Add batch operations that allow clients to execute multiple agent actions in one request, with support for asynchronous processing and transactional rollback.

### 5. Build Webhook and Event Systems

- Create a webhooks module that supports registering webhooks, verifying HMAC signatures, retrying failed deliveries with exponential backoff, and logging delivery history.
- Provide API endpoints:
  - `POST /api/v1/webhooks/subscriptions` – Create a subscription.
  - `GET /api/v1/webhooks/subscriptions` – List subscriptions.
  - `DELETE /api/v1/webhooks/subscriptions/{id}` – Delete a subscription.
  - `POST /api/v1/webhooks/test` – Send test payloads.
  - `GET /api/v1/webhooks/history` – View delivery history.

### 6. Implement Observability & Monitoring

- Create a monitoring module to collect metrics (CPU, memory, API latency, request counts) and expose them via `/api/v1/monitoring` endpoints.
- Implement health checks and readiness probes.
- Integrate with Prometheus/Grafana or a similar stack.

### 7. Ensure Compliance & Privacy

- Implement GDPR-compliant endpoints: `GET /api/v1/gdpr/export` (export user data) and `DELETE /api/v1/gdpr/delete` (delete user data).
- Define data retention and auditing policies.
- Provide logging for security events, authentication attempts, and data access.

### 8. Strengthen Testing & Documentation

- Write unit tests for each agent and endpoint, covering successful paths and edge cases (e.g., missing parameters, invalid tokens).
- Use FastAPI's built-in OpenAPI generation to document all endpoints. Provide examples and schemas in the repository.
- Maintain a `CHANGELOG.md` and upgrade guides for each release.

### 9. Deployment & Continuous Integration

- Update Dockerfiles and docker-compose setup for development and production environments.
- Configure CI pipelines (GitHub Actions) to run tests, linting, security scans, and build artifacts.
- Document environment variables (`.env`) and provide secure templates.

---

## Verification & Citations

At each step, consult official documentation to verify API usage and security configurations. For example, when implementing API versioning, follow the rationale that "a web API should continue to support existing client applications while allowing new clients to use new features". For Python upgrades, note that Python 3.11 offers features like finer-grained error locations and performance gains; use them to optimize error handling and throughput.

---

## Deliverables

- A fully implemented and tested DevSkyy repository with all agents active and endpoints exposed under `/api/v1/`.
- Comprehensive documentation (README, API reference, deployment guides).
- Automated test suite and CI/CD pipeline.

---

## Caveats & Risks

- Some modules may depend on external services (e.g., payment gateways); ensure proper sandbox credentials.
- Performance overhead from added security and monitoring should be measured and optimized.
- Backwards compatibility must be maintained; introduce breaking changes only in new versions.

---

## Closing Note

Follow the **Truth Protocol** rigorously: never invent APIs, always cite official sources, and state uncertainties. When decisions involve trade-offs (e.g., versioning strategy), explain the rationale, advantages, and drawbacks clearly.

---

## Development Commands

### Running the Application

```bash
# Development mode with auto-reload
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Production mode with multiple workers
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With Docker
docker-compose up -d
```

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest --cov=agent --cov=security --cov=api tests/

# Run production safety check (comprehensive validation)
python production_safety_check.py
```

### Security & Dependencies

```bash
# Security audit (check for vulnerabilities)
pip-audit

# Update dependencies safely
pip install --upgrade -r requirements.txt

# Check code quality
black . && flake8 . && mypy agent/
```

---

## Environment Configuration

### Required Variables

```bash
# Security (CRITICAL - Generate secure keys)
JWT_SECRET_KEY=your-secret-key-32-chars-min
ENCRYPTION_MASTER_KEY=your-base64-encoded-key

# AI Models (Required for agents)
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-key  # Optional but recommended

# Database (Optional - defaults to SQLite)
DATABASE_URL=postgresql://user:pass@localhost:5432/devskyy
```

### Optional Variables

```bash
# WordPress Integration
WORDPRESS_URL=https://your-site.com
WORDPRESS_API_KEY=your-api-key

# Features
META_ACCESS_TOKEN=your-token      # Social media automation
ELEVENLABS_API_KEY=your-key       # Voice/audio features
```

---

## API Documentation

When server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

---

## Documentation References

- **Production Deployment**: `PRODUCTION_DEPLOYMENT.md`
- **Enterprise Upgrade Details**: `ENTERPRISE_UPGRADE_COMPLETE.md`
- **API Integration Guide**: `ENTERPRISE_API_INTEGRATION.md`
- **Quick Reference**: `QUICK_REFERENCE.md`
- **Security Reports**: `FINAL_SECURITY_STATUS.md`, `ZERO_VULNERABILITIES_ACHIEVED.md`
