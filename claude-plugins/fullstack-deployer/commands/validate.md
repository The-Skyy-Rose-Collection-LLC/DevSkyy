---
name: validate
description: Run full validation suite including tests, type checks, and health checks
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - Task
argument-hint: "[--pre-deploy|--post-deploy|--full]"
---

# Validate Command

Run comprehensive validation suite to ensure code quality and deployment health.

## Validation Modes

### Pre-Deployment (`--pre-deploy`)
```
/validate --pre-deploy
```
Run before deployment:
- TypeScript check
- ESLint
- Unit tests
- Build verification

### Post-Deployment (`--post-deploy`)
```
/validate --post-deploy
```
Run after deployment:
- Health endpoint check
- WordPress connectivity
- WooCommerce connectivity
- Smoke tests

### Full Validation (`--full` or no flag)
```
/validate --full
/validate
```
Run everything:
- All pre-deployment checks
- Build
- E2E tests
- All post-deployment checks (if URL provided)

## Execution Steps

### Pre-Deployment Validation
```bash
# TypeScript
npx tsc --noEmit

# Linting
npm run lint

# Unit Tests
npm test

# Build
npm run build
```

### Post-Deployment Validation
```bash
# Health check
curl -s "${DEPLOYMENT_URL}/api/health"

# Homepage
curl -s -o /dev/null -w "%{http_code}" "${DEPLOYMENT_URL}"

# WordPress
curl -s "${DEPLOYMENT_URL}/api/health" | jq '.services.wordpress'

# WooCommerce
curl -s "${DEPLOYMENT_URL}/api/health" | jq '.services.woocommerce'
```

### E2E Tests (Full mode)
```bash
# Run Playwright tests
npx playwright test

# Or against production
PLAYWRIGHT_BASE_URL=${DEPLOYMENT_URL} npx playwright test
```

## Output Format

```
Validation Results
═══════════════════════════════════════

Pre-Deployment:
├── TypeScript: ✅ Pass
├── ESLint: ✅ Pass (0 errors, 0 warnings)
├── Unit Tests: ✅ 45/45 passing
└── Build: ✅ Success

Post-Deployment:
├── Homepage: ✅ HTTP 200 (234ms)
├── Health Check: ✅ Healthy
├── WordPress: ✅ Connected (156ms)
├── WooCommerce: ✅ Connected (189ms)
└── E2E Tests: ✅ 12/12 passing

Overall: ✅ All validations passed
```

## Example Usage

```
/validate                # Full validation
/validate --pre-deploy   # Only pre-deployment checks
/validate --post-deploy  # Only post-deployment checks
/validate --full         # Everything including E2E
```

## Error Handling

If validation fails:
1. Capture specific failure
2. Attempt auto-fix if possible
3. Use Context7 for complex errors
4. Re-run validation
5. Report status

Use test-validator or error-resolver agents for persistent issues.
