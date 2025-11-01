# CLAUDE.md — DevSkyy Orchestration Guide

**Claude Code** operates under the **Truth Protocol** for DevSkyy's multi-agent platform.

## Stack
- Python 3.11.9 (FastAPI 0.104) | Node 18/TS5 | PostgreSQL 15 | Docker | GitHub Actions

## Truth Protocol

1. **Never guess** – Verify all syntax, APIs, security from official docs
2. **Pin versions** – Explicit version numbers for all dependencies
3. **Cite standards** – RFC 7519 (JWT), NIST SP 800-38D (AES-GCM)
4. **State uncertainty** – Use: `I cannot confirm without testing.`
5. **No secrets in code** – Environment variables or secret manager only
6. **RBAC roles** – SuperAdmin, Admin, Developer, APIUser, ReadOnly
7. **Input validation** – Schema enforcement, sanitization, CSP
8. **Test coverage ≥90%** – Unit, integration, security tests
9. **Document all** – Auto-generate OpenAPI, maintain Markdown
10. **No-skip rule** – Log errors to `/artifacts/error-ledger-<run_id>.json`, continue processing
11. **Verified languages** – Python 3.11.*, TypeScript 5.*, SQL, Bash only
12. **Performance SLOs** – P95 < 200ms, error rate < 0.5%, zero secrets in repo
13. **Security baseline** – AES-256-GCM, Argon2id, OAuth2+JWT, PBKDF2
14. **Error ledger required** – Every run and CI cycle
15. **No placeholders** – Every line executes or verifies

## Pipeline
```
Ingress → Validation → Auth → RBAC → Logic → Encryption → Output → Observability
```

## Orchestration
**PLAN** → **BUILD** → **TEST** → **REVIEW** → **DEPLOY** → **MONITOR** → **HEAL** → **LEARN** → **REPORT**

## CI/CD
- **Platform:** GitHub Actions
- **Jobs:** lint → type → test → security → image scan
- **Release gate:** ≥90% coverage, no HIGH/CRITICAL CVEs, error ledger, OpenAPI valid, Docker signed, P95 < 200ms

## Deliverables
Code + Docs + Tests | OpenAPI + Coverage + SBOM | Metrics | Docker image + signature | Error ledger | CHANGELOG.md

## Failure Policy
Never skip. Always record. Use: `I cannot confirm this without testing.`

## Verification
| Audit | Tool | Target | Pass |
|-------|------|--------|------|
| Lint/Type | Ruff + Mypy | Python 3.11 | Clean |
| Security | Bandit + Safety + Trivy | All deps | No HIGH/CRITICAL |
| Tests | Pytest | Coverage | ≥90% |
| Performance | Autocannon | Latency | P95 < 200ms |

Claude enforces the **Truth Protocol** and ensures DevSkyy remains verifiable, secure, and enterprise-grade.
