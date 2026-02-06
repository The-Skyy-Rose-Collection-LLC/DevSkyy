---
name: verify
description: Verify WordPress site health, performance, and security
argument-hint: "[--deep] [--fix-issues]"
allowed-tools: [Read, Bash, WebFetch, mcp__plugin_playwright_playwright__browser_snapshot]
---

# Verify WordPress Site Health

Comprehensive verification of skyyrose.co health, performance, and security status.

## Usage

```bash
/wordpress-copilot:verify
/wordpress-copilot:verify --deep
/wordpress-copilot:verify --fix-issues
```

## Verification Checks

### 1. Site Availability

```bash
# Check site is up
curl -I https://skyyrose.co

# Expected: 200 OK
# Check response time
curl -w "%{time_total}\n" -o /dev/null -s https://skyyrose.co
```

### 2. WordPress Health

```bash
# Check WordPress version
curl -s https://skyyrose.co/wp-json/ | jq '.namespaces'

# Check REST API
curl -s https://skyyrose.co/wp-json/wp/v2/posts?per_page=1

# Expected: Valid JSON response
```

### 3. Theme Verification

Check active theme and files:

```bash
# Verify theme is active
curl -s "https://skyyrose.co/wp-json/wp/v2/themes" | jq '.[] | select(.status == "active")'

# Expected: skyyrose-2025

# Check critical files
urls=(
  "https://skyyrose.co/wp-content/themes/skyyrose-2025/style.css"
  "https://skyyrose.co/wp-content/themes/skyyrose-2025/screenshot.png"
)

for url in "${urls[@]}"; do
  curl -I "$url" | grep "200 OK" || echo "ERROR: $url not found"
done
```

### 4. Security Headers

```bash
# Check all security headers
curl -I https://skyyrose.co | grep -E "(Content-Security-Policy|X-Frame-Options|X-Content-Type-Options|Referrer-Policy|Permissions-Policy)"

# Verify CSP contains required directives
curl -I https://skyyrose.co | grep "content-security-policy" | grep -q "'unsafe-inline'" && echo "✅ CSP allows unsafe-inline" || echo "❌ CSP blocks inline"
```

**Expected headers:**
- `Content-Security-Policy`: Should include 'unsafe-inline', stats.wp.com, cdn.babylonjs.com
- `X-Frame-Options`: SAMEORIGIN
- `X-Content-Type-Options`: nosniff
- `Referrer-Policy`: strict-origin-when-cross-origin

### 5. Console Errors Check

Use Playwright to capture browser console:

```javascript
const { chromium } = require('playwright');

async function checkConsoleErrors() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const errors = [];
  const warnings = [];

  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
    if (msg.type() === 'warning') warnings.push(msg.text());
  });

  await page.goto('https://skyyrose.co/?nocache=1', { waitUntil: 'networkidle' });
  await page.waitForTimeout(5000);

  console.log(`Errors: ${errors.length}`);
  console.log(`Warnings: ${warnings.length}`);

  if (errors.length > 10) {
    console.log('\n⚠️  Excessive errors detected:');
    errors.slice(0, 5).forEach(e => console.log(`  - ${e}`));
  }

  await browser.close();
  return { errors: errors.length, warnings: warnings.length };
}
```

### 6. Performance Metrics

```bash
# Run Lighthouse audit
npx lighthouse https://skyyrose.co \
  --only-categories=performance \
  --output=json \
  --output-path=./lighthouse-report.json

# Extract Core Web Vitals
cat lighthouse-report.json | jq '{
  LCP: .audits."largest-contentful-paint".numericValue,
  FID: .audits."max-potential-fid".numericValue,
  CLS: .audits."cumulative-layout-shift".numericValue,
  Score: .categories.performance.score
}'
```

**Targets:**
- LCP: < 2.5s
- FID: < 100ms
- CLS: < 0.1
- Performance Score: > 90

### 7. WooCommerce Status

```bash
# Check WooCommerce API
curl -u "consumer_key:consumer_secret" \
  "https://skyyrose.co/wp-json/wc/v3/system_status"

# Verify product endpoints
curl -u "consumer_key:consumer_secret" \
  "https://skyyrose.co/wp-json/wc/v3/products?per_page=1"
```

### 8. Elementor Health

```bash
# Check Elementor assets load
curl -I "https://skyyrose.co/wp-content/plugins/elementor/assets/css/frontend.min.css"

# Expected: 200 OK
```

### 9. 3D Asset CDN Verification

```bash
# Verify all 3D library CDNs accessible
cdns=(
  "https://cdn.babylonjs.com/babylon.js"
  "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"
  "https://unpkg.com/@react-three/fiber@latest/dist/index.js"
)

for cdn in "${cdns[@]}"; do
  curl -I "$cdn" 2>&1 | grep "200 OK" && echo "✅ $cdn accessible" || echo "❌ $cdn failed"
done
```

### 10. Database Health (if credentials available)

```bash
# Check table status
wp db check --user=admin

# Optimize tables
wp db optimize --user=admin

# Check for corrupt tables
wp db query "CHECK TABLE wp_posts, wp_postmeta, wp_options"
```

## Verification Report Format

```
🔍 WordPress Verification Report
Site: https://skyyrose.co
Date: 2026-02-06
Duration: 45s

═══════════════════════════════════════

✅ Site Availability (200 OK, 892ms)
✅ WordPress Health (6.4.2, REST API active)
✅ Theme Active (skyyrose-2025)
⚠️  Security Headers (CSP missing X-Frame-Options)
✅ Console Errors (8/10 threshold)
✅ Performance (LCP: 2.1s, FID: 85ms, CLS: 0.09)
✅ WooCommerce (3.8.1, 47 products)
✅ Elementor (3.18.2, 12 widgets)
✅ 3D CDNs (All accessible)
⚠️  Database (2 tables need optimization)

═══════════════════════════════════════

Overall Health: 90% (Excellent)

Issues Found:
1. Missing X-Frame-Options header (MEDIUM)
2. wp_postmeta table fragmented (LOW)

Recommendations:
- Add X-Frame-Options: SAMEORIGIN to security-hardening.php
- Run: wp db optimize
```

## Deep Verification (--deep flag)

Additional checks:

1. **Full site crawl**: Check all pages for errors
2. **Broken link detection**: Find 404s
3. **Image optimization**: Check unoptimized images
4. **SEO audit**: Missing meta tags, broken schema
5. **Accessibility**: WCAG 2.1 compliance
6. **Mobile responsiveness**: Test on various viewports

## Auto-Fix (--fix-issues flag)

Automatically fix common issues:

```bash
# Fix database
wp db optimize

# Regenerate thumbnails
wp media regenerate --yes

# Clear all caches
wp cache flush
wp transient delete --all

# Update permalinks
wp rewrite flush
```

## Integration with Other Commands

```bash
# Verify after deployment
/wordpress-copilot:deploy --verify

# Verify before rollback
/wordpress-copilot:verify --deep
# If health < 50%, proceed with rollback

# Continuous monitoring
# Run verify every hour via cron
```

## Exit Codes

- `0`: All checks passed
- `1`: Minor issues found (warnings)
- `2`: Critical issues found (errors)
- `3`: Site unreachable

## Output Options

```bash
# JSON output for automation
/wordpress-copilot:verify --format=json

# Save report
/wordpress-copilot:verify --output=report.txt

# Quiet mode (errors only)
/wordpress-copilot:verify --quiet
```

## Examples

### Quick health check
```bash
/wordpress-copilot:verify
```

### Full deep scan with auto-fix
```bash
/wordpress-copilot:verify --deep --fix-issues
```

### Pre-deployment verification
```bash
/wordpress-copilot:verify --deep
# If health > 80%, proceed with deployment
```
