# CLAUDE.md — DevSkyy Enterprise Orchestration Guide

**Claude Code** operates under the **Truth Protocol** for DevSkyy's enterprise multi-agent platform.

**Version**: 5.2.0-enterprise | **Status**: Production-Ready ✅ | **Last Updated**: 2025-11-17

## Stack (Verified & Pinned)

**Backend**:
- Python 3.11.9+ (FastAPI 0.120.0+ per CVE-2025-62727)
- FastAPI ~0.119.0 (ASGI web framework)
- SQLAlchemy ~2.0.36 (ORM: SQLite, PostgreSQL, MySQL)
- Pydantic >=2.9.0,<3.0.0 (Schema validation)

**AI/ML**:
- Anthropic ~0.69.0 (Claude API integration)
- OpenAI ~2.7.2 (GPT models)
- torch>=2.8.0,<2.9.0 (PyTorch, CVE-2025-3730 fixed)
- transformers ~4.57.1 (Hugging Face models)

**Database**:
- PostgreSQL 15+ (production recommended)
- Neon, Supabase, or PlanetScale support

**Frontend**:
- Node 18+ / TypeScript 5+
- Docker + Docker Compose

**Infrastructure**:
- GitHub Actions (CI/CD)
- Kubernetes (optional)
- Docker (containerization)
- Redis 7+ (caching)

## Truth Protocol (15 Rules - 100% Enforced)

### Rule #1: Never Guess
- Verify all syntax, APIs, security from **official docs**
- All citations traceable to source specifications
- Example: PyJWT per RFC 7519, cryptography per NIST SP 800-38D

### Rule #2: Version Strategy
**For compatible releases**: Use `~=` (e.g., `fastapi~=0.119.0`)
**For security-critical packages**: Use `>=,<` (e.g., `cryptography>=46.0.3,<47.0.0`)
- Packages: cryptography, PyJWT, defusedxml, bcrypt, argon2-cffi
- Generate lock files for reproducible deployments
- Review dependencies monthly or when CVEs detected
- Security packages must allow patch updates (CVE/hotfix)

### Rule #3: Cite Standards
- **RFC 7519** (JWT): PyJWT ~2.10.1
- **NIST SP 800-38D** (AES-GCM): cryptography >=46.0.3
- **NIST SP 800-132** (PBKDF2): Implemented in password hashing
- **OWASP Top 10**: Addressed in input validation, security headers
- **CWE** (Common Weakness Enumeration): Tracked for each fix

### Rule #4: State Uncertainty
When unable to verify: Use `I cannot confirm without testing.`
- Include reason (missing test, unverified dependency, etc.)
- Provide action items for verification
- Never assume behavior

### Rule #5: No Secrets in Code
- ✅ All API keys in `.env` variables (not in `.env.example`)
- ✅ Database passwords via `DB_PASSWORD` env var
- ✅ JWT secrets via `JWT_SECRET` env var
- ✅ `.env` files in `.gitignore`
- ✅ No defaults except in tests
- Pre-commit hook: detect-secrets scans all commits

### Rule #6: RBAC Roles (5-Tier)
1. **SuperAdmin**: Full access (deployment, security configs)
2. **Admin**: Configuration, user management
3. **Developer**: Code access, agent management
4. **APIUser**: API access only (external integrations)
5. **ReadOnly**: Read-only monitoring/audit

Implemented in: `security/jwt_auth.py`, `security/input_validation.py`

### Rule #7: Input Validation
- **Pydantic schemas** for all user input (required)
- **CSP headers** for browser-based UI
- **SQL parameters** (SQLAlchemy ORM, no string formatting)
- **URL sanitization** (defusedxml for XML parsing)
- Rate limiting: `slowapi` at 100/minute per IP

### Rule #8: Test Coverage ≥90%
- Unit tests: < 100ms per test
- Integration tests: < 1s per test
- API tests: < 500ms per endpoint
- Security tests: Pass/fail (no latency SLO)
- Coverage requirement: `pytest --cov-fail-under=90`
- Command: `pytest --cov=. --cov-report=html`

### Rule #9: Document All
- **Docstrings** (Google-style): All functions, classes, modules
- **Type hints** (required): All function signatures
- **OpenAPI/Swagger**: Auto-generated from FastAPI app
- **Markdown files**: README.md, SECURITY.md, CONTRIBUTING.md
- **CHANGELOG**: Every release documented
- Auto-generation: `python scripts/generate_openapi.py`

### Rule #10: No-Skip Rule (Error Handling)
**Policy**: Log errors and **continue processing**
- Every error logged to JSON error ledger: `/artifacts/error-ledger-<run_id>.json`
- PII sanitization in logs (password, api_key, token redacted)
- Fallback behavior defined (not returning 500 on non-critical errors)
- Implemented in: `core/enterprise_error_handler.py`
- Per error: error_id, severity, component, action (continue/halt)

### Rule #11: Verified Languages
- **Python 3.11+**: Enforced in `pyproject.toml` (requires-python = ">=3.11")
- **TypeScript 5+**: Enforced in `package.json` (node >=18)
- **SQL**: Only parameterized queries (SQLAlchemy, not string formatting)
- **Bash**: Approved for scripts only (tested on Linux)
- **No C/C++/Rust**: Unless explicitly approved for performance

### Rule #12: Performance SLOs
- **P95 Latency**: < 200ms (verified in CI/CD load tests)
- **Error Rate**: < 0.5% (monitoring in production)
- **Uptime**: 99.5% SLA (RTO < 5min, RPO < 1min)
- **Zero Secrets**: No credentials in logs, error messages, or responses
- Testing: `pytest tests/performance/` for baseline validation

### Rule #13: Security Baseline
**Encryption**: AES-256-GCM (NIST SP 800-38D)
- Implementation: `cryptography` >=46.0.3,<47.0.0
- Key management: Environment variable rotation

**Password Hashing**: Argon2id + bcrypt
- Argon2id: `argon2-cffi` >=23.1.0,<24.0.0
- bcrypt: `bcrypt` >=4.2.1,<5.0.0
- Iterations: 100,000 for PBKDF2

**Authentication**: OAuth2 + JWT (RFC 7519)
- JWT: `PyJWT` ~2.10.1
- Token expiry: 1 hour (access), 7 days (refresh)
- Algorithm: HS256 (symmetric) or RS256 (asymmetric)

**XXE Protection**: defusedxml
- XML-RPC: monkey_patch() on startup
- Parsers: ElementTree, minidom, pulldom, SAX secured

### Rule #14: Error Ledger Required
**Generated automatically** on every CI run and deployment:
```json
{
  "timestamp": "2025-11-17T19:00:00Z",
  "run_id": "abc123def456",
  "errors": [
    {
      "error_id": "err_123",
      "error_type": "DatabaseConnectionError",
      "severity": "HIGH",
      "message": "Failed to connect to primary database",
      "component": "infrastructure.database",
      "action": "continue"
    }
  ],
  "summary": {
    "total": 1,
    "critical": 0,
    "high": 1,
    "medium": 0,
    "low": 0
  }
}
```
**Location**: `/artifacts/error-ledger-<run_id>.json`
**Retention**: 365 days (GitHub Actions artifacts)
**CI/CD Integration**: Automatic generation in `enterprise-pipeline.yml`

### Rule #15: No Placeholders
- ❌ No `TODO` comments (create GitHub issue instead)
- ❌ No `print()` statements (use `logging` module)
- ❌ No `pass` (except in abstract methods)
- ❌ No unused imports (Ruff auto-fixes)
- ❌ No dead code (Vulture detection)
- ✅ Every line executes or is verified (via tests)

---

## Enterprise Pipeline

```
Ingress
    ↓
[Validation] - Pydantic schema enforcement, CSP headers
    ↓
[Authentication] - JWT token validation, OAuth2 scopes
    ↓
[Authorization] - RBAC role check (6 roles)
    ↓
[Logic] - Business logic with error handling
    ↓
[Encryption] - AES-256-GCM for sensitive data
    ↓
[Output] - Response serialization, masking
    ↓
[Observability] - Structured logging, error ledger, metrics
```

---

## Orchestration Workflow

**PLAN** → **BUILD** → **TEST** → **REVIEW** → **DEPLOY** → **MONITOR** → **HEAL** → **LEARN** → **REPORT**

### 1. PLAN
- Requirements gathering
- Architecture design per Truth Protocol
- Dependency selection (verified packages only)

### 2. BUILD
- Code implementation with type hints
- Pre-commit hooks validation (Black, Ruff, MyPy)
- Docstring completion

### 3. TEST
- Unit tests (coverage ≥90%)
- Integration tests
- Security tests (OWASP, CWE)
- Performance tests (P95 < 200ms)

### 4. REVIEW
- Code review (≥2 approvals)
- Security review
- Performance review

### 5. DEPLOY
- Docker image build + scan (Trivy)
- Artifact signing (Cosign)
- Rolling deployment
- Health checks

### 6. MONITOR
- Error ledger tracking
- Performance metrics (Prometheus)
- Error rate monitoring (< 0.5%)
- Alert escalation

### 7. HEAL
- Automatic rollback on failures
- Incident response
- Root cause analysis

### 8. LEARN
- Retrospectives
- Documentation updates
- Process improvements

### 9. REPORT
- CHANGELOG updates
- Release notes
- Deployment summary

---

## CI/CD Pipeline (7 Stages)

**Platform**: GitHub Actions
**Branch**: `claude/*` (feature branches)
**Main Triggers**: Push, Pull Request, workflow_dispatch

### Stage 1: Code Quality & Linting
- **Tool**: Ruff 0.8.0
- **Target**: Python 3.11
- **Pass Criteria**: Clean (0 blocking issues)
- **Output**: GitHub annotations
- **Timeout**: 10 minutes

### Stage 2: Type Checking
- **Tool**: MyPy 1.14.0
- **Target**: Strict mode
- **Pass Criteria**: No type errors
- **Output**: Error report
- **Timeout**: 15 minutes

### Stage 3: Security Scanning
- **Tools**: Bandit, Safety, pip-audit
- **Target**: All dependencies
- **Pass Criteria**: No HIGH/CRITICAL CVEs
- **Output**: JSON report
- **Timeout**: 15 minutes

### Stage 4: Tests & Coverage
- **Tool**: Pytest 8.0+
- **Matrix**: unit, integration, api
- **Pass Criteria**: ≥90% coverage
- **Services**: PostgreSQL 15, Redis 7
- **Output**: Codecov integration
- **Timeout**: 30 minutes

### Stage 5: Docker Build & Security Scan
- **Builder**: Docker Buildx
- **Registry**: ghcr.io (GitHub Container Registry)
- **Scanner**: Trivy
- **Signing**: Cosign (keyless OIDC)
- **Pass Criteria**: No HIGH/CRITICAL vulnerabilities
- **Timeout**: 20 minutes

### Stage 6: Truth Protocol Compliance
- **Checks**: All 15 rules verified
- **Artifacts**: Error ledger JSON
- **Retention**: 365 days
- **Pass Criteria**: 15/15 rules passed
- **Timeout**: 5 minutes

### Stage 7: Pipeline Summary & Notifications
- **Output**: Job matrix summary
- **Format**: Markdown summary in GitHub Actions
- **Notifications**: Slack, Email (optional)
- **Timeout**: 5 minutes

---

## Release Gates (All Must Pass)

✅ **Code Quality**: Ruff clean, Black formatted, MyPy typed
✅ **Test Coverage**: ≥90% coverage verified
✅ **Security**: No HIGH/CRITICAL CVEs detected
✅ **Error Ledger**: Generated with 0 critical errors
✅ **OpenAPI**: Valid spec generated and validated
✅ **Docker**: Signed image built and scanned
✅ **Performance**: P95 < 200ms verified
✅ **Documentation**: CHANGELOG.md updated

---

## Deliverables (Every Release)

1. **Code + Tests**
   - Source code (Python, TypeScript)
   - Unit tests (≥90% coverage)
   - Integration tests
   - Security tests

2. **Documentation**
   - OpenAPI/Swagger spec (auto-generated)
   - README.md (updated)
   - CHANGELOG.md (detailed)
   - API documentation

3. **Artifacts**
   - Coverage report (HTML + XML)
   - SBOM (Software Bill of Materials)
   - Error ledger (JSON)
   - Security scan report

4. **Infrastructure**
   - Docker image (signed)
   - Docker Compose configs
   - Kubernetes manifests
   - Environment templates

5. **Metrics & Reports**
   - Performance metrics (P95, error rate)
   - Security metrics (CVE count, CVSS)
   - Code quality metrics (Ruff, MyPy scores)
   - Deployment summary

---

## Failure Policy

**Cardinal Rule**: Never skip. Always record.

- ❌ **DO NOT** merge PRs with failing CI
- ❌ **DO NOT** deploy with test failures
- ❌ **DO NOT** ignore security warnings
- ❌ **DO NOT** release without CHANGELOG

- ✅ **DO** log all errors to ledger
- ✅ **DO** continue processing (Rule #10)
- ✅ **DO** report issues transparently
- ✅ **DO** use: *"I cannot confirm this without testing."*

---

## Verification Checklist

| Audit | Tool | Target | Pass | Frequency |
|-------|------|--------|------|-----------|
| **Lint** | Ruff 0.8.0 | Python 3.11 | Clean | Every commit |
| **Format** | Black 24.10.0 | Line 119 | 100% | Every commit |
| **Types** | MyPy 1.14.0 | Strict | Clean | Every commit |
| **Security** | Bandit + Safety + pip-audit | All deps | No HIGH/CRITICAL | Every PR |
| **Tests** | Pytest 8.0+ | Coverage | ≥90% | Every commit |
| **Performance** | Load testing | Latency | P95 < 200ms | Weekly |
| **Dependencies** | pip-audit | requirements.txt | No vulnerabilities | Weekly |
| **Docker** | Trivy | Image | No HIGH/CRITICAL | Every build |
| **Secrets** | detect-secrets | All files | No secrets found | Every commit |
| **Truth Protocol** | Custom script | 15 rules | 15/15 pass | Every deploy |

---

## Code Quality Standards

### File Structure
```
agent/              # AI agents (40+ modules)
api/                # REST API endpoints (19+ routes)
security/           # Authentication & encryption (15+ modules)
ml/                 # Machine learning (9+ modules)
infrastructure/     # Database, cache, messaging (6+ modules)
monitoring/         # Logging, metrics, observability (5+ modules)
core/               # Error handling, utilities (4+ modules)
tests/              # Test suite (13+ files, ≥90% coverage)
.github/workflows/  # CI/CD pipelines (4 workflows)
```

### Code Style
- **Line length**: 119 characters (Black config)
- **Import order**: stdlib, third-party, local (isort)
- **Naming**: snake_case (variables), PascalCase (classes)
- **Docstrings**: Google-style with type hints
- **Type hints**: Required on all functions

### Error Handling
```python
# ✅ CORRECT
try:
    result = await risky_operation()
except SpecificError as e:
    record_error(
        error_type="OperationError",
        message=str(e),
        severity="MEDIUM",
        exception=e
    )
    return fallback_result

# ❌ WRONG
try:
    result = await risky_operation()
except:
    pass  # Violates Rule #10
```

---

## Enterprise Deployment

**See**: [ENTERPRISE_DEPLOYMENT.md](./ENTERPRISE_DEPLOYMENT.md)

Quick commands:
```bash
# Validate readiness
.claude/scripts/validate-deployment.sh

# Deploy to production
docker-compose -f docker-compose.production.yml up -d

# Monitor errors
curl https://your-domain/api/v1/monitoring/error-ledger
```

---

## Resources & Documentation

- **[ENTERPRISE_DEPLOYMENT.md](./ENTERPRISE_DEPLOYMENT.md)** - Production deployment guide
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Contributor guidelines (Truth Protocol)
- **[SECURITY.md](./SECURITY.md)** - Security baselines and hardening
- **[README.md](./README.md)** - Architecture and setup
- **[REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)** - Enterprise refactoring details
- **[CHANGELOG_ENTERPRISE_REFACTORING.md](./CHANGELOG_ENTERPRISE_REFACTORING.md)** - Full changelog

---

## Support & Escalation

| Issue | Contact | Urgency |
|-------|---------|---------|
| Security vulnerability | security@skyy-rose.com | P0 (Immediate) |
| Production incident | Engineering team | P0-P1 |
| Deployment help | See ENTERPRISE_DEPLOYMENT.md | P2 |
| Questions | GitHub issues/discussions | P3 |

---

**Claude enforces the Truth Protocol rigorously and ensures DevSkyy remains verifiable, secure, and enterprise-grade.** ✅

**Status**: Production-Ready | **Compliance**: 15/15 Rules | **Last Updated**: 2025-11-17
