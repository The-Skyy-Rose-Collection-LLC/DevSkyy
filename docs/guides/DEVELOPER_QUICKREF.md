# DevSkyy Developer Quick Reference

Essential commands and workflows for daily development with the Clean Coding Compliance System.

## 🚀 Quick Setup (One-time)

```bash
# Automated setup
./setup_compliance.sh

# Manual setup
pip install pre-commit
pre-commit install
```

## 📝 Daily Workflow

### Standard Development

```bash
# Normal workflow - hooks run automatically
git add .
git commit -m "feat: add new feature"  # ← Pre-commit runs here (2-5s)
git push                               # ← CI/CD runs here (5-10min)
```

### Before Committing (Optional)

```bash
# Run all checks manually
pre-commit run --all-files

# Quick format + lint
black . && isort . && ruff check . --fix
```

## 🔧 Essential Commands

### Code Quality

```bash
# Format code (auto-fix)
black .

# Sort imports (auto-fix)
isort .

# Lint and fix issues
ruff check . --fix

# Type checking
mypy .

# Security scan
bandit -r .

# All pre-commit hooks
pre-commit run --all-files
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov

# Specific test file
pytest tests/test_server.py

# With verbose output
pytest -v
```

### Documentation

```bash
# Check markdown
markdownlint-cli2 "**/*.md"

# Validate links
find . -name "*.md" -exec grep -l "http" {} \;
```

## 🛠️ Troubleshooting

### Pre-commit Issues

```bash
# Update hooks to latest versions
pre-commit autoupdate

# Clear cache and reinstall
pre-commit clean
pre-commit uninstall
pre-commit install

# Skip hooks temporarily (NOT recommended)
git commit --no-verify -m "emergency fix"
```

### Common Fixes

```bash
# Fix import order conflicts
isort . && black .

# Fix line length issues
black . --line-length 88

# Fix type issues
mypy . --ignore-missing-imports

# Update dependencies
pip install -r requirements.txt --upgrade
```

## 📊 Status Checks

### Local Status

```bash
# Check what will be committed
git status

# See what pre-commit will check
pre-commit run --all-files --dry-run

# Check test coverage
pytest --cov --cov-report=term-missing
```

### Remote Status

```bash
# Check CI status
gh pr status  # GitHub CLI

# View workflow runs
gh run list

# Check security alerts
gh api repos/:owner/:repo/security-advisories
```

## 🔍 Code Quality Metrics

### Coverage Requirements

- **Minimum**: 80% test coverage
- **Target**: 90%+ for new code
- **Exclusions**: `__init__.py`, test files

### Performance Targets

- **Pre-commit**: < 5 seconds
- **CI/CD**: < 10 minutes
- **Security scan**: < 2 minutes

### Quality Gates

- ✅ All pre-commit hooks pass
- ✅ Tests pass with >80% coverage
- ✅ No security vulnerabilities
- ✅ No type errors
- ✅ Documentation updated

## 🚨 Emergency Procedures

### Bypass Hooks (Use Sparingly)

```bash
# Skip pre-commit (NOT recommended)
git commit --no-verify -m "hotfix: critical issue"

# Skip specific hook
SKIP=mypy git commit -m "fix: temporary type issue"
```

### Fix Broken CI

```bash
# Check CI logs
gh run view --log

# Re-run failed jobs
gh run rerun

# Force push after fixes
git push --force-with-lease
```

### Rollback Changes

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert specific commit
git revert <commit-hash>
```

## 📋 Commit Message Format

### Conventional Commits

```bash
# Feature
git commit -m "feat: add user authentication"

# Bug fix
git commit -m "fix: resolve login timeout issue"

# Documentation
git commit -m "docs: update API documentation"

# Refactor
git commit -m "refactor: optimize database queries"

# Test
git commit -m "test: add unit tests for auth module"

# Chore
git commit -m "chore: update dependencies"
```

### Breaking Changes

```bash
git commit -m "feat!: change API response format

BREAKING CHANGE: API now returns data in different structure"
```

## 🔐 Security Checklist

### Before Committing

- [ ] No hardcoded secrets or API keys
- [ ] No sensitive data in logs
- [ ] Input validation implemented
- [ ] SQL injection prevention
- [ ] XSS protection in place

### Environment Variables

```bash
# Check for secrets
detect-secrets scan --all-files

# Update baseline
detect-secrets scan --baseline .secrets.baseline
```

## 📈 Performance Tips

### Speed Up Pre-commit

```bash
# Use specific hooks only
pre-commit run black isort ruff

# Skip slow hooks during development
SKIP=mypy,bandit git commit -m "wip: work in progress"
```

### Parallel Testing

```bash
# Run tests in parallel
pytest -n auto

# Run specific test categories
pytest -m "not slow"
```

## 🔄 Update Procedures

### Weekly Updates

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Update Python dependencies
pip install -r requirements.txt --upgrade

# Update Node.js dependencies
npm update
```

### Monthly Reviews

- Review security scan results
- Update tool configurations
- Check for new linting rules
- Evaluate performance metrics

## 📞 Getting Help

### Documentation

- `CLEAN_CODING_AGENTS.md` - Full system documentation
- `SERVER_README.md` - MCP server documentation
- `QUICKSTART.md` - 5-minute setup guide

### Commands

```bash
# Tool help
black --help
ruff --help
mypy --help
pytest --help

# Pre-commit help
pre-commit --help
pre-commit run --help
```

### Common Issues

1. **Hook failures**: Check `.pre-commit-config.yaml`
2. **Type errors**: Add type annotations or ignores
3. **Import errors**: Check `PYTHONPATH` and dependencies
4. **Test failures**: Run `pytest -v` for details

---

**Remember**: The system is designed to help, not hinder. When in doubt, run the checks manually first!
