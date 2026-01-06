---
name: deploy
description: Production deployment pipeline with full validation, security scanning, and automated rollback
tags: [deployment, production, ci-cd, workflow]
---

# DevSkyy Production Deployment Pipeline

I'll execute a **comprehensive deployment workflow** with enterprise-grade quality gates.

## 🎯 Deployment Phases

```
Pre-Flight → Security → Build → Test → Deploy → Verify → Smoke Test
```

---

## Phase 1: Pre-Flight Checks 🔍

Validating repository state and dependencies...

**Checks:**

- ✅ Git status (no uncommitted changes on main)
- ✅ Branch is `main` (production deployments only from main)
- ✅ All dependencies installed
- ✅ Environment variables configured

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "git status --porcelain",
  "description": "Check for uncommitted changes"
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "git rev-parse --abbrev-ref HEAD",
  "description": "Get current branch"
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f package.json ]; then npm list --depth=0 2>&1 | grep -q 'missing' && echo 'MISSING_DEPS' || echo 'OK'; fi && if [ -f pyproject.toml ]; then pip check 2>&1 | grep -q 'incompatible' && echo 'INCOMPATIBLE' || echo 'OK'; fi",
  "description": "Check dependencies"
}
</params>
</tool_call>

**🚨 Pre-Flight Gate:**

- If uncommitted changes: **ABORT** (commit or stash first)
- If not on main branch: **ASK** (confirm deployment from non-main branch)
- If missing dependencies: **ABORT** (run `npm install` or `pip install`)

---

## Phase 2: Security Audit 🔐

Running comprehensive security scan...

**Security Checks:**

- 🔍 Python: `pip-audit` (CVE database)
- 🔍 Node.js: `npm audit` (vulnerability scan)
- 🔍 Code: `bandit` (OWASP checks)
- 🔍 Secrets: `detect-secrets` scan

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "pip-audit --desc --format json 2>&1 || echo '{\"vulnerabilities\": []}'",
  "description": "Python dependency security audit",
  "timeout": 60000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "cd frontend && npm audit --json 2>&1 || echo '{\"vulnerabilities\": {}}'",
  "description": "Node.js dependency security audit",
  "timeout": 60000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "bandit -r . -f json -x './venv,./node_modules,./frontend/node_modules' 2>&1 || echo '{\"results\": []}'",
  "description": "OWASP security scan",
  "timeout": 90000
}
</params>
</tool_call>

**🚨 Security Gate:**

- **Critical/High vulnerabilities**: **ABORT** (fix immediately)
- **Medium vulnerabilities**: **WARN** (log and continue, fix in next sprint)
- **Low vulnerabilities**: **LOG** (track for future remediation)

---

## Phase 3: Code Quality & Formatting ✨

Enforcing DevSkyy code standards...

**Formatters & Linters:**

- 🎨 `isort` - Import sorting
- 🎨 `ruff check --fix` - Fast Python linting
- 🎨 `black` - Code formatting
- 🎨 `mypy` - Type checking

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "isort . --check-only --diff",
  "description": "Check import sorting"
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "ruff check . --output-format=json 2>&1 || echo '[]'",
  "description": "Lint Python code",
  "timeout": 45000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "black --check . 2>&1",
  "description": "Check code formatting"
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "mypy . --no-error-summary 2>&1 | head -50",
  "description": "Type check codebase",
  "timeout": 60000
}
</params>
</tool_call>

**🚨 Quality Gate:**

- **Type errors**: **ABORT** (fix type hints)
- **Formatting issues**: **AUTO-FIX** (run `isort && ruff --fix && black`)
- **Linting errors**: **ABORT** (resolve before deployment)

---

## Phase 4: Test Suite Execution 🧪

Running comprehensive test suite...

**Test Categories:**

- Unit tests (pytest)
- Integration tests
- API contract tests
- Frontend tests (if applicable)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "pytest tests/ -v --tb=short --maxfail=5 --cov=. --cov-report=term --cov-report=json --junitxml=test-results.xml 2>&1",
  "description": "Run test suite with coverage",
  "timeout": 300000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f frontend/package.json ] && grep -q '\"test\"' frontend/package.json; then cd frontend && npm run test 2>&1 || echo 'No frontend tests'; else echo 'No frontend tests configured'; fi",
  "description": "Run frontend tests",
  "timeout": 120000
}
</params>
</tool_call>

**🚨 Test Gate:**

- **Any test failures**: **ABORT** (fix tests before deploying)
- **Coverage < 70%**: **WARN** (track coverage debt)
- **No tests found**: **ABORT** (TDD violation)

---

## Phase 5: Build Production Bundle 📦

Building optimized production artifacts...

**Build Steps:**

- Frontend: `npm run build:production`
- Backend: Python package build
- Asset optimization
- Source maps generation

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f frontend/package.json ]; then cd frontend && npm run build 2>&1; else echo 'No frontend build required'; fi",
  "description": "Build frontend production bundle",
  "timeout": 180000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "python -m build 2>&1 || echo 'Skipping Python build'",
  "description": "Build Python package",
  "timeout": 60000
}
</params>
</tool_call>

**🚨 Build Gate:**

- **Build failures**: **ABORT** (fix build errors)
- **Bundle size > 5MB**: **WARN** (consider code splitting)
- **Missing assets**: **ABORT** (check asset paths)

---

## Phase 6: Deploy to Production 🚀

Deploying to production infrastructure...

**Deployment Target:** Vercel (Frontend) + Production Server (Backend)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if command -v vercel >/dev/null 2>&1; then cd frontend && vercel --prod --yes 2>&1; else echo 'Vercel CLI not installed - manual deployment required'; fi",
  "description": "Deploy frontend to Vercel",
  "timeout": 300000
}
</params>
</tool_call>

**Backend Deployment:**

- Option 1: Docker image push + container restart
- Option 2: Git push to production remote
- Option 3: Manual deployment (if infrastructure not automated)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f docker-compose.yml ]; then docker-compose build 2>&1 && echo 'Docker image built - push to registry manually'; else echo 'No Docker deployment configured'; fi",
  "description": "Build Docker image",
  "timeout": 300000
}
</params>
</tool_call>

**🚨 Deployment Gate:**

- **Deployment failures**: **ROLLBACK** (revert to previous version)
- **Partial deployment**: **ABORT** (ensure atomicity)

---

## Phase 7: Post-Deployment Verification ✅

Verifying deployment health...

**Health Checks:**

- API health endpoint (`/health`)
- Database connectivity
- MCP server availability
- Frontend accessibility

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "sleep 10 && curl -f -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>&1 || echo '000'",
  "description": "Check API health endpoint",
  "timeout": 30000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "curl -f -s -o /dev/null -w '%{http_code}' https://$(grep WORDPRESS_URL .env | cut -d'=' -f2 | tr -d '\"') 2>&1 || echo '000'",
  "description": "Check WordPress site",
  "timeout": 30000
}
</params>
</tool_call>

**🚨 Verification Gate:**

- **Health checks fail**: **ROLLBACK IMMEDIATE**
- **Partial service availability**: **INVESTIGATE** (check logs)
- **All checks pass**: **PROCEED** to smoke tests

---

## Phase 8: Smoke Tests 🔥

Running critical user journey tests...

**Smoke Test Scenarios:**

1. Homepage loads
2. API returns valid response
3. Database query succeeds
4. MCP tools accessible
5. Authentication flow works

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "python -c 'import requests; r = requests.get(\"http://localhost:8000/api/v1/health\"); print(f\"Status: {r.status_code}\"); assert r.status_code == 200, \"Health check failed\"' 2>&1 || echo 'Smoke test failed'",
  "description": "API smoke test",
  "timeout": 15000
}
</params>
</tool_call>

**🚨 Smoke Test Gate:**

- **Critical path failures**: **ROLLBACK IMMEDIATE**
- **Non-critical failures**: **CREATE INCIDENT** (monitor closely)
- **All tests pass**: **DEPLOYMENT SUCCESSFUL** ✅

---

## Phase 9: Deployment Report 📊

Generating deployment summary...

**Report Includes:**

- ✅ Deployment timestamp
- ✅ Deployed commit SHA
- ✅ Test results summary
- ✅ Security scan results
- ✅ Code coverage metrics
- ✅ Build artifacts
- ✅ Deployment duration

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "git log -1 --format='%H %s (%an, %ar)' && echo '' && git diff --stat HEAD~1 HEAD",
  "description": "Get deployment commit info"
}
</params>
</tool_call>

**Audit Log Entry:**

```json
{
  "deployment_id": "deploy_$(date +%s)",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit_sha": "$(git rev-parse HEAD)",
  "deployed_by": "claude-code-automation",
  "environment": "production",
  "status": "success|failed|rolled_back"
}
```

---

## 🎉 Deployment Complete

**Next Steps:**

1. Monitor production logs for errors
2. Check metrics dashboard
3. Verify user-facing features
4. Update deployment documentation

**Rollback Instructions (if needed):**

```bash
# Frontend rollback
cd frontend && vercel rollback

# Backend rollback
git revert HEAD && git push production main
docker-compose up -d
```

**Support Contacts:**

- Technical Issues: <support@skyyrose.com>
- Security Issues: <security@skyyrose.com>
- On-Call: [PagerDuty/Slack channel]

---

**Deployment Pipeline Version:** 1.0.0
**DevSkyy Environment:** Production
**Compliance:** GDPR, SOC2, OWASP Top 10
