# QA Testing Procedures

## Overview

This document outlines the quality assurance procedures for the SkyyRose Flagship Theme. Follow these procedures to ensure consistent, thorough testing.

## Table of Contents

1. [Pre-Release Testing](#pre-release-testing)
2. [Smoke Testing](#smoke-testing)
3. [Regression Testing](#regression-testing)
4. [Performance Testing](#performance-testing)
5. [Accessibility Testing](#accessibility-testing)
6. [Security Testing](#security-testing)
7. [Test Reporting](#test-reporting)

---

## Pre-Release Testing

### Timeline

Execute 1-2 weeks before release.

### Checklist

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Manual testing checklist completed
- [ ] Performance benchmarks met
- [ ] Accessibility audit passed
- [ ] Security scan completed
- [ ] Browser compatibility verified
- [ ] Mobile responsiveness tested
- [ ] 3D assets validated

### Steps

1. **Set up test environment**
   ```bash
   # Clone production database
   wp db export prod-backup.sql
   wp db import prod-backup.sql --url=staging.example.com

   # Install theme
   wp theme activate skyyrose-flagship
   ```

2. **Run automated tests**
   ```bash
   # PHP tests
   composer test

   # JavaScript tests
   npm test

   # E2E tests
   npm run test:e2e

   # Validation scripts
   ./scripts/validate-theme.sh
   ./scripts/test-performance.sh http://staging.example.com
   ./scripts/check-accessibility.sh http://staging.example.com
   ./scripts/test-browsers.sh http://staging.example.com
   ./scripts/validate-3d.sh
   ```

3. **Execute manual testing checklist**
   - Open `tests/checklist.md`
   - Test all items systematically
   - Document any issues in bug tracker

4. **Review test results**
   - Check all coverage reports
   - Ensure >80% code coverage
   - No critical bugs remaining
   - All P0/P1 bugs resolved

5. **Sign-off**
   - QA lead approval
   - Product owner approval
   - Technical lead approval

---

## Smoke Testing

### Purpose

Quick validation that critical functionality works after deployment.

### Duration

30-60 minutes

### Critical Paths

1. **Homepage**
   - [ ] Page loads without errors
   - [ ] Navigation menu works
   - [ ] 3D hero scene renders
   - [ ] Featured products display

2. **Product Browsing**
   - [ ] Shop page loads
   - [ ] Products display correctly
   - [ ] Filters work
   - [ ] Search works

3. **Product Page**
   - [ ] Product details display
   - [ ] Images load
   - [ ] 3D model renders (if applicable)
   - [ ] Add to cart works

4. **Checkout Flow**
   - [ ] Add product to cart
   - [ ] Cart page displays
   - [ ] Proceed to checkout
   - [ ] Fill billing details
   - [ ] Complete test order

5. **Admin**
   - [ ] Login to admin
   - [ ] Access theme customizer
   - [ ] Create test product
   - [ ] View orders

### Smoke Test Script

```bash
#!/bin/bash
# Quick smoke test

echo "Running smoke tests..."

# Test homepage
curl -f http://example.com || exit 1

# Test shop page
curl -f http://example.com/shop/ || exit 1

# Test cart
curl -f http://example.com/cart/ || exit 1

# Test checkout
curl -f http://example.com/checkout/ || exit 1

echo "Smoke tests passed!"
```

---

## Regression Testing

### Purpose

Ensure new changes haven't broken existing functionality.

### Frequency

- After every major feature addition
- Before each release
- After bug fixes

### Regression Test Suite

1. **Core Functionality**
   - Run all unit tests
   - Run all integration tests
   - Execute critical user flows

2. **Previously Fixed Bugs**
   - Test all resolved bugs
   - Verify fixes remain intact
   - Check for edge cases

3. **High-Risk Areas**
   - Payment processing
   - Cart calculations
   - User authentication
   - 3D scene rendering
   - Database queries

### Regression Test Execution

```bash
# Run full regression suite
npm run test:all

# Check previous bug fixes
./scripts/test-regressions.sh
```

### Regression Test Matrix

| Feature | Test Case | Status | Last Tested |
|---------|-----------|--------|-------------|
| Add to Cart | Simple product | ☐ | YYYY-MM-DD |
| Add to Cart | Variable product | ☐ | YYYY-MM-DD |
| Checkout | Guest checkout | ☐ | YYYY-MM-DD |
| Checkout | Logged-in checkout | ☐ | YYYY-MM-DD |
| 3D Viewer | Model loading | ☐ | YYYY-MM-DD |
| 3D Viewer | Camera controls | ☐ | YYYY-MM-DD |

---

## Performance Testing

### Metrics

- **Page Load Time:** < 3s (desktop), < 5s (mobile)
- **Lighthouse Score:** > 90
- **First Contentful Paint:** < 1.8s
- **Time to Interactive:** < 3.8s
- **3D Model Load:** < 3s
- **API Response Time:** < 500ms

### Testing Tools

1. **Google Lighthouse**
   ```bash
   lighthouse https://example.com --output=html --output-path=./report.html
   ```

2. **WebPageTest**
   - Visit https://www.webpagetest.org/
   - Test from multiple locations
   - Test on 3G and 4G connections

3. **Performance Script**
   ```bash
   ./scripts/test-performance.sh https://example.com
   ```

### Performance Test Procedure

1. **Baseline Measurement**
   - Measure current performance
   - Document metrics
   - Identify bottlenecks

2. **Optimization**
   - Optimize images
   - Minify assets
   - Enable caching
   - Compress 3D models

3. **Verification**
   - Re-measure performance
   - Compare to baseline
   - Verify improvements

4. **Load Testing**
   - Simulate concurrent users
   - Test under high load
   - Identify breaking points

### Load Test Script

```bash
# Using Apache Bench
ab -n 1000 -c 10 https://example.com/

# Using Artillery
artillery quick --count 10 --num 100 https://example.com/
```

---

## Accessibility Testing

### WCAG 2.1 Level AA Compliance

### Automated Testing

```bash
# Run accessibility tests
./scripts/check-accessibility.sh https://example.com

# axe-core
npx axe https://example.com

# pa11y
npx pa11y https://example.com
```

### Manual Testing

1. **Keyboard Navigation**
   - [ ] Tab through all interactive elements
   - [ ] Focus indicators visible
   - [ ] No keyboard traps
   - [ ] Skip navigation works

2. **Screen Reader Testing**
   - Test with NVDA (Windows)
   - Test with JAWS (Windows)
   - Test with VoiceOver (Mac/iOS)
   - Test with TalkBack (Android)

3. **Color Contrast**
   - Use WebAIM Contrast Checker
   - Verify 4.5:1 ratio for text
   - Verify 3:1 ratio for large text
   - Check focus indicators

4. **Zoom Testing**
   - Test at 200% zoom
   - Verify no content cutoff
   - Check layout integrity

### Accessibility Checklist

- [ ] All images have alt text
- [ ] Forms have proper labels
- [ ] Headings are hierarchical
- [ ] Color not sole indicator
- [ ] Videos have captions
- [ ] ARIA landmarks present
- [ ] Error messages clear
- [ ] Skip navigation available

---

## Security Testing

### Security Checklist

1. **Input Validation**
   - [ ] All user inputs sanitized
   - [ ] SQL injection prevention
   - [ ] XSS prevention
   - [ ] CSRF tokens present

2. **Authentication & Authorization**
   - [ ] Strong password requirements
   - [ ] Session management secure
   - [ ] User roles enforced
   - [ ] Admin access protected

3. **Data Protection**
   - [ ] HTTPS enforced
   - [ ] Sensitive data encrypted
   - [ ] No data leakage
   - [ ] Secure cookies

4. **WordPress Security**
   - [ ] File permissions correct
   - [ ] wp-config.php protected
   - [ ] Database prefix changed
   - [ ] Directory browsing disabled

### Security Testing Tools

```bash
# WPScan
wpscan --url https://example.com

# Security headers
curl -I https://example.com | grep -E "X-|Strict-Transport-Security"

# SSL test
openssl s_client -connect example.com:443
```

### Penetration Testing

1. **Manual Penetration Testing**
   - Attempt SQL injection
   - Test XSS vulnerabilities
   - Check for CSRF issues
   - Test authentication bypass

2. **Automated Scanning**
   - Run OWASP ZAP
   - Run Nikto scan
   - Check for known vulnerabilities

3. **Code Review**
   - Review for security issues
   - Check data sanitization
   - Verify nonce usage
   - Check capability checks

---

## Test Reporting

### Daily Test Report

**Date:** YYYY-MM-DD
**Tester:** Name

#### Tests Executed
- Unit Tests: X passed, Y failed
- Integration Tests: X passed, Y failed
- E2E Tests: X passed, Y failed

#### Bugs Found
- Critical: X
- High: Y
- Medium: Z
- Low: W

#### Blockers
- List any blockers

#### Next Steps
- Planned testing for tomorrow

### Weekly Test Summary

**Week of:** YYYY-MM-DD

#### Test Coverage
- PHP Code Coverage: XX%
- JavaScript Coverage: XX%
- E2E Coverage: XX%

#### Bug Metrics
- Bugs opened: XX
- Bugs closed: XX
- Bugs remaining: XX

#### Quality Metrics
- Pass rate: XX%
- Flaky tests: XX
- Average fix time: XX hours

#### Performance Benchmarks
- Lighthouse score: XX
- Page load time: XX seconds
- 3D load time: XX seconds

### Pre-Release Report

**Version:** X.X.X
**Release Date:** YYYY-MM-DD

#### Test Summary
- Total tests: XXX
- Tests passed: XXX
- Tests failed: XXX
- Pass rate: XX%

#### Bug Summary
- Critical bugs: 0
- High priority: 0
- Medium priority: X
- Low priority: Y

#### Performance Metrics
- All performance targets met: ☐ Yes ☐ No
- Lighthouse score: XX/100
- Load time: XX seconds

#### Accessibility
- WCAG 2.1 AA compliant: ☐ Yes ☐ No
- axe-core violations: 0

#### Browser Compatibility
- Chrome: ☐ Pass
- Firefox: ☐ Pass
- Safari: ☐ Pass
- Edge: ☐ Pass

#### Recommendations
- List any recommendations

#### Sign-Off
- QA Lead: _______________
- Product Owner: _______________
- Technical Lead: _______________

---

## Best Practices

1. **Test Early, Test Often**
   - Don't wait until end of sprint
   - Test during development
   - Continuous integration

2. **Automate Where Possible**
   - Write unit tests for new code
   - Add E2E tests for user flows
   - Use CI/CD for automated testing

3. **Document Everything**
   - Log all bugs
   - Document test results
   - Keep test cases updated

4. **Communicate Issues**
   - Report bugs immediately
   - Provide clear reproduction steps
   - Include screenshots/videos

5. **Maintain Test Data**
   - Keep test data fresh
   - Use realistic test scenarios
   - Clean up after testing

6. **Respect Test Environments**
   - Don't test in production
   - Use dedicated test environments
   - Restore backups after destructive tests

7. **Continuous Improvement**
   - Review failed tests
   - Update test procedures
   - Learn from bugs

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
