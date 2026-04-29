# WordPress Theme JS — Agent Guide

## Isolated Workspace

**Your scope — read/write freely:**
```
wordpress-theme/skyyrose-flagship/assets/js/
  (EXCEPT experiences/ — that subdirectory has its own AGENTS.md and separate agent scope)
```

**Adjacent reads allowed (do not write):**
```
wordpress-theme/skyyrose-flagship/inc/enqueue.php   # to understand how scripts are loaded
wordpress-theme/skyyrose-flagship/assets/css/       # read only — understand class names
```

**Out of bounds — do not touch:**
```
wordpress-theme/skyyrose-flagship/assets/js/experiences/   # separate agent scope
wordpress-theme/skyyrose-flagship/inc/                     # separate agent scope
frontend/                                                  # completely separate system
```

If a change requires modifying `inc/enqueue.php` to register a new script, flag it and describe the required change — do not make it yourself.

---

## Infrastructure

**Host**: WordPress.com Business plan — NOT self-hosted
- **Deploy**: `bash scripts/deploy-theme.sh` (atomic hot-swap script) OR `sftp sftp.wp.com` (SSH upload) — both require explicit user confirmation before execution
- No build pipeline — all files are vanilla ES6, loaded via `wp_enqueue_script()` in `inc/enqueue.php`
- WordPress Coding Standard applies to PHP; JS follows ESLint

---

## File Map

| File | Purpose | Loaded on |
|------|---------|-----------|
| `navigation.js` | Mobile nav open/close, keyboard trap | All pages |
| `product-card-holo.js` | Holographic tilt card system | All pages with product grids |
| `premium-interactions.js` | `rv-*`, `magnetic`, `btn-sweep`, `stagger-grid` | All pages (global) |
| `collection-pages.js` | Palette switching, scroll-reveal (`.col-reveal`) | Collection templates only |
| `landing-pages.js` | Palette switching, scroll-reveal (`.lp-rv`) | Landing templates only |
| `size-guide.js` | Size guide modal open/close | All pages |
| `toast.js` | Global `window.skyyToast(msg, type, duration)` | All pages |
| `skyy-3d.js` | SkyyRose avatar GLB loader (Three.js) | Immersive templates |
| `init-3d.js` | Three.js scene bootstrap | Immersive templates |

**`experiences/`** — per-collection Three.js scene classes. See `experiences/AGENTS.md`. Do not edit those files.

---

## Permissions

You MAY:
- Modify event listeners, CSS class toggling, and DOM queries in any file in your workspace
- Add new IntersectionObserver-based scroll-reveal triggers
- Use `window.skyyToast` from `toast.js` in any file
- Add new utility functions inside existing files (no new global variables without documenting here)
- Describe required enqueue changes for the user to apply in `inc/enqueue.php`

You MUST NOT (without explicit user confirmation):
- Add jQuery — not loaded in this theme, banned
- Add GSAP to `collection-pages.js` or `landing-pages.js` — IntersectionObserver only in those files
- Use `innerHTML` anywhere — XSS vector, banned
- Introduce new global `window.*` variables without adding them to the Global APIs table below
- Edit any file inside `experiences/` — separate agent scope
- Execute the deploy script directly

---

## Safeguards — Hard Rules

**No `innerHTML` — ever:**
```js
// WRONG — XSS vector
el.innerHTML = `<span class="name">${product.name}</span>`;

// CORRECT — DOM construction only
const span = document.createElement('span');
span.className = 'name';
span.textContent = product.name; // textContent is safe
el.appendChild(span);
```

**No jQuery** — use native DOM APIs:
```js
document.querySelector('.btn')         // not $(.btn)
el.addEventListener('click', handler)  // not el.on('click', handler)
el.classList.add('active')             // not el.addClass('active')
el.dataset.collection                  // not el.data('collection')
```

**Always use the global toast — never create a custom implementation:**
```js
window.skyyToast('Added to wishlist', 'success', 3000);
```

**Collection and landing scroll-reveal = IntersectionObserver only:**
```js
// collection pages: .col-reveal → .col-reveal--visible
// landing pages: .lp-rv → .lp-rv--visible
const observer = new IntersectionObserver(
    (entries) => entries.forEach(e => {
        if (e.isIntersecting) e.target.classList.add('col-reveal--visible');
    }),
    { threshold: 0.15, rootMargin: '0px 0px -50px 0px' }
);
document.querySelectorAll('.col-reveal').forEach(el => observer.observe(el));
```

**GSAP allowed only on:** preorder template, about template, immersive templates. Never on collection or landing pages.

**Immediate fix mandate**: If you find an `innerHTML` or jQuery call while working, fix it in the same commit.

---

## Global APIs (Do Not Remove or Rename)

| Global | File | Signature |
|--------|------|-----------|
| `window.skyyToast` | `toast.js` | `(message: string, type: 'success'\|'error'\|'info', duration?: number) => void` |
| `window.SkyyRoseNav` | `navigation.js` | `{ open(), close(), isOpen() }` |
| `window.SkyyRoseHolo` | `product-card-holo.js` | `{ init(), destroy() }` |

---

## New Script Enqueue Pattern

When a new script needs registering, provide this block for the user to add to `inc/enqueue.php`:
```php
wp_enqueue_script(
    'skyyrose-my-feature',
    get_template_directory_uri() . '/assets/js/my-feature.js',
    [], // dependencies
    SKYYROSE_VERSION,
    [ 'strategy' => 'defer', 'in_footer' => true ]
);
```

---

## Mandatory Quality Workflow

After every change to any JS file in your workspace, run ALL three steps.

### 1. JS Lint
```bash
cd wordpress-theme/skyyrose-flagship
# If ESLint is configured:
npx eslint assets/js/ --ext .js --ignore-pattern 'experiences/'
# Alternatively, check for syntax errors:
node --check assets/js/navigation.js
node --check assets/js/toast.js
# Zero new errors or warnings introduced.
```

### 2. /simplify
Invoke the `code-simplifier` agent on the modified file(s). Focus on: event listener cleanup, IntersectionObserver disconnect on page unload, and repeated DOM queries (cache them).

### 3. /verification-loop
```bash
# Check live site loads
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co/
# Must return 200.

# Manual browser checks on affected page:
# 1. Open Chrome DevTools → Console → verify 0 JS errors
# 2. Test at 375px viewport (mobile)
# 3. Tab through all interactive elements — verify keyboard navigation works
# 4. Trigger any toast — verify it appears and auto-dismisses
```

---

## Do NOT

- Use `innerHTML` — XSS vector, banned in this codebase
- Add jQuery — not in this theme
- Add GSAP to `collection-pages.js` or `landing-pages.js`
- Create custom toast implementations — always `window.skyyToast`
- Omit `SKYYROSE_VERSION` from enqueue — cache-busting requires it
- Add render-blocking scripts (always `defer` or `in_footer`)
- Edit `experiences/` files — out of scope for this agent
