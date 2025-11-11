# DevSkyy Code Quality Standards

## Overview

This document outlines the code quality standards and automated enforcement mechanisms for the DevSkyy Enterprise Platform.

## Code Style Standards

### PEP 8 Compliance

All Python code must comply with [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines:

- **Line Length**: Maximum 119 characters (aligned with transformers standard)
- **Indentation**: 4 spaces (no tabs)
- **Blank Lines**: 
  - 2 blank lines between top-level definitions
  - 1 blank line between method definitions
- **Operator Spacing**: Always use whitespace around operators
  - ✅ Correct: `x = a + b`, `result = value * 100`
  - ❌ Incorrect: `x=a+b`, `result=value*100`
- **Import Organization**:
  - Standard library imports first
  - Third-party imports second
  - Local application imports last
  - Alphabetically sorted within each group

### Import Management

- **No Unused Imports**: All imports must be used in the file
- **No Star Imports**: Avoid `from module import *`
- **Explicit Imports**: Use explicit imports for clarity
  ```python
  # ✅ Good
  from typing import List, Dict, Optional
  
  # ❌ Bad
  from typing import *
  ```

### Exception Handling

- **No Bare Except Clauses**: Always specify exception types
  ```python
  # ✅ Good
  try:
      risky_operation()
  except ValueError as e:
      logger.error(f"Value error: {e}")
  except Exception as e:
      logger.error(f"Unexpected error: {e}")
  
  # ❌ Bad
  try:
      risky_operation()
  except:
      logger.error("Error occurred")
  ```

### Code Complexity

- **Maximum Cyclomatic Complexity**: 12
- **Maximum Function Length**: 50 lines (guideline)
- **Maximum Arguments**: 7 parameters per function
- **Maximum Local Variables**: 15 per function

## Automated Tools

### Linters

#### 1. Ruff (Primary Linter)
- Modern, fast Python linter
- Replaces multiple tools (Flake8, isort, pyupgrade, etc.)
- Configuration in `pyproject.toml`

```bash
# Run Ruff
ruff check .

# Auto-fix issues
ruff check . --fix
```

#### 2. Flake8 (PEP8 Compliance)
- Checks for PEP 8 compliance
- Configuration in `.flake8`

```bash
# Run Flake8
flake8 agent/ api/ ml/

# With statistics
flake8 --statistics --count .
```

#### 3. Black (Code Formatter)
- Opinionated code formatter
- Ensures consistent code style

```bash
# Check formatting
black --check .

# Auto-format
black .
```

#### 4. isort (Import Sorter)
- Organizes imports automatically

```bash
# Check import order
isort --check-only .

# Auto-fix imports
isort .
```

#### 5. autoflake (Unused Import Remover)
- Removes unused imports and variables

```bash
# Remove unused imports
autoflake --remove-all-unused-imports --in-place --recursive .
```

### Type Checking

#### MyPy (Static Type Checker)
- Checks type hints
- Configuration in `pyproject.toml`

```bash
# Run MyPy
mypy . --ignore-missing-imports
```

### Security Scanning

#### Bandit (Security Linter)
- Finds common security issues
- Configuration in `pyproject.toml`

```bash
# Run Bandit
bandit -r . -c .bandit.yml
```

## Pre-Commit Hooks

Pre-commit hooks run automatically before each commit to ensure code quality.

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### Configured Hooks

1. **Secret Detection** - Prevents committing secrets
2. **Trailing Whitespace** - Removes trailing whitespace
3. **End of File Fixer** - Ensures newline at end of files
4. **YAML/JSON Validation** - Validates YAML and JSON files
5. **Black** - Formats Python code
6. **Ruff** - Lints Python code
7. **Flake8** - PEP8 compliance
8. **autoflake** - Removes unused imports
9. **Bandit** - Security scanning
10. **MyPy** - Type checking

### Running Hooks Manually

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## CI/CD Pipeline

Automated code quality checks run on every push and pull request.

### Linting Job

The CI/CD pipeline includes a dedicated linting job that runs:

1. **Ruff** - Modern linting
2. **Black** - Code formatting check
3. **isort** - Import order check
4. **Flake8** - PEP8 compliance check

### Type Checking Job

Separate job for static type checking with MyPy.

### Security Scanning Job

Dedicated security scanning with Bandit and other tools.

## Code Review Guidelines

### For Authors

- [ ] Run linters before committing (`pre-commit run --all-files`)
- [ ] Fix all linting issues
- [ ] Ensure code follows PEP 8 standards
- [ ] Add docstrings to public functions/classes
- [ ] Keep functions focused and under 50 lines
- [ ] Use meaningful variable names
- [ ] Add type hints to function signatures

### For Reviewers

- [ ] Check code style consistency
- [ ] Verify PEP 8 compliance
- [ ] Review exception handling
- [ ] Check for unused imports/variables
- [ ] Verify docstring presence and quality
- [ ] Assess code complexity
- [ ] Review security implications

## Common Issues and Fixes

### Operator Spacing (E226)

```python
# ❌ Bad
result = value*100
size = file_size//(1024*1024)

# ✅ Good
result = value * 100
size = file_size // (1024 * 1024)
```

### Trailing Whitespace (W291, W293)

```python
# ❌ Bad (has trailing spaces)
def function():    
    return True    

# ✅ Good (no trailing spaces)
def function():
    return True
```

### Unused Imports (F401)

```python
# ❌ Bad
from typing import List, Dict, Optional
from datetime import datetime

def get_items() -> List[str]:
    return ["item1", "item2"]

# ✅ Good (removed unused imports)
from typing import List

def get_items() -> List[str]:
    return ["item1", "item2"]
```

### Bare Except Clauses (E722)

```python
# ❌ Bad
try:
    risky_operation()
except:
    logger.error("Error")

# ✅ Good
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Value error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Quick Reference Commands

```bash
# Full code quality check
ruff check . && black --check . && isort --check-only . && flake8 agent/ api/ ml/

# Auto-fix all issues
ruff check . --fix && black . && isort . && autoflake --remove-all-unused-imports --in-place --recursive .

# Run pre-commit hooks
pre-commit run --all-files

# Type checking
mypy . --ignore-missing-imports

# Security scan
bandit -r . -c .bandit.yml
```

## Configuration Files

- **`.flake8`** - Flake8 configuration
- **`pyproject.toml`** - Ruff, Black, isort, MyPy, Bandit configuration
- **`.pre-commit-config.yaml`** - Pre-commit hooks configuration
- **`.github/workflows/ci-cd.yml`** - CI/CD pipeline configuration

## Resources

- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Pre-commit Documentation](https://pre-commit.com/)

## Enforcement

### Development Phase
- Pre-commit hooks prevent commits with code quality issues
- Local linting tools provide immediate feedback

### CI/CD Phase
- Automated checks on every push and pull request
- Warnings for code quality issues
- Required for merge to main/develop branches

### Code Review Phase
- Manual review ensures adherence to standards
- Feedback for improvement areas
- Learning opportunities for team

---

**Last Updated**: 2025-11-11  
**Version**: 1.0  
**Maintained by**: DevSkyy Platform Team
