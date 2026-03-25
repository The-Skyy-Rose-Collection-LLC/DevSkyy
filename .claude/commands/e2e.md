---
description: Generate and run Playwright E2E tests for critical user flows.
---

# E2E Command

Invokes **e2e-runner** agent to generate/run Playwright E2E tests.

## What It Does
1. Generate test journeys for user flows
2. Run tests across browsers
3. Capture artifacts (screenshots/videos on failure)
4. Identify and quarantine flaky tests

## Usage
```
/e2e Test the market search and view flow
```

## Commands
```bash
npx playwright test                   # Run all
npx playwright test --headed          # See browser
npx playwright test --debug           # Debug mode
npx playwright codegen localhost:3000 # Generate tests
npx playwright show-report            # View report
```

## Best Practices
- Use Page Object Model pattern
- Use `data-testid` locators
- Wait for network, not arbitrary timeouts
- Run 3-5 times to verify stability

## Related
- `/plan` - Identify flows to test
- `/tdd` - Unit tests
- Agent: `~/.claude/agents/e2e-runner.md`
