# DevSkyy Dependencies Management Guide

**Last Updated:** 2025-11-12  
**Version:** 2.0.0

## Overview

This document describes the dependency management strategy for the DevSkyy Enterprise Platform. All requirements files follow strict versioning and inheritance standards to ensure reproducibility, security, and maintainability.

## Requirements Files Structure

### Base Production Dependencies

#### `requirements.txt`
- **Purpose:** Core production dependencies for full-featured deployment
- **Scope:** All production features including ML, AI, and advanced capabilities
- **Versioning:** All packages pinned with `==` (except build tools like `setuptools`)
- **Usage:** Full production deployment with all features enabled
- **Install:** `pip install -r requirements.txt`

**Key Features:**
- ✅ All versions pinned for reproducibility
- ✅ Latest security patches applied
- ✅ No duplicate packages
- ✅ Comprehensive comments explaining each dependency
- ✅ Regular security audits

### Environment-Specific Dependencies

#### `requirements-dev.txt`
- **Purpose:** Development tools and quality assurance
- **Inheritance:** `-r requirements.txt` (inherits all production dependencies)
- **Scope:** Linting, formatting, type checking, profiling, debugging
- **Versioning:** All packages pinned with `==` for reproducibility
- **Usage:** Local development environment setup
- **Install:** `pip install -r requirements-dev.txt`

**Includes:**
- Code formatters: black, isort, autopep8
- Linters: flake8, pylint, mypy, ruff
- Security scanners: bandit, safety, semgrep
- Documentation tools: sphinx, mkdocs
- Profiling tools: py-spy, memory-profiler

#### `requirements-test.txt`
- **Purpose:** Testing framework and utilities
- **Inheritance:** `-r requirements.txt` (inherits all production dependencies)
- **Scope:** Unit, integration, performance, and security testing
- **Versioning:** All packages pinned with `==` for reproducibility
- **Usage:** CI/CD test execution
- **Install:** `pip install -r requirements-test.txt`

**Includes:**
- Testing frameworks: pytest, pytest-asyncio, pytest-cov
- Test utilities: factory-boy, faker, hypothesis
- Mocking tools: pytest-mock, responses, httpretty
- Load testing: locust, artillery
- Browser testing: selenium, playwright

### Lightweight/Minimal Deployments

#### `requirements-production.txt`
- **Purpose:** Lightweight production deployment without heavy ML libraries
- **Inheritance:** None (standalone, excludes torch, tensorflow, transformers)
- **Scope:** Core API functionality with lightweight AI SDK integrations only
- **Versioning:** All packages pinned with `==`
- **Usage:** Containerized deployments where image size matters
- **Install:** `pip install -r requirements-production.txt`

**Use Cases:**
- Docker production containers with size constraints
- Deployments not requiring ML model inference
- API-only services with external ML service calls

#### `requirements.minimal.txt`
- **Purpose:** Absolute minimum for API functionality
- **Inheritance:** None (standalone, minimal subset)
- **Scope:** FastAPI, database, authentication, basic utilities
- **Versioning:** All packages pinned with `==`
- **Usage:** Ultra-lightweight deployments, edge computing
- **Install:** `pip install -r requirements.minimal.txt`

**Use Cases:**
- Edge deployments with severe resource constraints
- Microservices with limited scope
- Health check/status endpoints only

### Specialized Deployments

#### `requirements.vercel.txt`
- **Purpose:** Serverless deployment on Vercel platform
- **Inheritance:** None (standalone, Vercel-optimized)
- **Scope:** Serverless-compatible packages only
- **Versioning:** All packages pinned with `==`
- **Usage:** Vercel serverless functions
- **Install:** Automatic via Vercel build process

**Optimizations:**
- Excludes large ML libraries
- Optimized for fast cold starts
- Serverless platform compatibility verified

#### `requirements_mcp.txt`
- **Purpose:** Model Context Protocol (MCP) server dependencies
- **Inheritance:** None (standalone, MCP-specific)
- **Scope:** FastMCP framework and MCP protocol support
- **Versioning:** All packages pinned with `==`
- **Usage:** MCP server deployment
- **Install:** `pip install -r requirements_mcp.txt`

**Key Packages:**
- fastmcp: MCP server framework
- mcp: Model Context Protocol core
- httpx, pydantic: Supporting libraries

#### `requirements-luxury-automation.txt`
- **Purpose:** Luxury fashion automation with full ML stack
- **Inheritance:** None (standalone, specialized ML versions)
- **Scope:** PyTorch, HuggingFace, computer vision, NLP
- **Versioning:** All packages pinned with `==`
- **Usage:** Luxury fashion AI features
- **Install:** `pip install -r requirements-luxury-automation.txt`

**Special Requirements:**
- Python 3.11+ required
- CUDA 11.8+ for GPU acceleration
- 16GB+ RAM recommended
- 12GB+ GPU RAM for Stable Diffusion XL

#### `wordpress-mastery/docker/ai-services/requirements.txt`
- **Purpose:** WordPress AI services Docker container
- **Inheritance:** None (standalone, Flask-based)
- **Scope:** Flask, AI/ML for WordPress integration
- **Versioning:** All packages pinned with `==`
- **Usage:** WordPress AI services container
- **Install:** `pip install -r wordpress-mastery/docker/ai-services/requirements.txt`

## Versioning Standards

### Version Pinning Rules

1. **Production Dependencies (`requirements.txt`)**
   - ✅ Use `==` for all packages (exact version pinning)
   - ✅ Exception: Build tools like `setuptools` can use `>=`
   - ❌ Never use `~=` or bare `>=` for runtime dependencies

2. **Development/Test Dependencies**
   - ✅ Use `==` for all packages (reproducible dev environments)
   - ✅ Inherit from `requirements.txt` via `-r`
   - ❌ Avoid version ranges (>=, ~=) for reproducibility

3. **Lightweight Deployments**
   - ✅ Use `==` for all packages
   - ✅ Keep synchronized with main requirements.txt versions where possible
   - ✅ Document any version differences with comments

### Version Update Process

1. **Security Updates (Critical)**
   ```bash
   # Check for vulnerabilities
   pip-audit -r requirements.txt
   
   # Update specific package
   pip install --upgrade <package>==<new_version>
   
   # Test thoroughly
   pytest tests/
   
   # Update requirements file
   # Update CHANGELOG with CVE fixes
   ```

2. **Regular Updates (Monthly)**
   ```bash
   # Check for outdated packages
   pip list --outdated
   
   # Update in development environment first
   pip install --upgrade <package>
   
   # Run full test suite
   pytest tests/ -v
   
   # Update requirements.txt
   # Update DEPENDENCIES.md changelog
   ```

3. **Breaking Changes (Major versions)**
   ```bash
   # Create feature branch
   git checkout -b update/package-v2
   
   # Update package
   pip install <package>==2.0.0
   
   # Update code for compatibility
   # Run full test suite
   # Update documentation
   # Submit PR for review
   ```

## Inheritance Strategy

### Using `-r` for Inheritance

Development and test requirements inherit from production:

```txt
# requirements-dev.txt
-r requirements.txt

# Additional dev-only packages
black==24.10.0
pytest==8.4.2
```

**Benefits:**
- ✅ Ensures dev/test environments match production
- ✅ Reduces duplication and conflicts
- ✅ Easier to maintain consistency

**When NOT to use inheritance:**
- Lightweight deployments (requirements-production.txt)
- Platform-specific files (requirements.vercel.txt)
- Specialized stacks (requirements-luxury-automation.txt)

## Validation & Testing

### Automated Validation

Run the validation script:

```bash
./scripts/validate_requirements.sh
```

**Validation Checks:**
1. ✅ All files exist
2. ✅ Syntax validation (pip install --dry-run)
3. ✅ Version pinning standards
4. ✅ Inheritance structure
5. ✅ No duplicate packages
6. ✅ Security vulnerability scanning

### CI/CD Integration

All requirements files are validated in CI/CD:

```yaml
# .github/workflows/ci-cd.yml
- name: Validate requirements files
  run: |
    ./scripts/validate_requirements.sh
```

### Manual Testing

Test individual files:

```bash
# Test syntax
pip install --dry-run -r requirements.txt

# Test installation
pip install -r requirements.txt

# Test for conflicts
pip check

# Check for vulnerabilities
safety check -r requirements.txt
pip-audit -r requirements.txt
```

## Dependency Conflict Resolution

### Common Conflicts

1. **Version Conflicts**
   ```
   ERROR: Package A requires foo>=2.0, but Package B requires foo<2.0
   ```
   
   **Resolution:**
   - Check if both packages can use a compatible version
   - Update to latest versions that are compatible
   - Consider alternative packages if conflict persists
   - Document the constraint

2. **Duplicate Packages**
   ```
   Package X appears multiple times in requirements.txt
   ```
   
   **Resolution:**
   - Keep only one entry (usually the more specific version)
   - Check for extras (e.g., `pydantic[email]` vs `pydantic`)
   - Update comments to reflect combined requirements

3. **Platform Incompatibilities**
   ```
   Package Y is not available on Windows/MacOS/Linux
   ```
   
   **Resolution:**
   - Use platform-specific markers: `package; sys_platform == 'linux'`
   - Provide alternative packages for different platforms
   - Document platform requirements

### Conflict Prevention

1. **Regular Updates**
   - Update dependencies monthly
   - Test updates in development first
   - Use dependency scanning tools

2. **Version Ranges**
   - Avoid in production (use exact pins)
   - Test with latest compatible versions
   - Pin after testing

3. **Dependency Scanning**
   ```bash
   # Check dependency tree
   pipdeptree
   
   # Check for conflicts
   pip check
   
   # Analyze dependencies
   pip-audit -r requirements.txt
   ```

## Security Management

### Security Scanning

1. **Automated Scans (CI/CD)**
   ```bash
   # safety check (database of known vulnerabilities)
   safety check -r requirements.txt
   
   # pip-audit (official PyPI advisory database)
   pip-audit -r requirements.txt
   
   # Bandit (code security linting)
   bandit -r agent/ api/
   
   # Semgrep (SAST scanning)
   semgrep --config auto
   ```

2. **Manual Security Review**
   - Review Dependabot alerts
   - Check GitHub Security Advisories
   - Monitor CVE databases
   - Subscribe to security mailing lists

### Security Update Workflow

1. **Critical Security Patch (< 24 hours)**
   ```bash
   # 1. Create hotfix branch
   git checkout -b security/cve-xxxx-xxxx
   
   # 2. Update vulnerable package
   # Edit requirements.txt
   
   # 3. Run quick tests
   pytest tests/security/
   
   # 4. Deploy immediately
   git commit -m "security: Fix CVE-XXXX-XXXX in package X"
   git push origin security/cve-xxxx-xxxx
   # Create PR, get expedited review, merge, deploy
   ```

2. **Medium/Low Priority Updates (< 7 days)**
   - Include in regular update cycle
   - Test thoroughly
   - Deploy with next release

### Security Documentation

Document all security updates in:
- CHANGELOG.md
- requirements.txt comments
- Security advisories
- Pull request descriptions

## Upgrade Procedures

### Minor Version Upgrades (1.2.3 → 1.2.4)

```bash
# 1. Update in requirements.txt
nano requirements.txt
# Change: package==1.2.3
# To: package==1.2.4

# 2. Install and test
pip install -r requirements.txt
pytest tests/

# 3. Commit
git add requirements.txt
git commit -m "deps: Upgrade package to 1.2.4"
```

### Major Version Upgrades (1.x → 2.x)

```bash
# 1. Create feature branch
git checkout -b upgrade/package-v2

# 2. Update package version
nano requirements.txt

# 3. Check for breaking changes
# Review package CHANGELOG/migration guide

# 4. Update code for compatibility
# Make necessary code changes

# 5. Run full test suite
pytest tests/ -v --cov

# 6. Update documentation
# Update DEPENDENCIES.md, CHANGELOG.md

# 7. Submit PR
git push origin upgrade/package-v2
```

### Bulk Upgrades (Multiple Packages)

```bash
# 1. Use pip-upgrader or similar tool
pip install pip-upgrader
pip-upgrade requirements.txt

# 2. Review changes carefully
git diff requirements.txt

# 3. Test incrementally
# Update a few packages at a time
pytest tests/

# 4. Document all changes
# Update CHANGELOG.md
```

## Best Practices

### DO ✅

1. **Pin all production dependencies** with `==`
2. **Use `-r` inheritance** for dev/test requirements
3. **Document all packages** with inline comments
4. **Run validation script** before committing
5. **Test in development** before updating production
6. **Keep versions synchronized** across related files
7. **Update regularly** to get security patches
8. **Use virtual environments** for isolation
9. **Check for vulnerabilities** with safety/pip-audit
10. **Document breaking changes** in CHANGELOG

### DON'T ❌

1. **Don't use version ranges** (>=, ~=) in production
2. **Don't duplicate packages** in the same file
3. **Don't mix versions** of the same package across files
4. **Don't commit untested updates**
5. **Don't ignore security warnings**
6. **Don't skip validation** scripts
7. **Don't update too many** packages at once
8. **Don't forget to update** related files
9. **Don't bypass CI/CD** for dependency changes
10. **Don't leave conflicts** unresolved

## Troubleshooting

### Common Issues

#### Issue: "Dependency conflict detected"
```
ERROR: package-a 1.0.0 requires package-b>=2.0, but you have package-b 1.5
```

**Solution:**
```bash
# Check what requires package-b
pipdeptree -p package-b

# Update package-b to compatible version
pip install package-b==2.0.0

# Update requirements.txt
# Test thoroughly
```

#### Issue: "Package not found"
```
ERROR: Could not find a version that satisfies the requirement package-x==1.0.0
```

**Solution:**
```bash
# Check if package name is correct
pip search package-x

# Check if version exists
pip install package-x==
# Will show available versions

# Update to available version
```

#### Issue: "Build failed on Windows/MacOS"
```
ERROR: Failed building wheel for package-y
```

**Solution:**
```bash
# Install platform-specific binary
pip install package-y --only-binary :all:

# Or use platform markers in requirements.txt
package-y==1.0.0; sys_platform == 'linux'
package-y-windows==1.0.0; sys_platform == 'win32'
```

## Version History

### 2.0.0 (2025-11-12)
- ✅ Removed all duplicate packages from requirements.txt
- ✅ Converted all dev/test files to use `==` pinning
- ✅ Updated all specialized files to latest versions
- ✅ Synchronized versions across all requirements files
- ✅ Added validation script for CI/CD
- ✅ Created comprehensive documentation

### 1.0.0 (2024-10-24)
- Initial dependency management documentation
- Basic requirements file structure
- Security update workflow

## Support

For questions or issues with dependencies:
1. Check this documentation first
2. Run validation script: `./scripts/validate_requirements.sh`
3. Create GitHub issue with `dependencies` label
4. Tag @maintainers for urgent security issues

## References

- [pip Requirements File Format](https://pip.pypa.io/en/stable/reference/requirements-file-format/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [PyPI Security Advisories](https://pypi.org/security/)
