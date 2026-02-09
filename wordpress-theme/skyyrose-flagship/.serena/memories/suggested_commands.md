# SkyyRose Theme - Development Commands

## Build Commands
```bash
# Build all assets (JS + CSS)
npm run build

# Build JavaScript only
npm run build:js

# Build CSS only
npm run build:css
```

## Testing Commands
```bash
# Run all tests
npm run test:all

# Unit tests (Jest)
npm run test:js
npm run test:js:watch      # Watch mode
npm run test:js:coverage   # With coverage

# E2E tests (Playwright)
npm run test:e2e
npm run test:e2e:ui        # UI mode
npm run test:e2e:debug     # Debug mode

# Validation tests
npm run test:validate      # Theme structure validation
npm run test:performance   # Lighthouse performance
npm run test:accessibility # Pa11y + Axe accessibility
npm run test:browsers      # Cross-browser testing
npm run test:3d            # Three.js validation
```

## Code Quality
```bash
# Lint JavaScript
npm run lint:js
npm run lint:js:fix        # Auto-fix

# Format code
npm run format             # Prettier
```

## WordPress Development
```bash
# No specific WordPress CLI commands in package.json
# Use WP-CLI directly if needed:
# wp theme activate skyyrose-flagship
# wp server --host=localhost --port=8080
```

## Task Completion Checklist
1. Run `npm run lint:js:fix` to fix linting errors
2. Run `npm run test:js` to verify unit tests pass
3. Run `npm run test:e2e` for E2E validation
4. Run `npm run build` to create production assets
5. Test in browser (local WordPress install)
6. Check PHP error log for runtime errors
7. Validate with `npm run test:validate`
