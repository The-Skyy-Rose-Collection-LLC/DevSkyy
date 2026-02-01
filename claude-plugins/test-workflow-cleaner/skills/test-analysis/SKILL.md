# Test Analysis

This skill provides knowledge for analyzing test suites to identify outdated, orphaned, or irrelevant tests. It activates when users mention "analyze tests", "find outdated tests", "test coverage", "orphaned tests", "dead tests", or need to audit their test suite.

---

## Test Analysis Workflow

### 1. Discovery Phase

Scan the codebase to build a test inventory:

```bash
# Find all test files
find . -name "test_*.py" -o -name "*_test.py" -o -name "*.test.js" -o -name "*.spec.ts" -o -name "*_test.go"

# Count tests per file (Python)
grep -c "def test_" tests/*.py

# Count tests per file (JavaScript)
grep -c "it\('" tests/*.test.js
```

### 2. Mapping Tests to Source

Build relationships between tests and source code:

| Test Pattern | Likely Source |
|--------------|---------------|
| `test_user.py` | `user.py`, `models/user.py` |
| `test_api_endpoints.py` | `api/endpoints.py`, `api/routes.py` |
| `UserService.test.ts` | `UserService.ts` |
| `api_test.go` | `api.go` |

### 3. Detecting Outdated Tests

**Indicators of outdated tests:**

1. **Import Errors**: Test imports modules/functions that no longer exist
2. **Missing References**: Test references classes, methods, or variables removed from source
3. **Stale Mocks**: Mocking functions/methods that have changed signatures
4. **Dead Assertions**: Asserting on properties/methods that no longer exist
5. **Skipped/Ignored**: Tests marked skip with no plan to re-enable
6. **Old Comments**: TODO/FIXME comments older than 6 months

### 4. Analysis Commands

#### Python (pytest)
```bash
# Check for import errors without running tests
python -m py_compile tests/*.py

# Find skipped tests
grep -r "@pytest.mark.skip" tests/
grep -r "pytest.skip(" tests/

# Find tests with old TODO comments
grep -rn "TODO\|FIXME" tests/ | head -20
```

#### JavaScript (Jest)
```bash
# Find skipped tests
grep -r "it.skip\|describe.skip\|test.skip\|xit\|xdescribe" tests/

# Find tests with only
grep -r "it.only\|describe.only\|test.only" tests/

# Check for syntax errors
npx eslint tests/ --ext .test.js,.spec.js
```

## Orphaned Test Detection

### Definition
Orphaned tests are tests whose target source code has been:
- Deleted entirely
- Renamed without updating tests
- Moved to a different module
- Significantly refactored

### Detection Strategy

```python
# Pseudo-code for orphan detection
def find_orphaned_tests(test_files, source_files):
    orphans = []

    for test_file in test_files:
        # Extract what the test is testing
        imports = extract_imports(test_file)
        references = extract_class_and_function_refs(test_file)

        for ref in references:
            if not exists_in_source(ref, source_files):
                orphans.append({
                    'test_file': test_file,
                    'missing_ref': ref,
                    'type': 'orphaned'
                })

    return orphans
```

### Common Orphan Patterns

| Pattern | Example | Issue |
|---------|---------|-------|
| Deleted module | `from old_module import func` | Module removed |
| Renamed class | `TestOldClassName` | Class renamed to `NewClassName` |
| Moved function | `from utils import helper` | Helper moved to `utils.helpers` |
| Removed endpoint | `test_delete_v1_endpoint` | API v1 deprecated |

## Test Quality Metrics

### Coverage Analysis
```bash
# Python coverage
pytest --cov=src --cov-report=term-missing

# JavaScript coverage
npm test -- --coverage --coverageReporters=text

# Go coverage
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out
```

### Quality Indicators

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| Line Coverage | >80% | 60-80% | <60% |
| Branch Coverage | >70% | 50-70% | <50% |
| Tests per File | 1+ | 0 (new) | 0 (old) |
| Assertion Density | 2+ per test | 1 | 0 |
| Test Execution Time | <100ms | 100-500ms | >500ms |

## Analysis Report Format

```markdown
# Test Analysis Report

## Summary
- Total test files: X
- Total tests: Y
- Coverage: Z%

## Issues Found

### Critical (Must Fix)
- [ ] `test_old_api.py` - References deleted `OldAPI` class
- [ ] `test_utils.py::test_deprecated_func` - Function removed in v2.0

### Warnings (Review)
- [ ] `test_user.py` - 3 tests skipped for 6+ months
- [ ] `test_cache.py` - Low assertion density (0.5 per test)

### Suggestions
- [ ] `api/endpoints.py` - No test coverage
- [ ] `test_integration.py` - Consider splitting (47 tests)

## Outdated Tests (Candidates for Removal)
| File | Test | Reason | Last Modified |
|------|------|--------|---------------|
| test_v1.py | test_old_endpoint | API v1 removed | 2024-06-01 |
| test_legacy.py | * | Legacy module deleted | 2024-03-15 |
```

## Automated Detection Script

```python
#!/usr/bin/env python3
"""Analyze test suite for outdated tests."""

import ast
import os
from pathlib import Path

def analyze_test_file(test_path: Path, source_paths: list[Path]) -> dict:
    """Analyze a single test file for issues."""
    issues = []

    with open(test_path) as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {'file': str(test_path), 'issues': [{'type': 'syntax_error', 'detail': str(e)}]}

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not module_exists(alias.name, source_paths):
                    issues.append({
                        'type': 'missing_import',
                        'module': alias.name,
                        'line': node.lineno
                    })
        elif isinstance(node, ast.ImportFrom):
            if node.module and not module_exists(node.module, source_paths):
                issues.append({
                    'type': 'missing_import',
                    'module': node.module,
                    'line': node.lineno
                })

    return {'file': str(test_path), 'issues': issues}

def module_exists(module_name: str, source_paths: list[Path]) -> bool:
    """Check if a module exists in source paths."""
    module_path = module_name.replace('.', '/')
    for source_path in source_paths:
        if (source_path / f"{module_path}.py").exists():
            return True
        if (source_path / module_path / "__init__.py").exists():
            return True
    return False
```

## Integration with CI/CD

Add test analysis to your pipeline:

```yaml
# GitHub Actions
- name: Analyze Tests
  run: |
    python scripts/analyze_tests.py --output report.json
    if [ $(jq '.critical | length' report.json) -gt 0 ]; then
      echo "Critical test issues found!"
      exit 1
    fi
```
