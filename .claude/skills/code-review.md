---
name: code-review
description: Comprehensive code analysis - security, quality, complexity, coverage
---

# DevSkyy Code Review

## Quick Commands
```bash
pip-audit --desc               # Python vulnerabilities
npm audit                      # Node.js vulnerabilities
bandit -r . -x venv            # OWASP security scan
mypy .                         # Type checking
pytest --cov=.                 # Test coverage
```

## Severity Levels
- **CRITICAL**: Hardcoded secrets, injection, missing auth
- **HIGH**: Coverage <50%, type errors >100
- **MEDIUM**: Coverage 50-70%, complexity >15
- **LOW**: Missing docstrings, TODO markers

## Checklist
- [ ] No CRITICAL/HIGH security issues
- [ ] Type errors <50
- [ ] Coverage >70%
- [ ] No hardcoded secrets

## Related Tools
- **Agent**: Use `code-reviewer` agent for full review
- **Agent**: Use `security-reviewer` for auth/API code
- **Command**: `/verify` for pre-commit checks
- **Skill**: `security-review` for OWASP patterns

Run `pytest -v` after every code change.
