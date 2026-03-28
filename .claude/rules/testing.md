# Testing Requirements

## Minimum Test Coverage: 85%

Test Types (ALL required):
1. **Unit Tests** - Individual functions, utilities, components
2. **Integration Tests** - API endpoints, database operations (in `tests/integration/`)
3. **E2E Tests** - Critical user flows (Playwright)

## Test Commands
- `pytest tests/ -v` after EVERY change
- `pytest tests/ -k "name" -v` for specific tests
- `pytest tests/ -m integration` for integration only
- `make test-cov` for coverage report

## Test-Driven Development

MANDATORY workflow:
1. Write test first (RED)
2. Run test - it should FAIL
3. Write minimal implementation (GREEN)
4. Run test - it should PASS
5. Refactor (IMPROVE)
6. Verify coverage (85%+)

## Troubleshooting Test Failures

1. Use **tdd-guide** agent
2. Check test isolation
3. Verify mocks are correct
4. Fix implementation, not tests (unless tests are wrong)
5. No mocks in integration/e2e tests

## Agent Support

- **tdd-guide** - Use PROACTIVELY for new features, enforces write-tests-first
- **e2e-runner** - Playwright E2E testing specialist
