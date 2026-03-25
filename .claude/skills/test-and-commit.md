---
name: test-and-commit
description: TDD workflow automation - test, format, commit with coverage.
---

# TDD Workflow Automation

## Workflow

```
Detect Changes → Run Tests → Format Code → Commit
```

## Commands

```bash
# 1. Detect changes
git diff --name-only HEAD | grep '\.py$'

# 2. Run tests with coverage
pytest tests/ -v --cov=. --cov-report=term --junitxml=test-results.xml

# 3. Format code
isort . && ruff check --fix . && black .

# 4. Commit (only if tests pass)
git add -A && git commit -m "test: update tests with X% coverage"
```

## Success Criteria

- [ ] All tests pass (0 failures)
- [ ] Coverage > 70%
- [ ] Code formatted (isort, ruff, black)

## Error Handling

- **Tests fail**: Fix tests first, DO NOT commit
- **Coverage drops**: Add missing test cases
- **Formatting fails**: Run `/fix-linting`

## Related Tools

- **Command**: `/tdd` for guided TDD workflow
- **Command**: `/verify` for pre-commit checks
- **Agent**: `tdd-guide` for test-first methodology
- **Agent**: `build-error-resolver` for test failures
- **Skill**: `fix-linting` for format issues
