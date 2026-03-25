---
name: tdd-workflow
description: Test-driven development with 80%+ coverage enforcement.
---

# TDD Workflow

## Core Principle

**Write tests BEFORE code. Always.**

## TDD Steps

1. **Write test** (RED) - Test should fail
2. **Implement** (GREEN) - Minimal code to pass
3. **Refactor** (IMPROVE) - Clean up, tests stay green
4. **Verify** - 80%+ coverage

## Test Types
- **Unit**: Functions, utilities | **Integration**: API, DB | **E2E**: Playwright

## Test Pattern

```typescript
describe('Feature', () => {
  it('does X when Y', async () => {
    const result = await feature(input)
    expect(result).toBe(expected)
  })
  it('handles edge case', async () => { /* ... */ })
  it('handles errors', async () => { /* ... */ })
})
```

## Coverage Commands

```bash
npm test -- --coverage    # Run with coverage
pytest --cov=. --cov-report=html  # Python coverage
```

## Avoid

- Testing implementation details (test behavior)
- Brittle selectors (use data-testid)
- Test interdependence (isolate each test)

## Related Tools
- **Agent**: `tdd-guide`, `e2e-runner` | **Command**: `/tdd` | **Skill**: `test-and-commit`
