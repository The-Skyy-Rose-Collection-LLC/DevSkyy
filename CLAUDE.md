  # CLAUDE.md — DevSkyy 20/10 Master Orchestration Guide

This document governs **Claude Code** when contributing to the DevSkyy repository.  
It defines how Claude collaborates with all other agents (Cursor, ChatGPT, Gemini, HuggingFace) under the **Truth Protocol** to achieve a **fully automated, headless, self-healing, self-learning system**.

---

## Core Identity

DevSkyy is an **AI-driven, multi-agent platform** written in:
- **Python 3.11.9** (FastAPI 0.104 backend)
- **Node 18 / TypeScript 5 frontend**
- **PostgreSQL 15** database
- **Docker + GitHub Actions** for CI/CD  
- **Hugging Face**, **Claude**, **ChatGPT**, and **Gemini** for adaptive automation

Target: **Enterprise A+ readiness** (performance, security, compliance, automation).

---

## Truth Protocol (Immutable Rules)

1. **Never guess.** All syntax, APIs, and security flows must be verified from official documentation.  
2. **Pin versions.** Each dependency includes its explicit version number.  
3. **Cite standards.** RFC 7519 (JWT), NIST SP 800-38D (AES-GCM), Microsoft REST Guidelines (API Versioning).  
4. **State uncertainty.** Use only: `I cannot confirm without testing.`  
5. **No hard-coded secrets.** Load from environment or secret manager.  
6. **RBAC enforcement.** Roles: SuperAdmin, Admin, Developer, APIUser, ReadOnly.  
7. **Input validation.** Enforce schema, sanitize, block traversal, enforce CSP.  
8. **Test coverage ≥ 90 %.** Unit, integration, and security tests.  
9. **Document everything.** Auto-generate OpenAPI and Markdown docs.  
10. **No-skip rule.** Never skip a file, artifact, or process due to error.  
    - Continue processing. Log all exceptions to `/artifacts/error-ledger-<run_id>.json`.  
11. **Languages.** Only verified: Python 3.11.*, TypeScript 5.*, SQL, Bash.  
12. **Performance SLOs.**  
    - P95 < 200 ms per endpoint.  
    - Error rate < 0.5 %.  
    - Zero secrets in repo.  
13. **Security Baseline.**  
    - AES-256-GCM (encryption)  
    - Argon2id (password hashing)  
    - OAuth2 + JWT auth (RFC 7519)  
    - PBKDF2 for key derivation  
14. **Error ledger required** for every run and CI cycle.  
15. **No fluff.** Every line must execute or verify. No placeholders or speculative code.

---

## Endpoint Pipeline (FastAPI Core)

```
Ingress (HSTS, CORS, Rate-limit)
→ Validation (Pydantic strict)
→ Auth (OAuth2/JWT)
→ RBAC/ABAC
→ Business Logic (Idempotency, Transactions)
→ Data Protection (AES-GCM, Argon2id)
→ Output (Schemas, Pagination)
→ Observability (Logs, Metrics, Traces)
→ Error Mapping (problem+json)
```

Middleware: `/backend/app/middleware/pipeline.py`  
Metrics: `/api/v1/monitoring/metrics`  
Health: `/api/v1/healthz`, `/api/v1/monitoring/readyz`

---

## Agent System

| Agent | Composition | Primary Function | Output |
|-------|--------------|------------------|--------|
| **Professors of Code** | Claude + Cursor | Backend audits, refactors, security enforcement | Code PRs + tests + OpenAPI |
| **Growth Stack** | Claude + ChatGPT | Build WordPress themes, landing pages, A/B testing, CX automation | Deployable themes, analytics mapping |
| **Data & Reasoning** | Claude + Gemini | Retrieval, eval harnesses, prompt routing, KPI analysis | Eval reports + routing policies |
| **Visual Foundry** | HuggingFace + Claude + Gemini + ChatGPT | Image upscaling, brand-true asset generation, video automation | High-fidelity visuals + metadata |

---

## Orchestration Loop

1. **PLAN** – Break project into atomic jobs with owners, inputs, outputs, and acceptance tests.  
2. **BUILD** – Implement code/assets. Validate syntax, versions, and security.  
3. **TEST** – Run full suite (`pytest --cov`, `mypy --strict`, `bandit`, `safety`).  
4. **REVIEW** – Static analysis, red-team prompts, dependency scan.  
5. **DEPLOY** – Docker image build, push, and canary rollout.  
6. **MONITOR** – Collect Prometheus metrics, detect regressions.  
7. **HEAL** – Auto-rollback or patch; PR generated with failing test included.  
8. **LEARN** – Integrate feedback and metrics into future iterations.  
9. **REPORT** – Publish `CHANGELOG.md`, coverage, SBOM, and error ledger.

---

## CI/CD Baseline

- **Platform:** GitHub Actions (`.github/workflows/ci.yml`)  
- **Jobs:** lint → type → test → security scan → Trivy image scan  
- **Artifacts:** all reports uploaded even on failure  
- **Release criteria:**  
  - Tests pass ≥ 90 % coverage  
  - No critical/high CVEs  
  - Error ledger complete  
  - OpenAPI schema valid  
  - Docker image signed and scanned  

---

## Observability & GDPR

**Endpoints:**  
- `/api/v1/gdpr/export` – Export user data (`gdpr.export` scope)  
- `/api/v1/gdpr/delete` – Delete user data (`gdpr.delete` scope)  
- `/api/v1/monitoring/metrics`, `/api/v1/healthz`, `/api/v1/monitoring/readyz`

**Logging:** Structured JSON logs with request_id  
**Metrics:** Prometheus; **Tracing:** OTEL-ready  
**Ledger:** `/artifacts/error-ledger-<run_id>.json` for every build

---

## Deliverables per Cycle

- Code + Docs + Tests  
- OpenAPI + Coverage + SBOM  
- Prometheus metrics snapshot  
- Docker image + signature  
- Error ledger JSON  
- `CHANGELOG.md`

---

## Failure Policy

- Never skip. Always record failures.  
- Never guess or repair heuristically without tests.  
- Use: `I cannot confirm this without testing.`

---

## Security & Verification

| Audit | Tool | Target | Pass |
|-------|------|---------|------|
| Lint/Type | Ruff + Mypy | Python 3.11 | Clean |
| Security | Bandit + Safety + Trivy | All deps | No HIGH/CRITICAL |
| Tests | Pytest | Coverage | ≥ 90 % |
| Performance | Autocannon | Latency | P95 < 200 ms |

---

## AI Agent Interaction Rules

- No cross-agent overwrites without orchestration approval.  
- Claude validates all outputs before merge.  
- Agents return deterministic, testable artifacts.  
- Every commit must be reproducible and measurable.

---

## Command Surface

| Command | Purpose |
|----------|----------|
| `PLAN(scope)` | Create job graph and tests |
| `BUILD(job_id)` | Execute implementation |
| `TEST(job_id)` | Validate output/security |
| `DEPLOY(env)` | Push release and monitor |
| `HEAL(incident)` | Rollback and patch |
| `LEARN(run)` | Update heuristics |
| `REPORT(run)` | Summarize KPIs/errors |

---

## Release Gate Checklist

✅ Tests ≥ 90 % coverage  
✅ No HIGH/CRITICAL CVEs  
✅ Zero hard-coded secrets  
✅ Error ledger exists  
✅ OpenAPI valid  
✅ Docker signed  
✅ Latency P95 < 200 ms

---

Claude enforces the **Truth Protocol**, coordinates all agents, and ensures DevSkyy’s codebase remains verifiable, secure, and enterprise-grade.
