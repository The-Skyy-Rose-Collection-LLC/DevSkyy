---
name: e2e-runner
description: Playwright E2E testing for critical user flows.
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

Create and maintain Playwright E2E tests for critical user journeys.

## Commands
```bash
npx playwright test                    # Run all
npx playwright test --headed           # See browser
npx playwright test --debug            # Debug mode
npx playwright codegen localhost:3000  # Generate tests
npx playwright show-report             # HTML report
```

## Test Structure
- Use Page Object Model pattern
- Use `data-testid` locators
- Wait for network/elements, not arbitrary timeouts
- Screenshot on failure

## Test Template
```typescript
test('user journey', async ({ page }) => {
  await page.goto('/path')
  await page.locator('[data-testid="element"]').click()
  await expect(page).toHaveURL(/expected/)
})
```

## Flaky Test Handling
- Run 3-5 times to verify stability
- Mark with `test.fixme()` if unstable
- Fix race conditions with proper waits

## Success Criteria
- Critical flows: 100% passing
- Overall pass rate: >95%
- Flaky rate: <5%
