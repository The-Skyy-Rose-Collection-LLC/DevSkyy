# Footer Logo Swap to Brand-Primary Monogram

**Date:** 2026-05-25
**Status:** Approved scope
**Owner:** Claude (DevSkyy engineering agent)
**Live target:** https://skyyrose.co
**Theme version at start:** 1.5.20

## Problem

`wordpress-theme/skyyrose-flagship/footer.php:67-68` currently renders the footer brand monogram from the legacy path:

```
assets/images/logos/sr-monogram-rose-gold.webp
```

That path predates the canonical `assets/branding/` hierarchy established last session (`docs/brand/asset-hierarchy.md`). The matching production-sized footer variant already exists at:

```
assets/branding/skyyrose-monogram-footer.webp   (978 B, verified 2026-05-25)
```

The header was already swapped last session to point at `assets/branding/skyyrose-monogram-nav.webp` (50×50). The footer was not. This spec closes that loop so the entire site chrome resolves to the canonical `assets/branding/` tier.

## Out of Scope (explicit drops from original 3-item backlog)

| Item | Why dropped |
|------|-------------|
| Mobile nav brand swap | Real file is `template-parts/mobile-bottom-nav.php`, a 5-icon glass nav with no brand mark by design. Mobile top header already shows the brand-primary monogram via `header.php`. |
| Favicon wiring | Already wired at `inc/seo.php:1001` (`skyyrose_favicon_tags()`, `wp_head` priority 2). Points at `assets/branding/skyyrose-rose-icon-favicon.webp`. `has_site_icon()` guard handles WP admin override. |

## Change

Single file edit: `wordpress-theme/skyyrose-flagship/footer.php`, lines ~67-74 (the `.footer-brand__logo-link` block).

### Before

```php
<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="footer-brand__logo-link" rel="home">
    <img
        src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/logos/sr-monogram-rose-gold.webp?v=' . SKYYROSE_VERSION ); ?>"
        alt="..."
        class="footer-brand__monogram"
        ...
    >
```

### After

```php
<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="footer-brand__logo-link" rel="home">
    <img
        src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/skyyrose-monogram-footer.webp?v=' . SKYYROSE_VERSION ); ?>"
        alt="..."
        class="footer-brand__monogram"
        width="60"
        height="60"
        decoding="async"
        loading="lazy"
        ...
    >
```

### Substantive deltas

1. **Source path** → canonical `assets/branding/skyyrose-monogram-footer.webp`.
2. **URI helper** → switch from `get_template_directory_uri() . '/assets/...'` to `SKYYROSE_ASSETS_URI . '/branding/...'` to match the pattern `header.php` already uses for the nav monogram (consistency within the chrome layer).
3. **Add `width="60" height="60"`** → prevents Cumulative Layout Shift; matches asset intent recorded in `docs/brand/asset-hierarchy.md`.
4. **Add `decoding="async" loading="lazy"`** → footer is below-fold, lazy is correct (header is `fetchpriority="high"`, footer is `loading="lazy"` — chrome-tier symmetry).
5. **Keep `?v=' . SKYYROSE_VERSION`** → cache-bust for CDN.
6. **Keep the existing `.footer-brand__text` wordmark span** below the img — that text wordmark stays. This swap is the monogram only.

## Acceptance Criteria

1. `npm run lint:php` exits 0.
2. `grep -c "sr-monogram-rose-gold" wordpress-theme/skyyrose-flagship/footer.php` returns 0.
3. `grep -c "branding/skyyrose-monogram-footer" wordpress-theme/skyyrose-flagship/footer.php` returns 1.
4. Local render (or post-deploy `curl -s "https://skyyrose.co/?cb=$(date +%s)" | grep skyyrose-monogram-footer`) returns the expected `<img>` tag.
5. No other files modified. `git diff --name-only` reports only `footer.php` + this spec.

## Risk

| Risk | Mitigation |
|------|------------|
| CDN cache serves stale asset | `?v=` query-arg appended; force-flush via deploy script's post-cache-flush step if needed. |
| `SKYYROSE_ASSETS_URI` constant not defined in scope | Verified — `functions.php:28` defines `SKYYROSE_ASSETS_URI` as `SKYYROSE_URI . '/assets'`. `header.php` already uses it identically. |
| Asset file missing on remote after deploy | Asset exists in repo (978 B, verified `ls`); deploy script uploads everything under `assets/`. Post-deploy 200-check on the URL confirms. |
| Layout shift from missing intrinsic dimensions | `width="60" height="60"` added; modern browsers honor intrinsic-size hints to reserve box before bytes arrive. |

## Verification (post-edit)

```bash
cd wordpress-theme
npm run lint:php
grep -nE "branding/skyyrose-monogram-footer|sr-monogram-rose-gold" skyyrose-flagship/footer.php
git diff --name-only
```

## Out-of-bound (do not touch in this change)

- `.footer-brand__text` wordmark span
- `.footer-brand__tagline`, `.footer-brand__description`, `.footer-brand__social` block
- `inc/seo.php` favicon function
- `header.php` nav monogram (already swapped)
- Any CSS in `assets/css/footer.css` — current selectors `.footer-brand__monogram` continue to apply

## Implementation Mode

One-shot edit. No plan-execute loop necessary. After spec approval:

1. Single Edit call against `footer.php`.
2. `npm run lint:php`.
3. Stage + commit (`fix: footer monogram → canonical branding/ tier`).
4. Defer deploy until bucket B (visual hero direction) is also ready — ship both at once to avoid two consecutive deploys.
