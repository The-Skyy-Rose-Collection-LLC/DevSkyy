# Lessons Learned

Patterns extracted from corrections. Review at session start.

## WordPress Theme
- CDN caches CSS aggressively — always bump `SKYYROSE_VERSION` for cache bust
- WordPress.com `page-optimize` plugin strips enqueued JS — inline JS in templates to bypass
- `enqueue.php` template slug map must match actual template filenames exactly
- When deleting files, grep ALL remaining files for references before committing
- When removing a PHP section, also remove its CSS rules AND responsive breakpoint overrides
- Don't duplicate content sections — if showcase cards show collections, don't add separate narrative cards
- Card content must be visible by default (`opacity: 1`) — mobile has no hover
- Collection pages use unified `col-*` classes with `data-collection` attribute — one CSS file, not four
- `php-lint.sh` needs explicit Homebrew PHP path (`/opt/homebrew/bin/php`) — lint-staged subshell doesn't inherit brew paths
- Image URLs: append `?v=' . SKYYROSE_VERSION` for CDN cache bust on branding images
- Cursor disappearing: Jetpack Instant Search overlay (z-index max, opacity 0, pointer-events auto) — fix with `pointer-events: none !important`
- Customizer DB values override `get_theme_mod()` defaults — hardcode values when Customizer has stale data
- "Where Love Meets Luxury" is NOT the tagline — "Luxury Grows from Concrete" is the only tagline

## Animation System
- Premium animations: `animations-premium.css` + `premium-interactions.js` loaded globally
- Use `rv-clip-*`, `rv-blur*`, `rv-split-*`, `stagger-grid`, `magnetic`, `btn-sweep`, `btn-border-draw` classes
- Old `.rv` system (`.vis` trigger) coexists with new premium system (`.is-visible` trigger) — both needed
- Never set `will-change` permanently in CSS — only during active animation
- Don't duplicate IntersectionObservers — one global observer in premium-interactions.js handles all premium classes
- SVG kses whitelist: use `skyyrose_svg_kses()` function, don't copy-paste the array

## Process
- Fix everything in one batch, test all pages, deploy ONCE — no back-and-forth
- Collection hero images are branded logo wordmarks (custom art), not just font choices
- The user's collection font = the actual logo wordmark image, not a CSS font-family
- Always check if assets exist before referencing them in templates
- Always verify with Chrome DevTools MCP screenshots before claiming pages render correctly
