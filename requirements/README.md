# Dependency Management with pip-tools

This directory uses [pip-tools](https://pip-tools.readthedocs.io/en/latest/) for deterministic, reproducible dependency management.

## Directory Structure

```
requirements/
├── base.in      # Production dependencies (source)
├── base.txt     # Production dependencies (lock file, generated)
├── dev.in       # Development dependencies (source)
├── dev.txt      # Development dependencies (lock file, generated)
├── test.in      # Test dependencies (source)
├── test.txt     # Test dependencies (lock file, generated)
├── Makefile     # Automation commands
└── README.md    # This file
```

## Quick Start

### Install pip-tools
```bash
pip install pip-tools
```

### Compile Dependencies
```bash
cd requirements/
make compile
```

### Install for Development
```bash
make sync-dev
```

### Install for CI/CD Testing
```bash
make sync-test
```

### Install for Production
```bash
make sync-prod
```

## Workflow

### Adding a New Dependency

1. **Edit the appropriate `.in` file:**
   - `base.in` - Production dependencies
   - `dev.in` - Development tools (linters, formatters)
   - `test.in` - Test frameworks and fixtures

2. **Recompile:**
   ```bash
   make compile
   ```

3. **Commit both `.in` and `.txt` files:**
   ```bash
   git add requirements/
   git commit -m "deps: add new-package"
   ```

### Upgrading Dependencies

```bash
# Upgrade all dependencies
make upgrade

# Upgrade a specific package
pip-compile --upgrade-package requests base.in -o base.txt
```

### Verifying Lock Files

```bash
make verify
```

## Layered Dependencies

Dependencies are organized in layers with constraints:

```
base.in (production)
    ↓
dev.in (development) ─── uses `-c base.txt` constraint
    ↓
test.in (testing) ────── uses `-c base.txt` constraint
```

This ensures dev/test environments use the exact same versions of production dependencies.

## Security

- All `.txt` files include package hashes for integrity verification
- Security-critical packages use `>=,<` version ranges per CLAUDE.md
- Run `make upgrade` monthly to get security patches

## Reference

- [pip-tools Documentation](https://pip-tools.readthedocs.io/en/latest/)
- [pip-compile CLI](https://pip-tools.readthedocs.io/en/latest/cli/pip-compile/)
- [GitHub: jazzband/pip-tools](https://github.com/jazzband/pip-tools)
