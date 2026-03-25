---
name: deploy
description: Production deployment pipeline with validation and rollback.
---

# DevSkyy Deployment Pipeline

## Phases
```
Pre-Flight → Security → Build → Test → Deploy → Verify → Smoke
```

## Pre-Flight
- No uncommitted changes
- On main branch
- Dependencies installed

## Security Gates
```bash
pip-audit --desc           # Python CVEs
npm audit                  # Node.js vulnerabilities
bandit -r . -x venv        # OWASP scan
```
**ABORT on CRITICAL/HIGH vulnerabilities**

## Quality Gates
```bash
pytest --cov=. --cov-report=term    # Tests + coverage
mypy .                               # Type checking
```
**ABORT if tests fail or coverage <70%**

## Deploy Commands
```bash
vercel --prod                        # Frontend
docker-compose build && push         # Backend
```

## Post-Deploy Verification
- Health endpoint returns 200
- Database connectivity
- MCP server availability

## Related Tools
- **Agent**: `security-reviewer` before deploy
- **Command**: `/verify pre-pr` for full checks
- **MCP**: `health_check` for monitoring
