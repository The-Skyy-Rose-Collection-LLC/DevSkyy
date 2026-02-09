# Testing & Validation Scripts

This directory contains automated scripts for testing and validating the SkyyRose Flagship Theme.

## Quick Start

```bash
# Make all scripts executable (first time only)
chmod +x scripts/*.sh

# Run all tests
./scripts/run-all-tests.sh http://localhost:8080

# Or run individual scripts
./scripts/validate-theme.sh
./scripts/test-performance.sh http://localhost:8080
./scripts/check-accessibility.sh http://localhost:8080
./scripts/test-browsers.sh http://localhost:8080
./scripts/validate-3d.sh
```

## Available Scripts

### `run-all-tests.sh`

**Purpose:** Master test runner that executes all tests and validations.

**Usage:**
```bash
./scripts/run-all-tests.sh [SITE_URL]
```

**Example:**
```bash
./scripts/run-all-tests.sh http://localhost:8080
```

**What it does:**
1. Runs theme validation
2. Executes PHP unit tests
3. Runs JavaScript tests
4. Executes E2E tests
5. Tests performance
6. Checks accessibility
7. Tests browser compatibility
8. Validates 3D assets
9. Runs code quality checks
10. Performs basic security scan

**Output:** Comprehensive test report with all results

---

### `validate-theme.sh`

**Purpose:** Validates WordPress theme requirements and best practices.

**Usage:**
```bash
./scripts/validate-theme.sh
```

**Checks:**
- Required theme files (style.css, index.php, functions.php, etc.)
- style.css header information
- Template files structure
- Theme setup functions
- Security best practices
- WooCommerce integration
- Asset organization
- Code standards (if PHPCS installed)

**Output:** Pass/Fail report with recommendations

---

### `test-performance.sh`

**Purpose:** Tests site performance and generates optimization recommendations.

**Usage:**
```bash
./scripts/test-performance.sh [SITE_URL]
```

**Example:**
```bash
./scripts/test-performance.sh http://localhost:8080
```

**Checks:**
- Lighthouse performance scores
- Page load times
- Asset sizes (CSS, JS, Images, 3D models)
- Resource optimization
- Core Web Vitals

**Output:**
- Performance reports in `tests/coverage/performance/`
- Lighthouse HTML reports
- Asset size analysis
- Optimization recommendations

**Requirements:**
- `lighthouse` (npm install -g lighthouse)
- `curl`
- `jq` (optional, for JSON parsing)

---

### `check-accessibility.sh`

**Purpose:** Tests WCAG 2.1 AA accessibility compliance.

**Usage:**
```bash
./scripts/check-accessibility.sh [SITE_URL]
```

**Example:**
```bash
./scripts/check-accessibility.sh http://localhost:8080
```

**Checks:**
- Automated axe-core tests
- pa11y WCAG compliance tests
- Skip links presence
- ARIA landmarks
- Image alt attributes
- Form labels
- Heading hierarchy
- Color contrast
- Focus indicators
- Keyboard navigation support

**Output:**
- Accessibility reports in `tests/coverage/accessibility/`
- axe-core JSON reports
- pa11y JSON reports
- Manual testing checklist

**Requirements:**
- `axe` (npm install -g @axe-core/cli)
- `pa11y` (npm install -g pa11y)
- `curl`

---

### `test-browsers.sh`

**Purpose:** Tests browser compatibility across multiple browsers.

**Usage:**
```bash
./scripts/test-browsers.sh [SITE_URL]
```

**Example:**
```bash
./scripts/test-browsers.sh http://localhost:8080
```

**Checks:**
- Feature detection (WebGL, ES6, CSS features)
- Cross-browser compatibility
- Responsive design
- JavaScript execution
- CSS rendering

**Tests:**
- Chrome/Chromium
- Firefox
- Safari/WebKit
- Edge

**Output:**
- Browser compatibility reports
- Screenshots (mobile and desktop)
- Feature detection results
- Compatibility matrix

**Requirements:**
- `playwright` (npm install -D @playwright/test)
- `node` and `npm`

---

### `validate-3d.sh`

**Purpose:** Validates 3D assets and Three.js integration.

**Usage:**
```bash
./scripts/validate-3d.sh
```

**Checks:**
- 3D model files (GLB/GLTF)
- Model file sizes
- Texture files and sizes
- Three.js library presence
- GLTFLoader availability
- OrbitControls presence
- DRACOLoader (optional)
- Scene initialization code
- Animation loops
- Error handling
- Resize handlers
- Loading indicators

**Output:**
- 3D validation report in `tests/coverage/3d/`
- Model validation results (if gltf-validator installed)
- Performance recommendations
- Optimization checklist

**Requirements:**
- `gltf_validator` (optional, recommended)
- `node` (for JSON parsing)

---

## Installation

### Prerequisites

```bash
# Node.js and npm
node --version  # v18+ recommended
npm --version

# PHP and Composer
php --version   # 7.4+ required
composer --version
```

### Install Testing Dependencies

```bash
# Install Node.js packages
npm install

# Install Composer packages
composer install

# Install global tools (optional but recommended)
npm install -g lighthouse @axe-core/cli pa11y @playwright/test

# Install Playwright browsers
npx playwright install
```

### Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

## Configuration

Most scripts accept a site URL as an argument. Default is `http://localhost:8080`.

### Environment Variables

You can set default values using environment variables:

```bash
export BASE_URL=http://localhost:8080
export WP_TESTS_DIR=/tmp/wordpress-tests-lib
```

## Output and Reports

All scripts generate reports in the `tests/coverage/` directory:

```
tests/coverage/
├── php/                    # PHP code coverage
├── js/                     # JavaScript code coverage
├── e2e-report/            # Playwright E2E reports
├── performance/           # Lighthouse & performance reports
├── accessibility/         # Accessibility test results
├── browsers/              # Browser compatibility reports
└── 3d/                    # 3D validation reports
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

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
      - run: chmod +x scripts/*.sh
      - run: ./scripts/run-all-tests.sh
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
test:
  image: node:18
  script:
    - npm ci
    - chmod +x scripts/*.sh
    - ./scripts/run-all-tests.sh
  artifacts:
    paths:
      - tests/coverage/
```

## Troubleshooting

### Permission Denied

```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Command Not Found

```bash
# Install missing tools
npm install -g lighthouse @axe-core/cli pa11y

# Or install locally
npm install --save-dev lighthouse @axe-core/cli pa11y
```

### Site Not Accessible

Ensure your local development server is running:

```bash
# WordPress built-in server
php -S localhost:8080 -t /path/to/wordpress

# Or use Docker
docker-compose up
```

### Test Timeouts

Increase timeout in Playwright config or script parameters.

## Best Practices

1. **Run tests before committing**
   ```bash
   # Add to pre-commit hook
   ./scripts/run-all-tests.sh
   ```

2. **Test on staging before production**
   ```bash
   ./scripts/run-all-tests.sh https://staging.example.com
   ```

3. **Monitor performance regularly**
   ```bash
   # Add to cron
   0 */6 * * * /path/to/scripts/test-performance.sh
   ```

4. **Keep dependencies updated**
   ```bash
   npm update
   composer update
   ```

5. **Review reports after each run**
   - Check coverage percentages
   - Review failed tests
   - Address warnings
   - Track performance trends

## Exit Codes

All scripts follow standard exit code conventions:

- `0` - All tests passed
- `1` - Some tests failed
- `2` - Script error or missing dependencies

## Getting Help

For issues or questions:
1. Check script output for specific errors
2. Review documentation in `tests/README.md`
3. Check individual tool documentation
4. Review log files in `tests/coverage/`

## Related Documentation

- [Testing Suite Overview](../tests/README.md)
- [Manual Testing Checklist](../tests/checklist.md)
- [QA Procedures](../docs/testing/qa-procedures.md)
- [Performance Benchmarks](../docs/testing/performance-benchmarks.md)
- [Bug Report Template](../docs/testing/bug-report-template.md)

---

**Last Updated:** 2026-02-08
**Version:** 1.0.0
