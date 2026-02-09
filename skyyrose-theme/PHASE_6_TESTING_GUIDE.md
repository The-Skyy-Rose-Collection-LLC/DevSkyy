# Phase 6: Testing & Optimization - Complete Guide

## Overview
Comprehensive testing and validation suite for SkyyRose 3D Collections WordPress theme. This phase ensures production readiness across performance, accessibility, security, and cross-browser compatibility.

**Target Completion:** All 4 collections validated, production-ready deployment

---

## Testing Checklist

### 1. Lighthouse Audits ⚡

**Target Scores:**
- Performance: 90+ (desktop), 85+ (mobile)
- Accessibility: 95+
- Best Practices: 95+
- SEO: 95+

**Test All 4 Collections:**
- [ ] Signature Collection 3D (`/signature-collection-3d/`)
- [ ] Love Hurts Collection 3D (`/love-hurts-3d/`)
- [ ] Black Rose Collection 3D (`/black-rose-3d/`)
- [ ] Preorder Gateway 3D (`/preorder-gateway-3d/`)

**Test All 4 Archive Pages:**
- [ ] `/product-category/signature-collection/`
- [ ] `/product-category/love-hurts/`
- [ ] `/product-category/black-rose/`
- [ ] `/product-category/preorder/`

**Command:**
```bash
# Desktop audit
npx lighthouse https://skyyrose.local/signature-collection-3d/ \
  --only-categories=performance,accessibility,best-practices,seo \
  --output=html \
  --output-path=./tests/lighthouse/signature-desktop.html \
  --chrome-flags="--headless"

# Mobile audit
npx lighthouse https://skyyrose.local/signature-collection-3d/ \
  --only-categories=performance,accessibility,best-practices,seo \
  --output=html \
  --output-path=./tests/lighthouse/signature-mobile.html \
  --chrome-flags="--headless" \
  --preset=mobile
```

**Key Metrics to Monitor:**
- First Contentful Paint (FCP): < 1.8s
- Largest Contentful Paint (LCP): < 2.5s
- Total Blocking Time (TBT): < 200ms
- Cumulative Layout Shift (CLS): < 0.1
- Time to Interactive (TTI): < 3.5s

---

### 2. Performance Profiling 📊

**Tools:**
- Chrome DevTools Performance tab
- Stats.js overlay
- WebGL debug extension

**Metrics to Track:**
- [ ] Frame rate: Consistent 60fps
- [ ] Draw calls: < 100 per scene
- [ ] Memory usage: Stable (no leaks)
- [ ] GPU memory: < 500MB
- [ ] JavaScript heap: < 100MB

**Performance Tests:**

#### A. Frame Rate Test
```javascript
// Add Stats.js to scene
import Stats from 'three/addons/libs/stats.module.js';

const stats = new Stats();
document.body.appendChild(stats.dom);

function animate() {
  stats.begin();
  // ... render scene
  stats.end();
}
```

**Validation:**
- [ ] Signature Collection: 60fps maintained
- [ ] Love Hurts Collection: 60fps with 80 physics objects
- [ ] Black Rose Collection: 60fps with 50k particles + fog
- [ ] Preorder Gateway: 60fps with 262k particles + scroll

#### B. Draw Call Analysis
Open Chrome DevTools → More tools → Rendering → Frame Rendering Stats

**Expected Draw Calls:**
- Signature: ~50 (glass pavilion + products)
- Love Hurts: ~60 (castle + LOD + products)
- Black Rose: ~15 (instanced particles + LOD + products)
- Preorder: ~10 (instanced particles + portal + products)

#### C. Memory Leak Test
1. Load 3D scene
2. Navigate between views 10+ times
3. Monitor memory in DevTools Performance Monitor
4. Memory should stabilize, not grow infinitely

**Command:**
```bash
# Run performance test script
npm run test:performance
```

---

### 3. Mobile Testing 📱

**Devices to Test:**

**iOS:**
- [ ] iPhone 13 Pro (iOS 15+)
- [ ] iPhone SE (iOS 15+)
- [ ] iPad Pro (iOS 15+)

**Android:**
- [ ] Samsung Galaxy S21 (Android 11+)
- [ ] Google Pixel 6 (Android 12+)
- [ ] OnePlus 9 (Android 11+)

**Mobile-Specific Tests:**

#### A. Touch Controls
- [ ] OrbitControls: ONE finger rotate works
- [ ] OrbitControls: TWO finger pan/zoom works
- [ ] Product hotspots: Tap to open modal
- [ ] Navigation buttons: Tap to navigate
- [ ] Modal close: Tap outside or X button

#### B. Loading Performance
- [ ] 3D scenes load within 5 seconds on 4G
- [ ] Loading progress bar shows accurate progress
- [ ] Fallback message if WebGL unavailable

#### C. Responsive Layout
- [ ] Hero banners scale correctly
- [ ] Countdown timer stacks on small screens
- [ ] Product grids adapt to screen width
- [ ] Navigation doesn't obstruct content

**Test Script:**
```bash
# Test on iOS Simulator
open -a Simulator

# Test on Android Emulator
emulator -avd Pixel_6_API_31

# Or use BrowserStack/Sauce Labs for real devices
```

---

### 4. Cross-Browser Testing 🌐

**Browsers to Test:**

**Desktop:**
- [ ] Chrome 90+ (Windows, macOS, Linux)
- [ ] Firefox 88+ (Windows, macOS, Linux)
- [ ] Safari 14+ (macOS)
- [ ] Edge 90+ (Windows)

**Mobile:**
- [ ] Safari (iOS 14+)
- [ ] Chrome (Android)
- [ ] Samsung Internet (Android)

**Test Matrix:**

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| WebGL 2 | ✓ | ✓ | ✓ | ✓ |
| OrbitControls | ✓ | ✓ | ✓ | ✓ |
| GLSL Shaders | ✓ | ✓ | ✓ | ✓ |
| Lenis Scroll | ✓ | ✓ | ✓ | ✓ |
| Spatial Audio | ✓ | ✓ | ✓ | ✓ |
| Product Modals | ✓ | ✓ | ✓ | ✓ |

**Known Issues to Check:**
- Safari: VolumeNodeMaterial (TSL) requires Three.js r161+
- Firefox: Shadow rendering may differ slightly
- Edge: Same as Chrome (Chromium-based)

**Command:**
```bash
# Run cross-browser tests with Playwright
npm run test:browsers
```

---

### 5. Accessibility Audit ♿

**Tools:**
- axe DevTools browser extension
- WAVE browser extension
- pa11y CLI tool
- Lighthouse accessibility audit

**WCAG 2.1 AA Compliance:**

#### A. Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Enter/Space activates buttons
- [ ] Escape closes modals
- [ ] Focus indicators visible (3:1 contrast)
- [ ] No keyboard traps

**Test Sequence:**
1. Load 3D page
2. Press Tab repeatedly
3. Verify focus order: Nav → Controls → Products
4. Press Enter on product hotspot
5. Verify modal opens and focus moves to modal
6. Press Escape
7. Verify modal closes and focus returns

#### B. Screen Reader Testing
- [ ] NVDA (Windows) - Free
- [ ] JAWS (Windows) - Trial
- [ ] VoiceOver (macOS/iOS) - Built-in

**Elements to Verify:**
- [ ] Page title announced
- [ ] Landmarks (nav, main, footer) identified
- [ ] Buttons have descriptive labels
- [ ] Images have alt text
- [ ] Product info read correctly
- [ ] Loading states announced

#### C. Color Contrast
**Minimum Ratios:**
- Normal text: 4.5:1
- Large text (18pt+): 3:1
- UI components: 3:1

**Test with:**
- Chrome DevTools Contrast Checker
- WebAIM Contrast Checker
- Colour Contrast Analyser (CCA)

**Areas to Check:**
- [ ] Cyan text on dark backgrounds (Preorder)
- [ ] Purple text on dark backgrounds (Black Rose)
- [ ] Gold text on dark backgrounds (Love Hurts)
- [ ] Pink text on light backgrounds (Signature)

#### D. Motion & Animation
- [ ] Respect `prefers-reduced-motion` media query
- [ ] No auto-playing audio without user interaction
- [ ] No flashing content (seizure risk)
- [ ] Animations pausable/stoppable

**Command:**
```bash
# Run accessibility audit
npm run test:accessibility
```

---

### 6. WooCommerce Integration Tests 🛒

**Test Scenarios:**

#### A. Product Data Loading
- [ ] REST API endpoint returns products: `/wp-json/skyyrose/v1/products/3d/signature-collection`
- [ ] Product positions (X, Y, Z) load correctly
- [ ] Product images load
- [ ] Product prices display
- [ ] Product names display

**cURL Test:**
```bash
curl http://skyyrose.local/wp-json/skyyrose/v1/products/3d/signature-collection | jq
```

**Expected Response:**
```json
[
  {
    "id": 123,
    "name": "Luxury Rose Bouquet",
    "price": "$299.00",
    "image": "https://...",
    "url": "https://...",
    "position": {
      "x": 5.0,
      "y": 2.0,
      "z": -3.0
    }
  }
]
```

#### B. Add to Cart
- [ ] Click product hotspot → Modal opens
- [ ] Click "Add to Cart" → AJAX request succeeds
- [ ] Cart count updates
- [ ] Success message displays
- [ ] Modal closes

#### C. Product Admin
- [ ] Edit product in WordPress admin
- [ ] Set 3D position fields (X, Y, Z)
- [ ] Save product
- [ ] Verify position updates in 3D scene

#### D. Category Archives
- [ ] Static archive pages load
- [ ] Products display in WooCommerce grid
- [ ] Filters work (price, attributes)
- [ ] Sorting works (default, price, name)
- [ ] Pagination works
- [ ] "Enter 3D" button links correctly

---

### 7. 3D Scene Validation 🎮

**Per-Collection Tests:**

#### Signature Collection
- [ ] Glass pavilion renders with transparency
- [ ] HDR environment lighting works
- [ ] Golden hour atmosphere present
- [ ] Product hotspots glow gold
- [ ] Camera navigation smooth
- [ ] No console errors

#### Love Hurts Collection
- [ ] 80 rose petals fall with physics
- [ ] Cannon.js simulation stable (60fps)
- [ ] Chandelier toggles on/off
- [ ] Audio system ready (placeholder)
- [ ] LOD switches at correct distances
- [ ] Gothic architecture renders

#### Black Rose Collection
- [ ] Volumetric fog visible with TSL
- [ ] 50,000 fireflies animate smoothly
- [ ] God rays visible through windows
- [ ] Gothic cathedral architecture renders
- [ ] Fog toggle works
- [ ] Moonlit atmosphere present

#### Preorder Gateway
- [ ] Portal shader animates (swirling energy)
- [ ] 262,144 particles render (single draw call)
- [ ] Lenis smooth scroll works
- [ ] Camera syncs with scroll position
- [ ] Countdown timer updates every second
- [ ] Portal toggle works

**Validation Script:**
```bash
# Run 3D validation tests
npm run test:3d
```

---

### 8. Security Testing 🔒

**XSS Prevention:**
- [ ] Product names use `textContent` (not `innerHTML`)
- [ ] Product prices use `textContent`
- [ ] Product descriptions sanitized
- [ ] No user input directly inserted into DOM
- [ ] REST API uses nonces

**Test XSS:**
1. Create product with name: `<script>alert('XSS')</script>`
2. Load 3D scene
3. Click product hotspot
4. Verify script does NOT execute
5. Verify HTML entities escaped in modal

**WordPress Security:**
- [ ] Nonces used for AJAX requests
- [ ] REST API permissions set correctly
- [ ] File permissions correct (644/755)
- [ ] No hardcoded credentials
- [ ] SQL queries use `prepare()`

---

### 9. Production Readiness ✅

**Pre-Deployment Checklist:**

#### A. Asset Optimization
- [ ] JavaScript minified
- [ ] CSS minified
- [ ] Images optimized (WebP where possible)
- [ ] 3D models compressed (glTF Draco)
- [ ] Fonts subset (only used characters)

**Commands:**
```bash
# Build production assets
npm run build

# Verify minification
ls -lh assets/js/**/*.min.js
ls -lh assets/css/**/*.min.css
```

#### B. Caching
- [ ] Browser caching headers set (1 year for static assets)
- [ ] WP Rocket or similar cache plugin configured
- [ ] Object caching enabled (Redis/Memcached)
- [ ] Transients used for expensive queries

#### C. CDN Setup
- [ ] Static assets moved to CDN
- [ ] CDN URLs configured in theme
- [ ] CORS headers set for 3D assets
- [ ] Cache purge strategy defined

#### D. Error Handling
- [ ] WebGL not supported → Fallback message
- [ ] Product load fails → Error message
- [ ] 3D scene load fails → Graceful degradation
- [ ] Network errors → Retry logic

---

## Automated Testing Scripts

### Lighthouse Audit Script
**File:** `scripts/lighthouse-audit.sh`

```bash
#!/bin/bash

# Create output directory
mkdir -p tests/lighthouse

# Collections to test
collections=("signature-collection-3d" "love-hurts-3d" "black-rose-3d" "preorder-gateway-3d")

# Run audits
for collection in "${collections[@]}"; do
  echo "Testing $collection..."

  # Desktop
  npx lighthouse "https://skyyrose.local/$collection/" \
    --only-categories=performance,accessibility,best-practices,seo \
    --output=html \
    --output-path="./tests/lighthouse/${collection}-desktop.html" \
    --chrome-flags="--headless"

  # Mobile
  npx lighthouse "https://skyyrose.local/$collection/" \
    --only-categories=performance,accessibility,best-practices,seo \
    --output=html \
    --output-path="./tests/lighthouse/${collection}-mobile.html" \
    --preset=mobile \
    --chrome-flags="--headless"
done

echo "✅ Lighthouse audits complete. Check tests/lighthouse/ for reports."
```

### Accessibility Audit Script
**File:** `scripts/accessibility-audit.sh`

```bash
#!/bin/bash

# Create output directory
mkdir -p tests/accessibility

# Pages to test
pages=(
  "signature-collection-3d"
  "love-hurts-3d"
  "black-rose-3d"
  "preorder-gateway-3d"
  "product-category/signature-collection"
  "product-category/love-hurts"
  "product-category/black-rose"
  "product-category/preorder"
)

# Run pa11y tests
for page in "${pages[@]}"; do
  echo "Testing accessibility: $page..."

  npx pa11y "https://skyyrose.local/$page/" \
    --standard WCAG2AA \
    --reporter json \
    --timeout 30000 \
    > "tests/accessibility/${page//\//-}.json"
done

echo "✅ Accessibility audits complete. Check tests/accessibility/ for reports."
```

### Performance Monitoring Script
**File:** `scripts/performance-monitor.sh`

```bash
#!/bin/bash

# Test 3D scene performance
echo "Testing 3D scene performance..."

# Start Chrome with remote debugging
google-chrome \
  --remote-debugging-port=9222 \
  --headless \
  "https://skyyrose.local/signature-collection-3d/" &

# Wait for page to load
sleep 10

# Collect performance metrics
node scripts/collect-performance.js

# Kill Chrome
pkill chrome

echo "✅ Performance monitoring complete."
```

---

## Expected Results

### Lighthouse Scores

| Page | Performance | Accessibility | Best Practices | SEO |
|------|-------------|---------------|----------------|-----|
| Signature 3D | 90+ | 95+ | 95+ | 95+ |
| Love Hurts 3D | 88+ | 95+ | 95+ | 95+ |
| Black Rose 3D | 87+ | 95+ | 95+ | 95+ |
| Preorder 3D | 89+ | 95+ | 95+ | 95+ |
| Archives | 95+ | 95+ | 95+ | 95+ |

### Performance Metrics

| Scene | FPS | Draw Calls | Memory | GPU Memory |
|-------|-----|------------|--------|------------|
| Signature | 60 | ~50 | 80MB | 200MB |
| Love Hurts | 60 | ~60 | 100MB | 250MB |
| Black Rose | 60 | ~15 | 120MB | 300MB |
| Preorder | 60 | ~10 | 150MB | 400MB |

### Accessibility

| Criteria | Target | Status |
|----------|--------|--------|
| Keyboard Navigation | 100% | ✅ |
| Screen Reader | WCAG AA | ✅ |
| Color Contrast | 4.5:1+ | ✅ |
| Motion Safety | No seizures | ✅ |

---

## Issue Tracking

### High Priority
- [ ] Issue #1: Description
- [ ] Issue #2: Description

### Medium Priority
- [ ] Issue #3: Description
- [ ] Issue #4: Description

### Low Priority
- [ ] Issue #5: Description
- [ ] Issue #6: Description

---

## Sign-Off

### Testing Complete
- [ ] All Lighthouse audits passed
- [ ] Performance targets met
- [ ] Mobile testing complete
- [ ] Cross-browser validation done
- [ ] Accessibility compliance verified
- [ ] WooCommerce integration tested
- [ ] 3D scenes validated
- [ ] Security checks passed
- [ ] Production readiness confirmed

**Tested By:** _________________
**Date:** _________________
**Approved By:** _________________
**Date:** _________________

---

**Phase 6 Status:** In Progress 🔄
**Target Completion:** All validations passed, ready for production deployment
