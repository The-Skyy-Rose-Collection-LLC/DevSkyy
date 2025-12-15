# Developer Quick Reference - Clean Coding Compliance

**For:** DevSkyy Contributors  
**Purpose:** Fast reference for code quality tools and compliance agents

---

## Initial Setup (One-Time)

```bash
# Clone repository
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy

# Run setup script (handles everything automatically)
./setup_compliance.sh

# Or manually:
pip install -e ".[dev]"
pre-commit install
detect-secrets scan > .secrets.baseline
```

---

## Daily Workflow

### 1. Before You Code

```bash
# Update to latest
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. While Coding

```bash
# Run linter (auto-fixes many issues)
ruff check . --fix

# Format code
black .
isort .

# Type check
mypy .
```

### 3. Before Committing

```bash
# Pre-commit hooks run automatically, but you can test manually:
pre-commit run --all-files

# Or just on staged files:
pre-commit run
```

### 4. Committing Changes

```bash
# Stage your changes
git add .

# Commit (pre-commit hooks run automatically)
git commit -m "feat: add new feature"

# If pre-commit fails:
# - Fix the issues shown
# - Stage the fixes: git add .
# - Commit again: git commit -m "feat: add new feature"
```

### 5. Pushing to GitHub

```bash
# Push to remote
git push origin feature/your-feature-name

# GitHub Actions will automatically:
# ✓ Check code quality (Black, Ruff, MyPy)
# ✓ Run tests with coverage
# ✓ Scan for security issues
# ✓ Review dependencies
```

---

## Common Commands

### Code Formatting

```bash
# Format Python code (100 char lines)
black .

# Sort imports
isort .

# Both together
black . && isort .
```

### Linting

```bash
# Check code quality
ruff check .

# Auto-fix issues
ruff check . --fix

# Show specific rule violations
ruff check . --output-format=github
```

### Type Checking

```bash
# Check types
mypy .

# Check types with error codes
mypy . --show-error-codes

# Check specific file
mypy path/to/file.py
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_specific_function -v

# Run only fast tests
pytest tests/ -m "not slow"
```

### Security Scanning

```bash
# Scan dependencies
pip-audit

# Security linting
bandit -r .

# Check for secrets
detect-secrets scan
```

### Pre-Commit

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Update hooks to latest versions
pre-commit autoupdate

# Skip hooks (use rarely!)
git commit --no-verify

# Reinstall hooks
pre-commit uninstall
pre-commit install
```

---

## What Gets Checked Automatically

### On `git commit` (Pre-Commit Hooks)

✅ **Code Formatting**
- Black (Python formatter)
- isort (Import sorter)

✅ **Code Quality**
- Ruff (Fast linter)
- MyPy (Type checker)

✅ **Security**
- Bandit (Security scanner)
- detect-secrets (Secret detection)

✅ **File Quality**
- Trailing whitespace
- End-of-file newlines
- YAML/JSON/TOML validation
- Large file detection (>1MB)
- Merge conflicts

✅ **Documentation**
- Pydocstyle (Docstring checker)
- Markdownlint (Markdown formatter)

### On `git push` (GitHub Actions)

✅ **Testing**
- Full pytest suite
- Code coverage (must be >80%)
- Coverage reports

✅ **Security**
- pip-audit (dependency vulnerabilities)
- Safety check
- Bandit security linter

✅ **Code Quality** (Python 3.11 & 3.12)
- Black formatting check
- isort check
- Ruff linting
- MyPy type checking

✅ **Dependencies**
- Dependency review (on PRs)
- Breaking change detection

---

## Fixing Common Issues

### "Black would reformat X files"

```bash
# Just run Black to fix:
black .

# Then commit:
git add .
git commit -m "your message"
```

### "isort would reformat X files"

```bash
# Run isort to fix:
isort .

# Then commit:
git add .
git commit -m "your message"
```

### "Ruff found X violations"

```bash
# Auto-fix what can be fixed:
ruff check . --fix

# Review remaining issues and fix manually
# Then commit
```

### "MyPy found type errors"

```bash
# Add type hints to fix:
def my_function(param: str) -> int:
    return len(param)

# Or add ignore comment for special cases:
result = some_untyped_library()  # type: ignore
```

### "Bandit found security issue"

```bash
# Fix the security issue (e.g., don't use hardcoded passwords)
# Or if it's a false positive, add:
password = get_from_env()  # nosec B105

# Then commit
```

### "detect-secrets found potential secret"

```bash
# If it's NOT a real secret, update baseline:
detect-secrets scan > .secrets.baseline

# If it IS a real secret, remove it and use environment variables
```

### "Large file detected"

```bash
# Remove large files (>1MB) from repository
# Use Git LFS for large files if needed
git rm --cached large_file.bin
```

---

## Configuration Files Reference

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| `pyproject.toml` | Python project config (Black, Ruff, MyPy, pytest) |
| `.github/workflows/quality-check.yml` | GitHub Actions CI/CD |
| `.github/dependabot.yml` | Automated dependency updates |
| `.markdownlint.json` | Markdown linting rules |
| `.secrets.baseline` | Allowed secrets baseline |
| `.gitignore` | Files to ignore in Git |

---

## Compliance Levels

### 🟢 Level 1: Minimum Compliance (Required)

- [ ] Pre-commit hooks installed
- [ ] All pre-commit checks pass
- [ ] Tests pass locally
- [ ] No security vulnerabilities

### 🟡 Level 2: Good Compliance (Recommended)

- [ ] Code coverage >80%
- [ ] All type hints added
- [ ] Docstrings on public functions
- [ ] No MyPy errors

### 🔵 Level 3: Excellent Compliance (Optional)

- [ ] Code coverage >90%
- [ ] All functions documented
- [ ] Performance benchmarks pass
- [ ] Zero warnings from all tools

---

## Troubleshooting

### Pre-commit is too slow

```bash
# Run only on changed files
pre-commit run

# Skip specific hooks temporarily
SKIP=mypy pre-commit run

# Update hooks (may improve performance)
pre-commit autoupdate
```

### GitHub Actions failing

```bash
# Run the same checks locally:
black --check .
isort --check-only .
ruff check .
mypy .
pytest tests/

# Fix issues and push again
```

### Can't commit (emergency only)

```bash
# Skip pre-commit hooks (use with caution!)
git commit --no-verify -m "emergency fix"

# But fix the issues ASAP after
```

---

## Getting Help

### Documentation

- **Full Guide:** `CLEAN_CODING_AGENTS.md`
- **File Inventory:** `REPOSITORY_FILES.md`
- **Project README:** `README.md`

### Commands

```bash
# Pre-commit help
pre-commit --help

# Black help
black --help

# Ruff help
ruff check --help

# MyPy help
mypy --help

# Pytest help
pytest --help
```

### Resources

- Pre-commit: https://pre-commit.com/
- Black: https://black.readthedocs.io/
- Ruff: https://beta.ruff.rs/docs/
- MyPy: https://mypy.readthedocs.io/
- Pytest: https://docs.pytest.org/

---

**Last Updated:** December 14, 2025  
**Maintained By:** DevSkyy Team
