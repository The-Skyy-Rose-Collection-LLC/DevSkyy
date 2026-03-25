---
description: Enforce TDD workflow. Tests FIRST, then implement. 80%+ coverage.
---

# TDD Command

Invokes **tdd-guide** agent for test-driven development.

## TDD Cycle
```
RED → GREEN → REFACTOR → REPEAT
RED:      Write failing test
GREEN:    Minimal code to pass
REFACTOR: Improve, keep tests passing
```

## Workflow
1. Define interfaces first
2. Write tests that FAIL
3. Run tests, verify failure
4. Write minimal implementation
5. Run tests, verify pass
6. Refactor while green
7. Check coverage (80%+)

## Test Types
- **Unit**: Functions in isolation
- **Integration**: API endpoints, database
- **E2E**: Critical user flows

## Coverage Requirements
- 80% minimum for all code
- 100% for financial/auth/security code

## Commands
```bash
npm test                    # Run tests
npm test -- --coverage      # With coverage
npm test -- --watch         # Watch mode
```

## Rules
- Tests BEFORE implementation
- Test behavior, not implementation
- Mock external dependencies
- Never skip the RED phase

## Related
- `/plan`, `/e2e`, Agent: `tdd-guide`
