# SkyyRose Flagship Theme - Testing Documentation

## Overview

This document provides an overview of the complete testing and validation suite for the SkyyRose Flagship WordPress/WooCommerce theme with 3D capabilities.

## Quick Start

### Setup

```bash
# Install dependencies
npm install
composer install

# Make scripts executable
chmod +x scripts/*.sh

# Install Playwright browsers
npx playwright install
```

### Run All Tests

```bash
# Complete test suite
./scripts/run-all-tests.sh http://localhost:8080

# Individual test types
npm run test:js              # JavaScript tests
npm run test:e2e             # End-to-end tests
composer test                # PHP tests
./scripts/validate-theme.sh  # Theme validation
```

## Test Suite Components

### 1. Manual Testing Checklist

**Location:** `tests/checklist.md`

Comprehensive manual testing checklist covering:
- ✓ 3D experience functionality (scene loading, model display, controls)
- ✓ WooCommerce flows (browse, cart, checkout)
- ✓ Responsive design (320px to 1920px+)
- ✓ Browser compatibility (Chrome, Firefox, Safari, Edge)
- ✓ Accessibility audit (WCAG 2.1 AA)
- ✓ SEO validation
- ✓ Performance testing
- ✓ Security testing

**Usage:** Print or open the markdown file and check off items as you test.

### 2. PHP Unit Tests

**Location:** `tests/unit/` and `tests/integration/`

Tests for WordPress and WooCommerce functionality:
- Theme setup and configuration
- Template functions
- WooCommerce integration
- Product operations
- Cart and checkout
- Security features

**Run tests:**
```bash
composer test
composer test:coverage  # With coverage report
```

**Configuration:** `tests/phpunit.xml`

### 3. JavaScript Tests

**Location:** `tests/unit/*.test.js`

Tests for 3D scene and JavaScript functionality:
- Three.js scene initialization
- 3D model loading
- Camera controls
- Animation loops
- Error handling
- Memory management
- Performance monitoring

**Run tests:**
```bash
npm run test:js
npm run test:js:watch     # Watch mode
npm run test:js:coverage  # With coverage
```

**Configuration:** `tests/jest.config.js`, `tests/jest.setup.js`

### 4. End-to-End Tests

**Location:** `tests/e2e/specs/`

Complete user flow testing:
- Product browsing and filtering
- Add to cart functionality
- Cart management
- Complete checkout process
- Product variations
- Responsive design
- 3D viewer interaction

**Run tests:**
```bash
npm run test:e2e
npm run test:e2e:ui       # UI mode
npm run test:e2e:debug    # Debug mode
```

**Configuration:** `tests/e2e/playwright.config.js`

### 5. Validation Scripts

**Location:** `scripts/`

Automated validation and testing scripts:

#### Theme Validation (`validate-theme.sh`)
- Checks WordPress theme requirements
- Validates file structure
- Verifies security best practices
- Checks WooCommerce integration

#### Performance Testing (`test-performance.sh`)
- Runs Lighthouse performance tests
- Measures page load times
- Analyzes asset sizes
- Provides optimization recommendations

#### Accessibility Testing (`check-accessibility.sh`)
- Runs axe-core accessibility tests
- Executes pa11y WCAG compliance tests
- Checks ARIA landmarks and semantic HTML
- Validates keyboard navigation

#### Browser Compatibility (`test-browsers.sh`)
- Tests across Chrome, Firefox, Safari, Edge
- Feature detection (WebGL, ES6, CSS features)
- Responsive design validation
- Screenshot comparison

#### 3D Asset Validation (`validate-3d.sh`)
- Validates GLB/GLTF model files
- Checks texture files and sizes
- Verifies Three.js integration
- Provides optimization recommendations

#### Master Test Runner (`run-all-tests.sh`)
- Executes all tests in sequence
- Generates comprehensive report
- Saves all results to coverage directory

## Test Data

### Sample Products

**Location:** `tests/fixtures/sample-products.json`

Pre-configured test data:
- 5 sample products (simple and variable)
- 2 test user accounts
- 3 discount coupons
- 3 product collections

**Import:**
```bash
wp import tests/fixtures/sample-products.json --authors=create
```

### Test Users

| Username | Password | Role |
|----------|----------|------|
| testcustomer1 | TestPass123! | Customer |
| testcustomer2 | TestPass123! | Customer |

### Test Coupons

| Code | Type | Amount |
|------|------|--------|
| WELCOME10 | Percentage | 10% |
| LUXURY50 | Fixed Cart | $50 |
| FREESHIP | Free Shipping | - |

## Documentation

### Testing Documentation

**Location:** `docs/testing/`

- **`qa-procedures.md`** - Quality assurance procedures and workflows
- **`bug-report-template.md`** - Standardized bug reporting template
- **`performance-benchmarks.md`** - Performance targets and metrics

### Additional Documentation

- **`tests/README.md`** - Detailed testing suite documentation
- **`scripts/README.md`** - Script usage and configuration guide

## Coverage Reports

Reports are generated in `tests/coverage/`:

```
tests/coverage/
├── php/                    # PHP code coverage (HTML)
├── js/                     # JavaScript coverage (HTML)
├── e2e-report/            # Playwright test results
├── performance/           # Lighthouse reports
├── accessibility/         # Accessibility audit results
├── browsers/              # Browser compatibility tests
├── 3d/                    # 3D asset validation
└── *.txt                  # Test execution logs
```

**View coverage:**
```bash
# PHP coverage
open tests/coverage/php/index.html

# JavaScript coverage
open tests/coverage/js/index.html

# E2E report
npx playwright show-report tests/coverage/e2e-report
```

## Performance Targets

### Core Web Vitals
- **Largest Contentful Paint (LCP):** < 2.5s
- **First Input Delay (FID):** < 100ms
- **Cumulative Layout Shift (CLS):** < 0.1

### Lighthouse Scores
- **Performance:** > 90
- **Accessibility:** > 95
- **Best Practices:** > 95
- **SEO:** > 95

### Page Load Times
- **Desktop:** < 3 seconds
- **Mobile:** < 5 seconds

### 3D Performance
- **Desktop FPS:** 60 (target), 30 (minimum)
- **Mobile FPS:** 30 (target), 24 (minimum)
- **Model Load Time:** < 3 seconds

## Accessibility Standards

### WCAG 2.1 Level AA Compliance

- ✓ Color contrast 4.5:1 (text) or 3:1 (large text)
- ✓ Keyboard navigation for all functionality
- ✓ Screen reader compatibility
- ✓ Semantic HTML structure
- ✓ ARIA landmarks and labels
- ✓ Form labels and error messages
- ✓ Focus indicators visible
- ✓ Text resizable to 200%

## Browser Support

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest 2 | ✓ Supported |
| Firefox | Latest 2 | ✓ Supported |
| Safari | Latest 2 | ✓ Supported |
| Edge | Latest 2 | ✓ Supported |
| Mobile Safari | iOS 13+ | ✓ Supported |
| Chrome Mobile | Latest 2 | ✓ Supported |

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: chmod +x scripts/*.sh
      - run: ./scripts/run-all-tests.sh
```

### Pre-commit Hooks

```bash
# Install husky
npm install --save-dev husky

# Add pre-commit hook
npx husky add .husky/pre-commit "npm run test:js && ./scripts/validate-theme.sh"
```

## Continuous Testing Strategy

### Daily
- Run smoke tests
- Check critical paths
- Monitor error logs

### Weekly
- Full regression suite
- Performance benchmarking
- Accessibility audit

### Pre-Release
- Complete test suite
- Manual testing checklist
- Cross-browser validation
- Performance verification
- Security scan

### Post-Release
- Smoke tests in production
- Monitor real user metrics
- Performance monitoring

## Troubleshooting

### Common Issues

**Tests Won't Run**
```bash
# Install dependencies
npm install
composer install

# Make scripts executable
chmod +x scripts/*.sh
```

**Site Not Accessible**
```bash
# Check if server is running
curl http://localhost:8080

# Start WordPress server
php -S localhost:8080 -t /path/to/wordpress
```

**Playwright Browsers Missing**
```bash
npx playwright install
```

**Coverage Not Generated**
```bash
# PHP coverage requires Xdebug
pecl install xdebug

# JavaScript coverage
npm run test:js:coverage
```

## Best Practices

1. **Run tests before committing**
   - Always run relevant tests before pushing changes
   - Use pre-commit hooks

2. **Write tests for new features**
   - Every new feature should have tests
   - Maintain >80% code coverage

3. **Keep tests isolated**
   - Tests should not depend on each other
   - Clean up data after tests

4. **Use descriptive names**
   - Test names should describe what they test
   - Use clear, specific descriptions

5. **Test edge cases**
   - Don't just test the happy path
   - Test error conditions and edge cases

6. **Monitor coverage**
   - Review coverage reports regularly
   - Identify untested code

7. **Update tests with code**
   - Keep tests synchronized with code
   - Update tests when requirements change

8. **Document test requirements**
   - Clearly document test setup
   - List test dependencies

## Support and Resources

### Documentation
- [WordPress Theme Unit Test](https://codex.wordpress.org/Theme_Unit_Test)
- [WooCommerce Testing Guide](https://github.com/woocommerce/woocommerce/wiki/Testing)
- [Jest Documentation](https://jestjs.io/)
- [Playwright Documentation](https://playwright.dev/)
- [Three.js Documentation](https://threejs.org/docs/)

### Tools
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE Browser Extension](https://wave.webaim.org/extension/)
- [WebPageTest](https://www.webpagetest.org/)

### Getting Help
1. Check test output and error messages
2. Review coverage reports
3. Consult relevant documentation
4. Check troubleshooting section
5. Review related issues

## Maintenance

### Keep Dependencies Updated
```bash
# Update npm packages
npm update

# Update composer packages
composer update

# Check for outdated packages
npm outdated
composer outdated
```

### Archive Old Reports
```bash
# Archive reports older than 30 days
find tests/coverage -type f -mtime +30 -name "*.txt" -delete
```

### Review and Update Tests
- Monthly: Review test coverage
- Quarterly: Update test procedures
- Annually: Major test suite review

---

## Summary

The SkyyRose Flagship Theme includes a comprehensive testing suite that ensures:

✓ **Functional Quality** - All features work as expected
✓ **Performance** - Pages load quickly, 3D scenes render smoothly
✓ **Accessibility** - WCAG 2.1 AA compliant for all users
✓ **Compatibility** - Works across all major browsers and devices
✓ **Security** - Protected against common vulnerabilities
✓ **Maintainability** - Well-tested, documented code

**Total Test Coverage:**
- 100+ manual test cases
- 50+ automated unit tests
- 30+ integration tests
- 20+ end-to-end tests
- 5 validation scripts
- Continuous monitoring

**Quick Commands:**
```bash
# Run everything
./scripts/run-all-tests.sh http://localhost:8080

# Just code tests
npm test

# Just validation
./scripts/validate-theme.sh

# View coverage
open tests/coverage/php/index.html
open tests/coverage/js/index.html
```

---

**Version:** 1.0.0
**Last Updated:** 2026-02-08
**Maintained By:** SkyyRose Development Team
