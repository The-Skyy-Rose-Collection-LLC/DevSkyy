# DevSkyy Scripts

This directory contains utility scripts for managing and validating the DevSkyy platform.

## Requirements Validation Scripts

### validate_requirements_fast.py (Recommended for CI/CD)

**Purpose:** Fast Python-based validation of all requirements files  
**Runtime:** ~2-5 seconds  
**Used in:** CI/CD pipelines

**Features:**
- ✅ Checks all requirements files exist
- ✅ Validates version pinning standards (== vs >= vs ~=)
- ✅ Detects duplicate package entries
- ✅ Verifies inheritance structure (-r requirements.txt)
- ✅ Fast execution (no package installation)

**Usage:**
```bash
python3 scripts/validate_requirements_fast.py
```

**Exit Codes:**
- `0`: All validations passed
- `1`: One or more validations failed

### validate_requirements.sh (Comprehensive Validation)

**Purpose:** Full validation with pip install --dry-run and security scanning  
**Runtime:** ~60-120 seconds  
**Used in:** Local development, pre-commit hooks

**Features:**
- ✅ All features from fast validation
- ✅ Runs `pip install --dry-run` on each file
- ✅ Security vulnerability scanning with `safety` and `pip-audit`
- ✅ Comprehensive syntax validation

**Usage:**
```bash
./scripts/validate_requirements.sh
```

**Requirements:**
```bash
pip install safety pip-audit
```

**Exit Codes:**
- `0`: All validations passed
- `1`: One or more validations failed

## When to Use Which Script

### Use `validate_requirements_fast.py` for:
- ✅ CI/CD pipelines (fast feedback)
- ✅ Pre-commit hooks (quick checks)
- ✅ Development workflow (rapid iteration)
- ✅ Automated testing

### Use `validate_requirements.sh` for:
- ✅ Pre-release validation (comprehensive)
- ✅ Security audits (vulnerability scanning)
- ✅ Manual reviews (detailed output)
- ✅ Release preparation

## Integration

### GitHub Actions (CI/CD)

Already integrated in `.github/workflows/ci-cd.yml`:

```yaml
jobs:
  validate-requirements:
    name: Validate Requirements Files
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11.9'
      - name: Run requirements validation
        run: python3 scripts/validate_requirements_fast.py
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-requirements
        name: Validate Requirements Files
        entry: python3 scripts/validate_requirements_fast.py
        language: system
        pass_filenames: false
        files: 'requirements.*\.txt$'
```

### Manual Validation

Before committing changes to requirements files:

```bash
# Quick check
python3 scripts/validate_requirements_fast.py

# Full validation
./scripts/validate_requirements.sh

# Test installation
pip install --dry-run -r requirements.txt
```

## Troubleshooting

### Common Issues

#### "File not found" errors
```bash
# Ensure you're running from repository root
cd /path/to/DevSkyy
python3 scripts/validate_requirements_fast.py
```

#### Duplicate package errors
```
✗ requirements-dev.txt - duplicates found:
  Line 186: 'pytest-benchmark' already defined at line 56
```

**Solution:** Remove the duplicate line or add a comment referencing the original

#### Version pinning warnings
```
⚠ requirements-dev.txt - pinning issues:
  Line 68: httpx uses >= instead of ==
```

**Solution:** Change `>=` to `==` for reproducible builds (except for `setuptools`)

#### Inheritance errors
```
✗ requirements-dev.txt - inheritance issues:
  requirements-dev.txt should inherit from requirements.txt using '-r requirements.txt'
```

**Solution:** Add `-r requirements.txt` at the top of the file

## Validation Rules

### 1. Version Pinning
- **Production files** (requirements.txt, requirements-production.txt, etc.): Use `==` for all packages
- **Exception**: Build tools like `setuptools` can use `>=`
- **Development files**: Use `==` for reproducibility

### 2. No Duplicates
- Each package should appear only once per file
- Use comments to reference where packages are defined

### 3. Inheritance
- `requirements-dev.txt` must inherit from `requirements.txt`
- `requirements-test.txt` must inherit from `requirements.txt`
- Use `-r requirements.txt` at the top of the file

### 4. File Structure
All required files must exist:
- requirements.txt
- requirements-dev.txt
- requirements-test.txt
- requirements-production.txt
- requirements.minimal.txt
- requirements.vercel.txt
- requirements_mcp.txt
- requirements-luxury-automation.txt
- wordpress-mastery/docker/ai-services/requirements.txt

## See Also

- [DEPENDENCIES.md](../DEPENDENCIES.md) - Comprehensive dependency management guide
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [.github/workflows/ci-cd.yml](../.github/workflows/ci-cd.yml) - CI/CD pipeline configuration
