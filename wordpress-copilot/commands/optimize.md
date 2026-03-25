---
name: optimize
description: Run performance or security optimization audit and apply fixes
argument-hint: "[--type=performance|security|accessibility] [--apply-fixes]"
allowed-tools: [Read, Write, Edit, Bash, Grep]
---

# Optimize WordPress Site

Audit and optimize skyyrose.co for performance, security, or accessibility.

## Usage

```bash
/wordpress-copilot:optimize --type=performance
/wordpress-copilot:optimize --type=security --apply-fixes
/wordpress-copilot:optimize --type=accessibility
```

## Optimization Types

### 1. Performance Optimization

**Audits:**
- Core Web Vitals (LCP, FID, CLS)
- Image optimization
- Code splitting
- Bundle size
- Lazy loading
- Caching strategy

**Actions:**
```bash
# Run Lighthouse
npx lighthouse https://skyyrose.co \
  --only-categories=performance \
  --output=html \
  --output-path=./performance-report.html

# Check image sizes
find wordpress-theme/skyyrose-2025 -name "*.jpg" -o -name "*.png" | xargs du -h | sort -h

# Analyze bundle
npx webpack-bundle-analyzer
```

**Fixes Applied:**
- Convert images to WebP/AVIF
- Add lazy loading to images
- Defer non-critical CSS
- Minify JS/CSS
- Enable browser caching

### 2. Security Optimization

**Audits:**
- CSP headers
- XSS vulnerabilities
- SQL injection risks
- CSRF protection
- Authentication security
- Rate limiting

**Actions:**
```bash
# Check security headers
curl -I https://skyyrose.co | grep -i "security\|csp\|xss"

# Scan for vulnerabilities
npm audit
```

**Fixes Applied:**
- Update CSP directives
- Add input sanitization
- Implement rate limiting
- Update vulnerable dependencies
- Add CSRF tokens

### 3. Accessibility Optimization

**Audits:**
- WCAG 2.1 Level AA compliance
- ARIA labels
- Keyboard navigation
- Color contrast
- Screen reader compatibility

**Actions:**
```bash
# Run axe accessibility audit
npx @axe-core/cli https://skyyrose.co

# Check color contrast
npx pa11y https://skyyrose.co
```

**Fixes Applied:**
- Add ARIA labels
- Improve keyboard navigation
- Fix color contrast issues
- Add alt text to images
- Improve focus indicators

## Reports

Generated reports saved to:
```
reports/
├── performance-YYYY-MM-DD.html
├── security-YYYY-MM-DD.json
└── accessibility-YYYY-MM-DD.json
```

## Flags

**--type**: Optimization type (performance|security|accessibility)
**--apply-fixes**: Automatically apply recommended fixes
**--report-only**: Generate report without applying fixes

## Example Output

```
🎯 Performance Optimization Complete

Audited: https://skyyrose.co
Date: 2026-02-06

Metrics:
✅ LCP: 2.1s (target: < 2.5s)
⚠️  FID: 120ms (target: < 100ms)
✅ CLS: 0.08 (target: < 0.1)

Improvements Applied:
- Converted 15 images to WebP (-45% size)
- Added lazy loading to below-fold images
- Deferred non-critical CSS
- Enabled browser caching

Performance Score: 92/100 (was 78/100)
```
