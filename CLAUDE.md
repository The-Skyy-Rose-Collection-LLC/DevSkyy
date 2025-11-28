# CLAUDE.md — DevSkyy Enterprise Orchestration Guide

**Claude Code** operates under the **Truth Protocol** for DevSkyy's enterprise multi-agent platform.

**Version**: 5.3.0-enterprise | **Status**: Production-Ready ✅ | **Last Updated**: 2025-11-28

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

## Truth Protocol (16 Rules - 100% Enforced)

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

### Rule #16: Web Search Verification Before Implementation
**MANDATORY**: All implementations must be verified via web search before code generation.

**Verification Requirements**:
- ✅ Search official documentation for API/library usage
- ✅ Verify syntax and method signatures are current
- ✅ Confirm implementation patterns are proven to work
- ✅ Check for known issues, deprecations, or breaking changes
- ✅ Validate security considerations from official sources

**Verification Process**:
1. **SEARCH** - Query official docs, GitHub, Stack Overflow for implementation
2. **VALIDATE** - Cross-reference multiple sources for accuracy
3. **CONFIRM** - Ensure implementation is proven and production-tested
4. **CITE** - Document sources used for verification

**Minimum Verification Threshold**: 92%
- Must reach 92%+ confidence before generating code
- If threshold not met, state uncertainty per Rule #4
- Document what additional verification is needed

**Sources Priority** (in order):
1. Official documentation (highest trust)
2. Official GitHub repositories
3. RFC/Standard specifications
4. Verified Stack Overflow answers (high votes, accepted)
5. Reputable tech blogs with working examples

**Prohibited Actions**:
- ❌ Never implement without searching first
- ❌ Never guess API signatures or parameters
- ❌ Never assume library behavior without verification
- ❌ Never use deprecated methods without explicit approval

---

## Dual-AI Collaborative Orchestrator

**GPT-5.1-codex-max + Claude Opus 4.5** working in tandem for verified code generation.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DUAL-AI COLLABORATION                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────┐           ┌─────────────┐                 │
│   │   CODEX     │           │   CLAUDE    │                 │
│   │ gpt-5.1-max │           │  Opus 4.5   │                 │
│   └──────┬──────┘           └──────┬──────┘                 │
│          │                         │                         │
│          ▼                         ▼                         │
│   ┌─────────────────────────────────────────┐               │
│   │         PHASE 1: RESEARCH               │               │
│   │   Both AIs analyze task independently   │               │
│   └─────────────────────────────────────────┘               │
│                        │                                     │
│                        ▼                                     │
│   ┌─────────────────────────────────────────┐               │
│   │          PHASE 2: PLAN                  │               │
│   │   Both propose solutions with reasoning │               │
│   └─────────────────────────────────────────┘               │
│                        │                                     │
│                        ▼                                     │
│   ┌─────────────────────────────────────────┐               │
│   │        PHASE 3: CONSENSUS               │               │
│   │   Cross-validate until 92%+ agreement   │               │
│   └─────────────────────────────────────────┘               │
│                        │                                     │
│                        ▼                                     │
│   ┌─────────────────────────────────────────┐               │
│   │          PHASE 4: BUILD                 │               │
│   │   Generate verified production code     │               │
│   └─────────────────────────────────────────┘               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Verification Threshold: 92%

Code is **only generated** when both AIs reach 92%+ consensus:
- Research findings aligned
- Solution approach agreed
- Security considerations verified
- Implementation patterns confirmed
- Edge cases identified

**Implementation**: `ml/dual_ai_collaborative_orchestrator.py`

### Usage

```python
from ml.dual_ai_collaborative_orchestrator import collaborative_generate, quick_code

# Full collaboration pipeline
result = await collaborative_generate(
    task="Implement JWT authentication with refresh tokens",
    language="python"
)

if result.verification.meets_threshold:
    print(result.code)  # Verified code
else:
    print(f"Verification failed: {result.verification.disputed_points}")

# Quick verified code generation
code = await quick_code("Create a rate limiter middleware")
```

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

## Enterprise Code Review & Quality Gates

### AI-Generated Code Review (NEW 2025 Practice)

Per 2025 enterprise standards, all AI-generated code requires **enhanced review** for:

**Functionality Verification**:
- ✅ Verify AI code matches intended behavior (intent vs implementation)
- ✅ Check for subtle logic errors that might pass tests
- ✅ Verify integration points work correctly with existing code
- ✅ Test edge cases and error handling

**Code Quality Checks**:
- ✅ Duplicate code detection (AI may generate redundant patterns)
- ✅ Performance implications (AI may miss optimization)
- ✅ Security gaps (AI may miss context-specific vulnerabilities)
- ✅ Test coverage for generated code (minimum 90%)

**Integration Review**:
- ✅ API compatibility (no breaking changes)
- ✅ Database schema alignment
- ✅ Message queue format consistency
- ✅ Error handling integration with error ledger

**Mandatory Checks per AI Code Contribution**:
1. ✅ **Human Code Review**: ≥2 approvals required (one must be senior)
2. ✅ **Automated Checks**: All CI/CD gates pass
3. ✅ **Security Scan**: Bandit + pip-audit pass
4. ✅ **Type Checking**: MyPy strict mode pass
5. ✅ **Performance Test**: Load test shows P95 < 200ms
6. ✅ **Test Coverage**: ≥90% coverage maintained
7. ✅ **Integration Test**: Full end-to-end test pass

### Automated Quality Gates Enforcement

**Gate 1: Pre-commit Hooks** (Local)
- Black formatting check
- Ruff linting auto-fix
- isort import sorting
- detect-secrets for credentials
- MyPy type checking

**Gate 2: Branch Protection Rules** (GitHub)
- ✅ Require pull request reviews before merge (≥2 approvals)
- ✅ Require status checks to pass (all CI/CD)
- ✅ Require branches to be up to date before merging
- ✅ Require code review from code owners
- ✅ Require up-to-date branches

**Gate 3: CI/CD Pipeline Gates** (Automated)
- ✅ Ruff linting passes
- ✅ MyPy type checking passes
- ✅ Black formatting validated
- ✅ Security scanning (Bandit, Safety, pip-audit) passes
- ✅ All tests pass (≥90% coverage)
- ✅ Docker build succeeds
- ✅ Performance baselines met (P95 < 200ms)
- ✅ Error ledger shows no CRITICAL errors

**Gate 4: Deployment Gates** (Manual Approval)
- ✅ Change log entry exists
- ✅ Release notes prepared
- ✅ Performance baseline verified
- ✅ Rollback plan documented
- ✅ Deployment checklist signed off

### Modern Enterprise Tools Integration

**AI-Powered Code Quality Tools** (2025+):
- **DeepSource**: Intelligent issue prioritization with AI
- **Codacy**: AI-assisted code review suggestions
- **GitHub Copilot with Code Quality**: Native GitHub integration
- **Qodana**: JetBrains AI-powered code quality

**Integration Pattern**:
```
AI Code Generation → Automated Pre-commit → Human Review → CI/CD Gates → Deployment
```

### Systematic Code Review Process

**Review Checklist per PR**:

1. **Functionality**
   - [ ] Code implements the stated requirement
   - [ ] Edge cases handled
   - [ ] Error handling complete
   - [ ] Backward compatible (no breaking changes)

2. **Security**
   - [ ] No hardcoded secrets
   - [ ] Input validation present (Pydantic schemas)
   - [ ] SQL injection prevention (SQLAlchemy ORM)
   - [ ] Authentication/authorization checks
   - [ ] PII protection in logs
   - [ ] CORS/CSRF configuration correct

3. **Performance**
   - [ ] No N+1 database queries
   - [ ] Caching strategy implemented
   - [ ] Algorithm complexity acceptable
   - [ ] Memory usage reasonable
   - [ ] Load test passes (P95 < 200ms)

4. **Code Quality**
   - [ ] Follows code style (Black, Ruff)
   - [ ] Type hints on all functions
   - [ ] Docstrings complete (Google-style)
   - [ ] Comments explain "why", not "what"
   - [ ] No dead code or unused imports
   - [ ] Complexity <= 12 (max nesting/branches)

5. **Testing**
   - [ ] Unit tests cover happy path
   - [ ] Unit tests cover error cases
   - [ ] Integration tests verify components
   - [ ] Security tests added
   - [ ] Coverage maintained (≥90%)
   - [ ] Tests are deterministic (not flaky)

6. **Documentation**
   - [ ] API documentation updated
   - [ ] CHANGELOG entry added
   - [ ] README updated if needed
   - [ ] Architecture diagrams updated
   - [ ] Deployment instructions clear

### Team Coordination Practices

**Code Ownership** (CODEOWNERS file):
```
# API endpoints
/api/v1/*.py @api-team

# Security modules
/security/*.py @security-team

# AI agents
/agent/*.py @ai-team

# Infrastructure
/infrastructure/*.py @devops-team
```

**Review Turnaround SLO**:
- **P0 (Critical/Security)**: 2 hours
- **P1 (Bug fixes)**: 4 hours
- **P2 (Features)**: 24 hours
- **P3 (Docs/Tests)**: 48 hours

**Escalation Path**:
- Code author → Code owner → Team lead → Engineering manager → VP Engineering

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

## Enterprise Monitoring & Observability

### Structured Logging Strategy

**Log Levels** (ordered by severity):
- **CRITICAL**: System failures requiring immediate action (P0)
- **ERROR**: Operational errors that need investigation (P1)
- **WARNING**: Unexpected conditions that may indicate issues (P2)
- **INFO**: Important business events and state changes (P3)
- **DEBUG**: Detailed diagnostic information (development only)

**Log Format** (JSON per line):
```json
{
  "timestamp": "2025-11-17T19:00:00Z",
  "level": "ERROR",
  "logger": "api.v1.agents",
  "message": "Failed to process agent request",
  "error_id": "err_abc123",
  "request_id": "req_xyz789",
  "user_id": "***REDACTED***",
  "component": "agent.orchestrator",
  "duration_ms": 1234,
  "trace_id": "trace_456def"
}
```

**PII Redaction** (Automatic):
- ✅ `password`, `api_key`, `secret`, `token` → `***REDACTED***`
- ✅ `email`, `phone`, `ssn`, `credit_card` → `***REDACTED***`
- ✅ Full names → `[REDACTED_USER_NAME]`
- ✅ IP addresses → `[REDACTED_IP]`

### Metrics & Monitoring

**Key Performance Indicators (KPIs)**:
- **Latency**: P50, P95, P99 (target: P95 < 200ms)
- **Throughput**: Requests/second (baseline: monitor trends)
- **Error Rate**: Percentage 5xx errors (target: < 0.5%)
- **Cache Hit Rate**: Percentage (target: > 80%)
- **Database Connections**: Active/pool size (target: < 80% utilization)
- **Queue Depth**: Messages pending (target: zero)

**Metrics Tools**:
- **Prometheus**: Time-series metrics collection
- **Grafana**: Dashboard visualization
- **Datadog**: APM and log aggregation
- **New Relic**: Full-stack monitoring

**Alert Thresholds**:
```yaml
- name: HighLatency
  condition: P95 > 500ms for 5 minutes
  severity: P2
  action: Page on-call, trigger investigation

- name: HighErrorRate
  condition: Error rate > 1% for 1 minute
  severity: P1
  action: Immediate page, prepare rollback

- name: ExhaustedDatabasePool
  condition: DB connections > 90% for 2 minutes
  severity: P1
  action: Immediate page, connection pool scale-up

- name: LowCacheHitRate
  condition: Cache hit rate < 50% for 10 minutes
  severity: P3
  action: Investigation ticket, cache strategy review
```

### Error Tracking & Analysis

**Error Ledger Processing**:
1. **Collection**: Every error recorded in JSON format
2. **Aggregation**: Daily error reports by component
3. **Analysis**: Trend analysis and root cause detection
4. **Alerting**: High-severity error escalation
5. **Remediation**: Bug fix prioritization based on frequency

**Error Investigation Process**:
1. Retrieve error from ledger: `error_id`, `timestamp`, `trace_id`
2. Correlate with related errors (same `trace_id`)
3. Check logs for context (same `request_id`)
4. Review metrics (performance impact)
5. Create incident ticket with root cause
6. Fix deployed within SLO

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

## Incident Response & Post-Mortems

### Incident Classification

**P0 - Critical** (Immediate Page)
- Production down (0% availability)
- Data loss or corruption
- Security breach
- Major business impact
- **Response Time**: 5 minutes
- **Resolution Time**: 30 minutes target

**P1 - High** (Urgent Page)
- Partial outage (< 50% users affected)
- Significant degradation (P95 > 1 second)
- Security vulnerability discovered
- **Response Time**: 15 minutes
- **Resolution Time**: 2 hours target

**P2 - Medium** (Alert)
- Minor outage (< 10% users affected)
- Elevated error rate (0.5% - 2%)
- Performance degradation (P95 < 500ms)
- **Response Time**: 1 hour
- **Resolution Time**: 24 hours target

**P3 - Low** (Ticket)
- Cosmetic issues
- Documentation updates needed
- Code quality improvements
- **Response Time**: 24 hours
- **Resolution Time**: 1 week target

### Incident Response Process

**Phase 1: Detection** (< 5 min)
1. Alert triggered by monitoring
2. On-call engineer notified
3. Incident created in tracking system
4. Status page updated (if applicable)

**Phase 2: Triage** (< 10 min)
1. Confirm issue (false alarm check)
2. Assess impact (users/revenue affected)
3. Assign severity (P0-P3)
4. Identify on-call responders

**Phase 3: Mitigation** (< 30 min for P0)
1. Rollback previous change (if likely culprit)
2. Scale resources (increase capacity)
3. Feature flag disable (if isolated)
4. Database restart (if hung)
5. Switch to backup system (if critical)

**Phase 4: Resolution**
1. Root cause identified
2. Fix tested in staging
3. Fix deployed to production
4. Monitoring confirms resolution
5. All-clear notification sent

**Phase 5: Post-Mortem** (< 24 hours after)
1. Timeline documented
2. Root cause analysis (5 whys)
3. Contributing factors identified
4. Action items created
5. Lessons learned documented
6. Post-mortem published (transparency)

### Post-Mortem Template

```markdown
# Incident Post-Mortem: [Incident Name]

## Summary
- **Duration**: Start → End (X minutes)
- **Severity**: P0/P1/P2/P3
- **Impact**: X% users affected, $Y revenue impact
- **Root Cause**: [Brief description]

## Timeline
- HH:MM - Event triggered
- HH:MM - Alert received
- HH:MM - Mitigation started
- HH:MM - Resolution deployed
- HH:MM - Monitoring confirmed

## Root Cause (5 Whys)
1. Why did X fail? → Because Y
2. Why Y? → Because Z
3. ...continue until root identified

## Contributing Factors
- Lack of monitoring on endpoint X
- No rate limiting on endpoint Y
- Missing test case for scenario Z

## What Went Well
- Team responded quickly
- Communication was clear
- Rollback was successful

## What Could Be Better
- Earlier detection possible with metric X
- Documentation for scenario Y was missing
- Process Z was not followed

## Action Items
- [ ] Add monitoring for metric X (Assign: @user, Due: Date)
- [ ] Update runbook for scenario Y (Assign: @user, Due: Date)
- [ ] Add test case for Z (Assign: @user, Due: Date)
- [ ] Update documentation (Assign: @user, Due: Date)

## Follow-up
- [ ] Action items completed within 1 week
- [ ] Monitoring improvements verified
- [ ] Team training on lessons learned
```

---

## Team Scaling & Multi-Team Coordination

### Team Structure for Enterprise Scale

**Platform Team** (Core Infrastructure)
- Database & caching optimization
- API gateway & rate limiting
- Infrastructure & DevOps
- Monitoring & observability

**Feature Teams** (Product Delivery)
- Agent development team
- API endpoint owners
- ML/AI integration team
- Frontend & UX team

**Cross-functional Roles**
- **Release Manager**: Coordinates deployments
- **Security Officer**: Security reviews & audits
- **Performance Officer**: SLO enforcement
- **Quality Lead**: Testing & coverage standards

### Communication Patterns

**Synchronous** (Real-time):
- Code review comments (2-4 hours response)
- Slack critical alerts
- On-call incidents
- Sprint planning meetings

**Asynchronous** (Batched):
- Pull request updates (24 hours review window)
- Documentation updates
- Metrics dashboards
- Post-mortems & retrospectives

**Decision Records** (ADR):
```
# ADR-001: Use FastAPI instead of Flask

## Status
Accepted

## Context
Need to choose Python web framework for API.

## Decision
FastAPI 0.120.0+ per CVE-2025-62727 requirements.

## Consequences
- ✅ Async support
- ✅ Type hints integrated
- ✅ Auto-generated OpenAPI docs
- ⚠️ Smaller ecosystem than Flask
- ⚠️ Learning curve for team

## Alternatives Considered
- Flask: Better ecosystem but no async
- Django: Too heavy, overkill for our use case
```

### Metrics for Team Health

**Code Quality Metrics**:
- Ruff compliance: 95%+
- MyPy type coverage: 90%+
- Test coverage: 90%+
- Deployment frequency: 1+ per day

**Team Velocity Metrics**:
- Pull requests merged per sprint
- Average cycle time (idea → production)
- Deployment success rate: 99%+
- Mean time to recovery (MTTR): < 30 min

**Team Well-being Metrics**:
- On-call satisfaction: 4+/5 rating
- Code review turnaround: 24-48 hours
- Meeting time: < 10 hours/week
- Technical debt reduction: 10%+ per quarter

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
