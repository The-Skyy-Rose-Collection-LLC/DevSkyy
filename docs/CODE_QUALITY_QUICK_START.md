# Code Quality Quick Start Guide

## For New Developers

Welcome to the DevSkyy Enterprise Platform! This guide will help you set up code quality tools quickly.

## Quick Setup (5 minutes)

### 1. Install Development Dependencies

```bash
# Install all development tools
pip install -r requirements-dev.txt

# Or install individually
pip install black isort flake8 ruff autoflake autopep8 pre-commit bandit mypy
```

### 2. Install Pre-commit Hooks

```bash
# Install pre-commit hooks (runs automatically before each commit)
pre-commit install

# Test the hooks
pre-commit run --all-files
```

That's it! Your development environment is now configured for code quality.

## Daily Workflow

### Before Making Changes

```bash
# Pull latest changes
git pull origin main

# Create a feature branch
git checkout -b feature/your-feature-name
```

### While Coding

Your IDE should automatically:
- Format code with Black
- Sort imports with isort
- Show linting errors from Ruff/Flake8

If not, configure your IDE (see IDE Setup below).

### Before Committing

Pre-commit hooks will automatically run when you commit. They will:
1. Check for secrets
2. Remove trailing whitespace
3. Format code with Black
4. Sort imports with isort
5. Lint with Ruff and Flake8
6. Remove unused imports with autoflake
7. Run security checks with Bandit
8. Type check with MyPy

If any check fails, fix the issues and commit again.

### Manual Code Quality Check

```bash
# Run all checks manually
pre-commit run --all-files

# Or run individual checks
ruff check .
black --check .
isort --check-only .
flake8 agent/ api/ ml/
```

### Auto-fix Issues

```bash
# Auto-fix most issues
ruff check . --fix
black .
isort .
autoflake --remove-all-unused-imports --in-place --recursive .
```

## IDE Setup

### VS Code

1. Install extensions:
   - Python (Microsoft)
   - Ruff
   - Black Formatter

2. Add to `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.linting.flake8Args": [
    "--config=.flake8"
  ]
}
```

### PyCharm

1. Configure Black:
   - Settings → Tools → Black
   - Enable "On code reformat"
   - Enable "On save"

2. Configure isort:
   - Settings → Tools → Python Integrated Tools
   - Set import sorting to "isort"

3. Configure Flake8:
   - Settings → Tools → External Tools
   - Add Flake8 with config path `.flake8`

## Common Commands

### Linting

```bash
# Check for issues
ruff check .                    # Modern linter
flake8 agent/ api/ ml/         # PEP8 compliance
mypy .                         # Type checking

# Auto-fix
ruff check . --fix             # Fix auto-fixable issues
```

### Formatting

```bash
# Check formatting
black --check .                # Code formatting
isort --check-only .          # Import sorting

# Auto-format
black .                        # Format all files
isort .                        # Sort all imports
```

### Cleanup

```bash
# Remove unused imports and variables
autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive .

# Fix PEP8 issues automatically
autopep8 --in-place --recursive .
```

### Security

```bash
# Security scan
bandit -r . -c .bandit.yml
```

## Common Issues & Fixes

### Issue: "Imports are not sorted"

**Fix:**
```bash
isort .
```

### Issue: "Code is not formatted with Black"

**Fix:**
```bash
black .
```

### Issue: "Unused import found"

**Fix:**
```bash
# Automatically remove
autoflake --remove-all-unused-imports --in-place file.py

# Or manually delete the import
```

### Issue: "Line too long"

**Fix:**
```python
# Split long lines
result = some_function(
    param1,
    param2,
    param3
)

# Or for strings
message = (
    "This is a very long message "
    "that spans multiple lines"
)
```

### Issue: "Missing whitespace around operator"

**Fix:**
```python
# Before
result=value*100

# After
result = value * 100
```

### Issue: "Expected 2 blank lines"

**Fix:**
```python
# Before
class MyClass:
    pass
def my_function():
    pass

# After
class MyClass:
    pass


def my_function():
    pass
```

### Issue: "Pre-commit hook failed"

**Steps:**
1. Read the error message
2. Fix the issues (often auto-fixable with `black .` or `ruff check . --fix`)
3. Stage the changes: `git add .`
4. Commit again: `git commit -m "Your message"`

## Code Review Checklist

Before requesting review:

- [ ] All tests pass: `pytest`
- [ ] All linters pass: `pre-commit run --all-files`
- [ ] Code is formatted: `black --check .`
- [ ] Imports are sorted: `isort --check-only .`
- [ ] No unused imports: `autoflake --check --recursive .`
- [ ] Docstrings added to new functions
- [ ] Type hints added to function signatures

## Documentation

For detailed information, see:

- **[CODE_QUALITY_STANDARDS.md](CODE_QUALITY_STANDARDS.md)** - Complete standards guide
- **[DOCSTRING_GUIDE.md](DOCSTRING_GUIDE.md)** - How to write docstrings
- **[CODE_REVIEW_CHECKLIST.md](CODE_REVIEW_CHECKLIST.md)** - Review guidelines

## Getting Help

### Documentation
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)

### Team Resources
- Ask in #dev-help Slack channel
- Review existing code for examples
- Check the code review checklist

## Summary

**Key Points:**
1. Install pre-commit hooks: `pre-commit install`
2. Hooks run automatically before commit
3. Auto-fix most issues: `black . && isort . && ruff check . --fix`
4. Check your code: `pre-commit run --all-files`
5. Follow PEP 8 standards

**Remember:**
- Pre-commit hooks prevent bad commits
- CI/CD validates all pull requests
- When in doubt, run the auto-formatters
- Code quality is everyone's responsibility

---

**Questions?** Check the documentation or ask the team!
