# Accessibility Audit Report
## SkyyRose WordPress Theme v1.0.0

**Product/Feature**: SkyyRose Flagship Theme — full site audit
**Standard**: WCAG 2.2 Level AA
**Date**: 2026-05-04
**Auditor**: AccessibilityAuditor (source code review)
**Tools Used**: Source code static analysis, Python3 contrast ratio calculations (WCAG relative luminance formula), grep-based pattern analysis, manual review of all interactive component logic

---

## Testing Methodology

**Automated Scanning**: Not executed. axe-core CLI v12.8.2 is installed but requires a running local WordPress server. No local WP environment available in this audit context. Lighthouse and pa11y not run. All findings are from static source code analysis.

**Assistive Technology Testing**: Not executed in this audit. Findings reflect what the code will produce for screen readers, not live AT session recordings. Manual AT testing is recommended before ThemeForest submission.

**Keyboard Testing**: Traced from source — all interactive flows reviewed through JS event handler analysis and PHP template structure.

**Visual Testing**: Contrast ratios computed programmatically via WCAG 2.1 relative luminance formula. Zoom behavior inferred from CSS layout patterns.

**Cognitive Review**: Heading hierarchy, landmark structure, error recovery patterns, and reading order reviewed from source.

**Scope**: Source code review of `/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/`. Files reviewed: `assets/css/design-tokens.css`, `assets/css/accessibility.css`, `assets/css/system/animations-premium.css`, `assets/css/fonts.css`, `assets/css/header.css`, `assets/js/premium-interactions.js`, `assets/js/product-card-holo.js`, `assets/js/navigation.js`, `assets/js/experiences/init-3d.js`, `template-parts/product-card-holo.php`, `template-parts/cookie-consent.php`, `template-parts/size-guide-modal.php`, `header.php`, `footer.php`, `woocommerce/checkout/form-checkout.php`, `inc/enqueue.php`, `inc/accessibility-fix.php`.

**Extrapolations**: Collection page, landing page, and immersive template findings are extrapolated from the shared engine files reviewed (holo card system, premium-interactions.js, init-3d.js). No separate template PHP was read for those page types.

---

## Summary

**Total Issues Found**: 17
- Critical: 2 — Blocks access entirely for some users
- Serious: 7 — Major barriers requiring workarounds
- Moderate: 6 — Causes difficulty but has workarounds
- Minor: 2 — Annoyances that reduce usability

**WCAG Conformance**: DOES NOT CONFORM (multiple Level A and AA failures)
**Assistive Technology Compatibility**: PARTIAL (keyboard and screen reader users face multiple barriers; foundations are solid but component-level gaps block critical flows)

---

## Top 5 ThemeForest Submission Blockers

These five issues will trigger a ThemeForest reviewer rejection or required-fix request:

1. **Three.js scenes have no `prefers-reduced-motion` gate and no non-3D fallback** — full-page animated canvases run unconditionally for vestibular users. This is both a WCAG 2.3.3 failure and a guaranteed reviewer flag on an animation-heavy theme.
2. **Search input in the header has no label** — the most visible interactive element on every page fails WCAG 4.1.2. A ThemeForest reviewer will find this in 30 seconds of tab-testing.
3. **Checkout progress bar has `role="navigation"`** — a progress indicator is semantically misidentified as a navigation landmark; this is the kind of ARIA misuse ThemeForest reviewers are specifically trained to catch.
4. **Crimson `#DC143C` fails contrast on dark backgrounds for normal-weight text** — a brand accent color used for badges, error states, and CTA elements fails 4.5:1 minimum (3.97:1 on `#0A0A0A`). Brand color contrast failures are a common rejection reason.
5. **Cookie consent dialog lacks focus trap** — the GDPR consent dialog is the first thing many users encounter; a `role="dialog"` without a focus trap is a textbook WCAG 2.1.2 violation that will appear in any automated scan of the live site.

---

## Issues Found

### Issue 1: Three.js immersive scenes — no prefers-reduced-motion gate, no canvas text alternative
**WCAG Criterion**: 2.3.3 Animation from Interactions (Level AAA); 1.1.1 Non-text Content (Level A); 1.4.2 Audio Control (Level A applies by analogy for animated canvases)
**Severity**: Critical
**User Impact**: Users with vestibular disorders (BPPV, Meniere's disease, migraines) experience nausea and disorientation from full-page 3D animations. With no reduced-motion gate, there is no escape short of leaving the page. Screen reader users receive zero information about what the canvas displays.
**Location**: `assets/js/experiences/init-3d.js` — throughout; `template-immersive-*.php` (all four collection immersive pages)

**Current State**:
```javascript
// init-3d.js — no prefers-reduced-motion check anywhere
// Scene initializes and begins animation loop unconditionally
async function init() {
  const ExperienceClass = await loadExperienceClass();
  experience = new ExperienceClass(canvas, config);
  await experience.init();
  // animation loop starts immediately
}
```
The canvas elements in immersive templates have no `role="img"`, no `aria-label`, and no visible fallback content. The 5-second fallback on Three.js load failure logs `console.warn('THREE.js failed')` but renders nothing visible to users.

**Recommended Fix**:
```javascript
// At the top of init-3d.js, before any scene initialization:
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

async function init() {
  if (prefersReducedMotion) {
    showStaticFallback(); // render a static image instead
    return;
  }
  // ... existing init code
}

function showStaticFallback() {
  const canvas = document.getElementById('experience-canvas');
  if (!canvas) return;
  const fallback = document.createElement('div');
  fallback.className = 'experience-static-fallback';
  fallback.setAttribute('role', 'img');
  fallback.setAttribute('aria-label', pageConfig.collectionName + ' collection visual');
  canvas.replaceWith(fallback);
}
```

For each canvas rendered by PHP templates:
```html
<canvas id="experience-canvas"
        role="img"
        aria-label="Black Rose collection — immersive 3D scene">
  <p>An immersive 3D scene for the Black Rose collection. Enable a modern browser to view.</p>
</canvas>
```

**Testing Verification**: Enable `prefers-reduced-motion: reduce` in OS accessibility settings. Navigate to `/collections/black-rose/immersive/`. Confirm the 3D scene does not initialize. Confirm a static image or fallback content is visible. Screen reader should announce the canvas label.

---

### Issue 2: Search input has no accessible label
**WCAG Criterion**: 1.3.1 Info and Relationships (Level A); 4.1.2 Name, Role, Value (Level A)
**Severity**: Critical
**User Impact**: Screen reader users navigating to the search overlay are told there is a text field but receive no indication of its purpose. The placeholder "SEARCH THE COLLECTION..." is not announced by most screen readers because `placeholder` is not a label substitute.
**Location**: `header.php` line 102

**Current State**:
```html
<input type="search"
       id="search-input"
       class="search-overlay__input"
       placeholder="SEARCH THE COLLECTION..."
       name="s">
```

**Recommended Fix**:
```html
<label for="search-input" class="screen-reader-text">
  Search the SkyyRose collection
</label>
<input type="search"
       id="search-input"
       class="search-overlay__input"
       placeholder="Search the collection..."
       name="s"
       autocomplete="off">
```
The `screen-reader-text` utility class is already defined in `accessibility.css` and is visually hidden while remaining in the accessibility tree.

---

### Issue 3: Checkout progress bar has incorrect `role="navigation"`
**WCAG Criterion**: 1.3.1 Info and Relationships (Level A); 4.1.2 Name, Role, Value (Level A)
**Severity**: Serious
**User Impact**: Screen readers announce the progress bar as a navigation landmark and list it in the page's landmark summary. Landmark navigation users encounter phantom navigation that does nothing.
**Location**: `woocommerce/checkout/form-checkout.php`

**Current State**:
```html
<div class="checkout-progress" role="navigation" aria-label="Checkout Steps">
  <div class="checkout-progress__step active">1. Contact</div>
  ...
</div>
```

**Recommended Fix**:
```html
<div class="checkout-progress" role="list" aria-label="Checkout progress">
  <div class="checkout-progress__step active" role="listitem" aria-current="step">
    <span class="screen-reader-text">Current step: </span>1. Contact
  </div>
  <div class="checkout-progress__step" role="listitem">2. Shipping</div>
  <div class="checkout-progress__step" role="listitem">3. Payment</div>
  <div class="checkout-progress__step" role="listitem">4. Review</div>
</div>
```

---

### Issue 4: Checkout inactive steps not hidden from screen readers
**WCAG Criterion**: 1.3.1 Info and Relationships (Level A); 4.1.3 Status Messages (Level AA)
**Severity**: Serious
**User Impact**: Screen reader users reading checkout linearly encounter all four step panels simultaneously. Steps 2-4 are visually hidden by CSS but remain in the accessibility tree.
**Location**: `woocommerce/checkout/form-checkout.php`

**Recommended Fix**: When JS shows/hides steps, also manage `aria-hidden` and `inert`:
```javascript
function activateStep(stepIndex) {
  steps.forEach((step, i) => {
    if (i === stepIndex) {
      step.classList.add('checkout-step--active');
      step.removeAttribute('aria-hidden');
      step.removeAttribute('inert');
    } else {
      step.classList.remove('checkout-step--active');
      step.setAttribute('aria-hidden', 'true');
      step.setAttribute('inert', '');
    }
  });
  announceRegion.textContent = 'Step ' + (stepIndex + 1) + ' of 4: ' + stepTitles[stepIndex];
}
```

---

### Issue 5: Cookie consent dialog missing focus trap and `aria-modal`
**WCAG Criterion**: 2.1.2 No Keyboard Trap (Level A); 4.1.2 Name, Role, Value (Level A)
**Severity**: Serious
**User Impact**: Keyboard users can exit the dialog and interact with the page behind it. Screen readers with `role="dialog"` but no `aria-modal="true"` may read the full page tree.
**Location**: `template-parts/cookie-consent.php`

**Recommended Fix**:
```php
<div id="cookie-consent" class="cookie-consent cookie-consent--hidden"
     role="dialog" aria-labelledby="cookie-consent-title"
     aria-modal="true" aria-describedby="cookie-consent-desc">
```

Implement focus trap in JS (see size-guide-modal.php as reference pattern — already correct):
```javascript
function showCookieBanner() {
  banner.classList.remove('cookie-consent--hidden');
  banner.removeAttribute('inert');
  const firstBtn = banner.querySelector('button');
  if (firstBtn) firstBtn.focus();
  banner.addEventListener('keydown', trapFocus);
  document.querySelector('#page').setAttribute('inert', '');
}

function trapFocus(e) {
  if (e.key !== 'Tab') return;
  const focusable = banner.querySelectorAll('button, a, input, [tabindex]:not([tabindex="-1"])');
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault(); last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault(); first.focus();
  }
}
```

---

### Issue 6: Search overlay — focus not returned to trigger on close
**WCAG Criterion**: 2.4.3 Focus Order (Level A); 2.4.11 Focus Not Obscured (Level AA, WCAG 2.2)
**Severity**: Serious
**Location**: `assets/js/navigation.js`

**Recommended Fix**:
```javascript
let searchTrigger = null;

function openSearchOverlay(triggerElement) {
  searchTrigger = triggerElement;
  overlay.classList.add('is-active');
  overlay.removeAttribute('aria-hidden');
  overlay.removeAttribute('inert');
  document.body.classList.add('search-open');
  searchInput.focus();
}

function closeSearchOverlay() {
  overlay.classList.remove('is-active');
  overlay.setAttribute('aria-hidden', 'true');
  overlay.setAttribute('inert', '');
  document.body.classList.remove('search-open');
  if (searchTrigger) {
    searchTrigger.focus();
    searchTrigger = null;
  }
}
```

---

### Issue 7: Crimson `#DC143C` contrast ratio fails for normal-weight text
**WCAG Criterion**: 1.4.3 Contrast (Minimum) (Level AA)
**Severity**: Serious
**Location**: `assets/css/design-tokens.css` — `[data-collection="love-hurts"]` palette; `assets/css/accessibility.css` line 215

**Evidence** (computed via WCAG 2.1 relative luminance formula):
- `#DC143C` on `#0A0A0A`: **3.97:1** — FAILS 4.5:1 normal text; PASSES 3:1 large text
- `#DC143C` on `#111111`: **3.78:1** — FAILS both thresholds

**Recommended Fix**:
```css
[data-collection="love-hurts"] {
  --skyyrose-accent: #E8305A;          /* 4.52:1 on #0A0A0A — passes */
  --skyyrose-accent-large-text: #DC143C; /* large text only */
}
```

---

### Issue 8: Rose Gold `#B76E79` contrast ratio fails on white
**WCAG Criterion**: 1.4.3 Contrast (Minimum) (Level AA)
**Severity**: Serious
**Location**: `assets/css/accessibility.css` line 22 (skip link)

**Evidence**: `#B76E79` on `#FFFFFF`: **3.80:1** — FAILS 4.5:1 normal text. Skip link label is 12px uppercase.

**Recommended Fix**: Invert the skip link colors:
```css
.skip-link {
  background: #0A0A0A;
  color: var(--color-rose-gold, #B76E79); /* 5.26:1 on #0A0A0A — PASSES */
  border: 2px solid #B76E79;
}
```

---

### Issue 9: Size pills are `<span>` elements — not keyboard accessible, ARIA misuse
**WCAG Criterion**: 2.1.1 Keyboard (Level A); 4.1.2 Name, Role, Value (Level A)
**Severity**: Serious
**User Impact**: Keyboard users cannot select sizes on holographic product cards because `<span>` elements do not receive focus. JS applies `aria-checked` to `<span>` — invalid: `aria-checked` requires roles `checkbox`, `radio`, `menuitemcheckbox`, `menuitemradio`, `switch`, or `treeitem`.
**Location**: `template-parts/product-card-holo.php` lines 62-65; `assets/js/product-card-holo.js`

**Recommended Fix**:
```php
<div class="holo__sizes" role="radiogroup" aria-label="Select size for <?php echo esc_attr($title); ?>">
  <?php foreach ($sizes as $i => $size): ?>
    <button class="holo__size-pill" role="radio"
      aria-checked="<?php echo ($i === 0) ? 'true' : 'false'; ?>"
      type="button" data-size="<?php echo esc_attr($size); ?>">
      <?php echo esc_html($size); ?>
    </button>
  <?php endforeach; ?>
</div>
```

Add arrow-key navigation per WAI-ARIA Authoring Practices for radio groups.

---

### Issue 10: Buy button empties text content during loading state with no accessible label
**WCAG Criterion**: 4.1.2 Name, Role, Value (Level A)
**Severity**: Serious
**Location**: `assets/js/product-card-holo.js` line 213

**Current State**:
```javascript
btn.disabled = true;
btn.setAttribute('aria-busy', 'true');
btn.textContent = '';  // empties — no label remains
```

**Recommended Fix**:
```javascript
btn.disabled = true;
btn.setAttribute('aria-busy', 'true');
btn.setAttribute('aria-label', 'Adding to cart, please wait');
btn.textContent = '';

// On completion:
btn.removeAttribute('aria-busy');
btn.setAttribute('aria-label', 'Added to cart');
btn.textContent = 'Added';
setTimeout(() => {
  btn.removeAttribute('aria-label');
  btn.textContent = 'Add to Cart';
  btn.disabled = false;
}, 2000);
```

---

### Issue 11: Desktop navigation — no keyboard arrow navigation or ARIA for dropdowns
**WCAG Criterion**: 4.1.2 Name, Role, Value (Level A); 2.1.1 Keyboard (Level A)
**Severity**: Moderate
**Location**: `assets/js/navigation.js`

**Recommended Fix** (per WAI-ARIA Authoring Practices for disclosure menus):
```javascript
navLinks.forEach(link => {
  const dropdown = link.nextElementSibling;
  if (!dropdown || !dropdown.classList.contains('nav-dropdown')) return;

  link.setAttribute('aria-haspopup', 'true');
  link.setAttribute('aria-expanded', 'false');

  link.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
      e.preventDefault();
      dropdown.classList.add('is-open');
      link.setAttribute('aria-expanded', 'true');
      dropdown.querySelector('a').focus();
    }
  });

  dropdown.addEventListener('keydown', (e) => {
    const items = [...dropdown.querySelectorAll('a')];
    const idx = items.indexOf(document.activeElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); items[Math.min(idx+1, items.length-1)].focus(); }
    if (e.key === 'ArrowUp') { e.preventDefault(); items[Math.max(idx-1, 0)].focus(); }
    if (e.key === 'Escape') {
      dropdown.classList.remove('is-open');
      link.setAttribute('aria-expanded', 'false');
      link.focus();
    }
  });
});
```

---

### Issue 12: Reveal animations start `opacity: 0` — content invisible when JS is blocked
**WCAG Criterion**: 1.3.1 Info and Relationships (Level A)
**Severity**: Moderate
**Location**: `assets/css/system/animations-premium.css`

**Recommended Fix** (Option A — `<noscript>` override, simplest):
```html
<noscript>
  <style>
    .rv-clip-up, .rv-clip-left, .rv-clip-right, .rv-blur, .rv-blur-down,
    .rv-split-char, .rv-split-word, .rv-split-line, .col-reveal, .lp-rv,
    .stagger-grid > * { opacity: 1 !important; clip-path: none !important; filter: none !important; }
  </style>
</noscript>
```

---

### Issue 13: Mobile menu panel lacks `role="dialog"` and `aria-modal`
**WCAG Criterion**: 4.1.2 Name, Role, Value (Level A)
**Severity**: Moderate
**Location**: `header.php` — `#mobile-menu` div

**Recommended Fix**:
```html
<div id="mobile-menu" class="mobile-menu"
     role="dialog" aria-modal="true" aria-label="Navigation Menu"
     aria-hidden="true" inert>
  <button class="mobile-menu__close" aria-label="Close navigation menu">
    <!-- close icon -->
  </button>
  <!-- nav items -->
</div>
```

---

### Issue 14: Skip link text "Skip to the story" is non-standard and confusing
**WCAG Criterion**: 2.4.1 Bypass Blocks (Level A)
**Severity**: Moderate
**Location**: `header.php` line 10

**Recommended Fix**:
```html
<a class="skip-link" href="#primary">Skip to main content</a>
```

The brand-voice "story" framing undermines the functional accessibility control. ThemeForest reviewers specifically test skip links.

---

### Issue 15: Size guide table headers missing `scope` attribute
**WCAG Criterion**: 1.3.1 Info and Relationships (Level A)
**Severity**: Moderate
**Location**: `template-parts/size-guide-modal.php`

**Recommended Fix**:
```html
<table class="size-guide__table">
  <caption class="screen-reader-text">Sizing measurements for <?php echo esc_html($product_name); ?></caption>
  <thead>
    <tr>
      <th scope="col">Size</th>
      <th scope="col">Chest (inches)</th>
      <th scope="col">Length (inches)</th>
    </tr>
  </thead>
  <tbody>
    <!-- data rows -->
  </tbody>
</table>
```

---

### Issue 16: Fixed header (88px) has no `scroll-padding-top` — focus may scroll under header
**WCAG Criterion**: 2.4.11 Focus Not Obscured (Minimum) (Level AA, WCAG 2.2)
**Severity**: Moderate
**Location**: `assets/css/header.css`, `assets/css/design-tokens.css`

**Recommended Fix** (single CSS declaration resolves the issue site-wide):
```css
:root {
  --header-height: 88px;
}

html {
  scroll-padding-top: var(--header-height, 88px);
}
```

---

### Issue 17: Holo card back image has generic alt text
**WCAG Criterion**: 1.1.1 Non-text Content (Level A)
**Severity**: Minor
**Location**: `template-parts/product-card-holo.php` line 48

**Recommended Fix**:
```php
<img src="..."
     alt="<?php echo esc_attr( $title . ' — technical blueprint view' ); ?>"
     class="holo__back-img">
```

---

### Issue 18: Required field asterisk uses crimson (already fails contrast — see Issue 7)
**WCAG Criterion**: 1.4.3 Contrast (Minimum) (Level AA)
**Severity**: Minor
**Location**: `assets/css/accessibility.css` line 208-211

Apply Issue 7's lightened crimson (`#E8305A`) to the `[aria-required="true"]::after` pseudo-element.

---

## What's Working Well

The following patterns are well-implemented and should be preserved:

**Focus visible system** (`accessibility.css`): Global `*:focus-visible` outline (2px rose-gold, 2px offset) correctly scoped to keyboard via `*:focus:not(:focus-visible) { outline: none }`. Hotspot, room-nav, and tab overrides appropriately sized.

**Reduced motion handling** (`animations-premium.css`, `premium-interactions.js`, `design-tokens.css`): Three separate mechanisms work in concert — CSS duration collapse, JS early-return forcing `.is-visible`, token-level `0.01ms` overrides. Film-grain animation explicitly disabled. Above-average implementation.

**Split-text ARIA pattern** (`premium-interactions.js`): `aria-label` set on parent before split, `aria-hidden="true"` on each child span. Exact pattern from WAI-ARIA Authoring Practices.

**Size guide modal** (`template-parts/size-guide-modal.php`): Excellent. `role="dialog"`, `aria-labelledby`, `aria-modal`, `inert`, full focus trap with Shift+Tab, ESC closes and returns focus, tab pattern uses `role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"`. Use as reference for cookie consent fix.

**Mobile menu** (`navigation.js`, `header.php`): `aria-expanded`, `aria-hidden`, `inert` correctly coordinated. Just needs `role="dialog"` + `aria-modal`.

**Self-hosted fonts** (`fonts.css`): All 9 families use `font-display: swap`, served from theme domain. Zero Google Fonts CDN. No FOIT.

**High contrast mode support** (`accessibility.css`): `@media (forced-colors: active)` correctly uses system keywords (`ButtonText`, `Highlight`). Rarely done well — commendable.

**Footer landmark structure** (`footer.php`): `<footer role="contentinfo">`. Three `<nav>` elements with distinct `aria-label` values. Newsletter form has `<label class="screen-reader-text">`.

**Accessibility output buffer** (`inc/accessibility-fix.php`): `SkyyRose_Accessibility_Fix` post-processes HTML to add `type="button"`, deduplicate IDs, add `aria-label` to empty links, add `tabindex="-1"` to `aria-hidden` focusable. Safety net for ThemeForest checklist items.

**Touch target sizes** (`accessibility.css`): `min-height: 44px; min-width: 44px` on `a, button, [role="button"], input[type="checkbox"], input[type="radio"], select, summary`. Inline links exempted. Correct WCAG 2.5.8.

**`prefers-contrast: more`** (`accessibility.css`): Enhanced palette for secondary, muted, dim text. Border colors boosted.

**`prefers-reduced-transparency`** (`accessibility.css`): Glassmorphism removed on navbar, search overlay, mobile menu, toast, back-to-top.

---

## WCAG 2.2 AA Conformance Scorecard

| Success Criterion | Level | Status | Notes |
|-------------------|-------|--------|-------|
| 1.1.1 Non-text Content | A | PARTIAL FAIL | Canvas no text alternative; generic back-image alt |
| 1.3.1 Info and Relationships | A | FAIL | Checkout role misuse; inactive steps in AT tree |
| 1.3.2 Meaningful Sequence | A | PASS | Reading order follows visual order |
| 1.4.1 Use of Color | A | PASS | Color not the only means of conveying information |
| 1.4.3 Contrast (Minimum) | AA | FAIL | Crimson 3.97:1; Rose Gold 3.80:1 |
| 1.4.4 Resize Text | AA | PASS | No absolute font sizes preventing zoom |
| 1.4.10 Reflow | AA | PASS* | Layout responsive; not verified at 320px |
| 1.4.11 Non-text Contrast | AA | PASS | 2px focus ring visible |
| 1.4.12 Text Spacing | AA | PASS | No `!important` on letter-spacing in body |
| 1.4.13 Content on Hover | AA | PASS | Hover dropdowns dismissible; content stable |
| 2.1.1 Keyboard | A | FAIL | Size pills not keyboard operable; desktop dropdowns |
| 2.1.2 No Keyboard Trap | A | FAIL | Cookie consent allows focus escape |
| 2.2.2 Pause Stop Hide | A | FAIL | Three.js scenes autoplay without reduced-motion gate |
| 2.3.3 Animation from Interactions | AAA | FAIL | Three.js not gated on prefers-reduced-motion |
| 2.4.1 Bypass Blocks | A | PARTIAL | Skip link present but non-standard text |
| 2.4.3 Focus Order | A | FAIL | Search overlay close loses focus |
| 2.4.4 Link Purpose | A | PARTIAL | Back images all labeled "Technical Blueprint" |
| 2.4.7 Focus Visible | AA | PASS | Global `:focus-visible` correct |
| 2.4.11 Focus Not Obscured (Min) | AA | FAIL | Fixed 88px header, no `scroll-padding-top` |
| 2.5.3 Label in Name | A | PASS | Button labels match visible text |
| 2.5.7 Dragging Movements | AA | PASS | Magnetic cursor hover-only |
| 2.5.8 Target Size (Minimum) | AA | PASS | 44×44px enforced |
| 3.2.1 On Focus | A | PASS | No unexpected context changes on focus |
| 3.2.2 On Input | A | PASS | No unexpected context changes on input |
| 3.3.1 Error Identification | AA | PARTIAL | WC standard handling present; custom announcements unverified |
| 3.3.2 Labels or Instructions | A | FAIL | Search input has no label |
| 4.1.2 Name, Role, Value | A | FAIL | Size pills, buy button, progress bar, search input |
| 4.1.3 Status Messages | AA | PARTIAL | Checkout step transitions not announced |

**Overall**: DOES NOT CONFORM to WCAG 2.2 Level AA. Six Level A failures and four Level AA failures require remediation before conformance can be claimed.

---

## Remediation Priority

### Immediate — fix before ThemeForest submission

1. **Three.js reduced-motion gate + canvas text alternative** (`init-3d.js`)
2. **Search input label** (`header.php` line 102)
3. **Checkout progress bar role** (`form-checkout.php`) — `role="navigation"` → `role="list"`
4. **Cookie consent focus trap + `aria-modal`** (`template-parts/cookie-consent.php`)
5. **Buy button label during loading** (`product-card-holo.js` line 213)
6. **Size pills keyboard accessibility** (`product-card-holo.php`)
7. **Search overlay — restore focus on close** (`navigation.js`)
8. **Crimson contrast** (`design-tokens.css`)

### Short-term — fix within next sprint

9. **`scroll-padding-top` for fixed header** (`design-tokens.css`)
10. **Skip link text** (`header.php` line 10) — "Skip to main content"
11. **No-JS reveal fallback** (`animations-premium.css`)
12. **Mobile menu `role="dialog"`**
13. **Desktop dropdown keyboard navigation** (`navigation.js`)
14. **Checkout inactive steps hidden from AT** (`form-checkout.php`)
15. **Size guide table `scope` attribute**

### Ongoing — address in regular maintenance

16. **Holo card back image alt text** — make product-specific
17. **Required field asterisk contrast**

---

## Recommended Next Steps

1. **Run live axe-core scan** when staging is available: `npx @axe-core/cli https://skyyrose.co --tags wcag2a,wcag2aa,wcag22aa`. Surfaces violations in rendered HTML that static analysis cannot catch (WC plugin output, Jetpack overlays, dynamic widget markup).

2. **AT testing session** with VoiceOver (macOS Safari) on checkout, product page, homepage before submission. Source analysis cannot detect AT announcement order, virtual cursor behavior, or live region timing.

3. **Integrate jest-axe** into component tests: `expect(render(<HoloCard product={mockProduct} />)).toHaveNoViolations()`.

4. **Add CI gate**: `npx @axe-core/cli $STAGING_URL --tags wcag2a,wcag2aa --exit` in deploy pipeline, gating on Critical and Serious only. Current `accessibility-fix.php` output buffer is a safety net, not a primary defense.

5. **Conformance statement**: After Critical/Serious remediation, draft partial WCAG 2.2 AA conformance statement for ThemeForest documentation listing known limitations and testing methodology.

---

## Source Files Reviewed

- `assets/css/accessibility.css`
- `assets/css/design-tokens.css`
- `assets/css/system/animations-premium.css`
- `assets/css/fonts.css`
- `assets/css/header.css`
- `assets/js/premium-interactions.js`
- `assets/js/product-card-holo.js`
- `assets/js/navigation.js`
- `assets/js/experiences/init-3d.js`
- `template-parts/product-card-holo.php`
- `template-parts/cookie-consent.php`
- `template-parts/size-guide-modal.php`
- `header.php`
- `footer.php`
- `woocommerce/checkout/form-checkout.php`
- `inc/enqueue.php`
- `inc/accessibility-fix.php`
