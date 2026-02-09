# SkyyRose Flagship Theme - Testing Suite

Complete testing and validation suite for the SkyyRose flagship WordPress/WooCommerce theme with 3D capabilities.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

This testing suite includes:

1. **Manual Testing Checklist** - Comprehensive checklist for manual QA
2. **PHP Unit Tests** - Tests for theme functions and WooCommerce integration
3. **JavaScript Tests** - Tests for 3D scene rendering and interactions
4. **E2E Tests** - End-to-end tests for complete user flows
5. **Validation Scripts** - Automated scripts for theme, performance, accessibility, and 3D validation

## Setup

### Prerequisites

```bash
# Node.js and npm
node --version  # v18+ recommended
npm --version

# PHP and Composer
php --version  # 7.4+ required
composer --version

# WordPress Test Library
bash bin/install-wp-tests.sh wordpress_test root '' localhost latest
```

### Install Dependencies

```bash
# Install npm packages
npm install

# Install Composer packages
composer install

# Install Playwright browsers
npx playwright install
```

### Environment Configuration

Create a `.env` file in the theme root:

```env
WP_TESTS_DIR=/tmp/wordpress-tests-lib
WP_CORE_DIR=/tmp/wordpress
BASE_URL=http://localhost:8080
DB_NAME=wordpress_test
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
```

## Running Tests

### All Tests

```bash
# Run complete test suite
npm test

# Or with coverage
npm run test:coverage
```

### Manual Testing

```bash
# Open the manual testing checklist
open tests/checklist.md
```

### PHP Unit Tests

```bash
# Run PHPUnit tests
composer test

# Run with coverage
composer test:coverage

# Run specific test file
./vendor/bin/phpunit tests/unit/test-theme-setup.php
```

### JavaScript Tests

```bash
# Run Jest tests
npm run test:js

# Run in watch mode
npm run test:js:watch

# Run with coverage
npm run test:js:coverage
```

### E2E Tests

```bash
# Run Playwright tests
npm run test:e2e

# Run in UI mode
npm run test:e2e:ui

# Run specific browser
npm run test:e2e -- --project=chromium

# Debug mode
npm run test:e2e:debug
```

### Validation Scripts

```bash
# Make scripts executable (first time only)
chmod +x scripts/*.sh

# Validate WordPress theme requirements
./scripts/validate-theme.sh

# Test performance
./scripts/test-performance.sh http://localhost:8080

# Check accessibility
./scripts/check-accessibility.sh http://localhost:8080

# Test browser compatibility
./scripts/test-browsers.sh http://localhost:8080

# Validate 3D assets
./scripts/validate-3d.sh
```

## Test Types

### 1. Manual Testing (`tests/checklist.md`)

Comprehensive manual testing checklist covering:

- 3D experience functionality
- WooCommerce flows (browse, cart, checkout)
- Responsive design across all breakpoints
- Browser compatibility (Chrome, Firefox, Safari, Edge)
- Accessibility (WCAG 2.1 AA compliance)
- SEO validation
- Performance metrics
- Security checks

**How to use:**
1. Print or open the checklist
2. Test each item systematically
3. Mark items as Pass/Fail/Warn
4. Document any issues found
5. Sign off when complete

### 2. PHP Unit Tests (`tests/unit/`)

Tests for WordPress theme functionality:

- Theme setup and configuration
- Template functions
- WooCommerce integration
- Widget areas
- Navigation menus
- Custom post types
- Security features

**Example:**
```php
public function test_theme_supports() {
    $this->assertTrue( current_theme_supports( 'woocommerce' ) );
}
```

### 3. JavaScript Tests (`tests/unit/*.test.js`)

Tests for JavaScript functionality:

- Three.js scene initialization
- 3D model loading
- Camera controls
- Animation loops
- Error handling
- Memory management

**Example:**
```javascript
test('should create a scene', () => {
    const scene = new THREE.Scene();
    expect(scene).toBeDefined();
});
```

### 4. Integration Tests (`tests/integration/`)

Tests for component integration:

- WooCommerce cart operations
- Product variations
- Payment processing
- Order management
- User authentication

**Example:**
```php
public function test_add_to_cart() {
    $product = WC_Helper_Product::create_simple_product();
    WC()->cart->add_to_cart( $product->get_id(), 1 );
    $this->assertEquals( 1, WC()->cart->get_cart_contents_count() );
}
```

### 5. E2E Tests (`tests/e2e/specs/`)

End-to-end user flow tests:

- Complete checkout process
- Product browsing and filtering
- Cart management
- User account operations
- Mobile responsive flows

**Example:**
```javascript
test('should complete checkout as guest', async ({ page }) => {
    await page.goto('/shop/');
    await page.click('.product:first-child .add_to_cart_button');
    // ... complete checkout flow
    await expect(page.locator('.woocommerce-thankyou')).toBeVisible();
});
```

### 6. Validation Scripts (`scripts/`)

Automated validation scripts:

#### `validate-theme.sh`
- Checks required WordPress theme files
- Validates style.css header
- Checks for security best practices
- Validates code structure

#### `test-performance.sh`
- Runs Lighthouse performance tests
- Measures page load times
- Checks asset sizes
- Provides optimization recommendations

#### `check-accessibility.sh`
- Runs axe-core accessibility tests
- Runs pa11y WCAG compliance tests
- Checks ARIA landmarks
- Validates semantic HTML

#### `test-browsers.sh`
- Tests across multiple browsers (Chrome, Firefox, Safari, Edge)
- Checks feature compatibility
- Takes screenshots
- Validates responsive design

#### `validate-3d.sh`
- Validates 3D model files (GLB/GLTF)
- Checks texture files
- Verifies Three.js integration
- Provides optimization recommendations

## Test Data

### Sample Products (`tests/fixtures/sample-products.json`)

Pre-configured test data including:
- 5 sample products (simple and variable)
- Test user accounts
- Discount coupons
- Product collections

**Import test data:**
```bash
# Using WP-CLI
wp import tests/fixtures/sample-products.json --authors=create

# Or use the WooCommerce importer in admin
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

## CI/CD Integration

### GitHub Actions

Example workflow (`.github/workflows/test.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test
      - run: npx playwright install
      - run: npm run test:e2e
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
npm run test:js
./scripts/validate-theme.sh
```

## Coverage Reports

Coverage reports are generated in `tests/coverage/`:

- `tests/coverage/php/` - PHP code coverage (HTML)
- `tests/coverage/js/` - JavaScript code coverage (HTML)
- `tests/coverage/e2e-report/` - Playwright test report
- `tests/coverage/performance/` - Lighthouse performance reports
- `tests/coverage/accessibility/` - Accessibility audit reports
- `tests/coverage/browsers/` - Browser compatibility reports
- `tests/coverage/3d/` - 3D asset validation reports

**View coverage:**
```bash
# PHP coverage
open tests/coverage/php/index.html

# JavaScript coverage
open tests/coverage/js/index.html

# E2E report
npx playwright show-report tests/coverage/e2e-report
```

## Troubleshooting

### Common Issues

#### WordPress Test Library Not Found

```bash
# Reinstall WordPress test library
bash bin/install-wp-tests.sh wordpress_test root '' localhost latest
```

#### Playwright Browsers Missing

```bash
# Install Playwright browsers
npx playwright install
```

#### Three.js Tests Failing

Check that Three.js mocks are properly set up in `tests/jest.setup.js`.

#### E2E Tests Timeout

Increase timeout in `tests/e2e/playwright.config.js`:

```javascript
use: {
    timeout: 60000, // Increase timeout
}
```

#### Permission Denied on Scripts

```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Debug Mode

#### PHP Tests
```bash
# Run with verbose output
./vendor/bin/phpunit --verbose
```

#### JavaScript Tests
```bash
# Run with debugging
node --inspect-brk node_modules/.bin/jest --runInBand
```

#### E2E Tests
```bash
# Run with headed browser
npm run test:e2e -- --headed

# Run with debugger
npm run test:e2e:debug
```

## Best Practices

1. **Run tests before committing** - Always run the test suite before pushing changes
2. **Write tests for new features** - Every new feature should have corresponding tests
3. **Keep tests isolated** - Tests should not depend on each other
4. **Use descriptive names** - Test names should clearly describe what they test
5. **Mock external dependencies** - Don't rely on external APIs or services
6. **Clean up after tests** - Always clean up created data in tearDown/afterEach
7. **Test edge cases** - Don't just test the happy path
8. **Monitor coverage** - Aim for >80% code coverage
9. **Update tests with code** - Keep tests in sync with code changes
10. **Document test requirements** - Clearly document what each test needs

## Performance Targets

- **Lighthouse Performance Score:** > 90
- **Page Load Time:** < 3 seconds (desktop), < 5 seconds (mobile)
- **First Contentful Paint:** < 1.8 seconds
- **Time to Interactive:** < 3.8 seconds
- **3D Model Load:** < 3 seconds
- **Cart/Checkout Load:** < 2 seconds

## Accessibility Targets

- **WCAG 2.1 Level:** AA compliance
- **Color Contrast:** 4.5:1 minimum
- **Keyboard Navigation:** 100% keyboard accessible
- **Screen Reader:** Compatible with NVDA, JAWS, VoiceOver
- **axe-core Score:** 0 violations

## Browser Support

- **Chrome:** Latest 2 versions
- **Firefox:** Latest 2 versions
- **Safari:** Latest 2 versions
- **Edge:** Latest 2 versions
- **Mobile Safari:** iOS 13+
- **Chrome Mobile:** Latest 2 versions

## Resources

- [WordPress Theme Unit Test Data](https://codex.wordpress.org/Theme_Unit_Test)
- [WooCommerce Testing](https://github.com/woocommerce/woocommerce/wiki/Testing)
- [Jest Documentation](https://jestjs.io/)
- [Playwright Documentation](https://playwright.dev/)
- [PHPUnit Documentation](https://phpunit.de/)
- [Lighthouse Documentation](https://developers.google.com/web/tools/lighthouse)
- [axe-core Documentation](https://www.deque.com/axe/)
- [Three.js Documentation](https://threejs.org/docs/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test output and error messages
3. Check coverage reports for untested code
4. Consult the relevant documentation

---

**Last Updated:** 2026-02-08
**Version:** 1.0.0
