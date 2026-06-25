# SkyyRose v1.1.2 — Application Security Audit
**Date:** 2026-05-23 | **Scope:** skyyrose.co (WordPress.com) | **Source:** `/wordpress-theme/skyyrose-flagship/`
**Method:** `curl -sI https://skyyrose.co/` (homepage, `/shop/`, `/cart/`), source grep, targeted file reads

---

## Executive Summary

No CRITICAL findings. Two HIGH findings, both in client-side JavaScript. The PHP layer is well-hardened: nonces on all AJAX endpoints, `$wpdb->prepare()` throughout, `ABSPATH` guards present in all live-code PHP files, input sanitization consistent. The security header posture is strong but has one material gap: **HSTS is platform-stripped of `includeSubDomains; preload`** on the wire. The CSP ships `'unsafe-inline'` which is acknowledged and justified given WordPress/WooCommerce constraints.

**No findings block the current deploy.** The HIGH findings should be addressed in the next sprint.

---

## 1. Security Headers — Live Wire vs. Source

Tested with: `curl -sI https://skyyrose.co/` (2026-05-23T23:20:14Z)

### 1.1 Content-Security-Policy

**Status: Present. PASS with caveats.**

Wire value matches `inc/security.php` lines 46–61 verbatim. CSP is correctly sent on all page types tested (homepage, `/shop/`, `/cart/`).

| Directive | Value | Assessment |
|-----------|-------|------------|
| `default-src` | `'self'` | Good |
| `script-src` | `'self' 'unsafe-inline'` + 8 external origins + `blob:` | See SEC-02 |
| `style-src` | `'self' 'unsafe-inline'` + fonts.wp.com, cdn.jsdelivr.net, cdnjs.cloudflare.com | Justified (WP/WC inline styles) |
| `img-src` | `'self' data: blob: *.wp.com gravatar *.skyyrose.co facebook` | Good |
| `connect-src` | `'self'` + stats.wp.com, public-api.wordpress.com, api.skyyrose.co, pixel.wp.com, devskyy.app, facebook | Good |
| `frame-ancestors` | `'self'` | Good (also backed by X-Frame-Options) |
| `object-src` | `'none'` | Good |
| `base-uri` | `'self'` | Good |
| `form-action` | `'self'` | Good |
| `upgrade-insecure-requests` | present | Good |
| `worker-src` | `'self' blob:` | Correct for Three.js workers |

**SEC-01 Low** — `X-Frame-Options: SAMEORIGIN` redundant with CSP `frame-ancestors 'self'`. Harmless duplication; keep both for legacy browsers, but if `frame-ancestors` ever tightens to `'none'`, update X-Frame-Options together.

**SEC-02 Medium** — `'unsafe-inline'` in `script-src`. Acknowledged at `inc/security.php:41–44`. WordPress/WooCommerce/Jetpack inject inline scripts without nonces. Path to remediation: `wp_nonce_inline_scripts()` (WP 6.1+). Sprint-level work, not deploy blocker.

**SEC-03 Low** — `https://unpkg.com` in `script-src`. Public npm CDN = effectively `'unsafe-src'`. Verify via `grep -rn "unpkg.com" theme --include='*.{php,js}' | grep -v vendor`; if no usage, remove from `inc/security.php:48`.

**SEC-04 Low** — `https://devskyy.app` in `connect-src`. Verify intentional on customer-facing pages; if admin-only, remove from front-end CSP.

### 1.2 HSTS

**SEC-05 Medium** — `includeSubDomains; preload` stripped by WP.com edge.

Source (`inc/security.php:76`):
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```
Live wire:
```
strict-transport-security: max-age=31536000
```

Theme code correct; WP.com edge strips both directives. Subdomains unprotected; preload submission impossible. **Remediation:** WP.com support ticket OR check Business plan custom header allowance.

### 1.3 Other Headers

| Header | Live Value | Assessment |
|--------|-----------|------------|
| `X-Content-Type-Options` | `nosniff` | PASS |
| `X-Frame-Options` | `SAMEORIGIN` | PASS (see SEC-01) |
| `X-XSS-Protection` | `0` | PASS — correct modern value |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | PASS |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(self), ...` | PASS |
| `Cross-Origin-Opener-Policy` | `same-origin` | PASS |
| `Cross-Origin-Resource-Policy` | `same-site` | PASS |

`payment=(self)` correct for WC checkout. WebGL/Three.js not Permissions-Policy controlled.

---

## 2. CSP Inline Nonce Coverage

`'unsafe-inline'` in `script-src` + `style-src` means no per-request nonce enforcement. Documented in source. Inline scripts in templates: WP localize, enqueue inline, Three.js init — all use server-side PHP data through WP escaping layers. No user-controlled interpolation found. Risk from `'unsafe-inline'` is theoretical XSS amplification, not standalone exploit path from theme code.

Migration path: `wp_nonce_inline_scripts()` (WP 6.1+) — future hardening sprint.

---

## 3. WordPress Hardening

### 3.1 AJAX Endpoints — Nonce Coverage

27 `wp_ajax_*` / `wp_ajax_nopriv_*` registrations across 5 files. All have nonce verification:

| File | Handlers | Nonce |
|------|----------|-------|
| `inc/immersive-ajax.php` | get_product_by_sku, get_collection_products, immersive_add_to_cart | `wp_verify_nonce` L34, 113, 217 |
| `inc/woocommerce.php` | get_cart_count | `check_ajax_referer` L511 |
| `inc/klaviyo-integration.php` | klaviyo_subscribe | `wp_verify_nonce` L225 |
| `inc/wishlist-functions.php` | add/remove/move/clear/move_all | `check_ajax_referer` L285, 324, 363, 399, 415, 444 |
| `inc/ajax-handlers.php` | contact_submit, newsletter_subscribe, incentive_signup, signin, track_referral, mascot_chat | `wp_verify_nonce` L63, 202, 276, 354/445, 479, 550 |

**PASS.** All public AJAX has nonce verification as first operation. Double-check at L354 + L445 in `signin` correct (two separate hook paths).

### 3.2 Capability Checks — PASS

`current_user_can()` verified on all write-capable admin AJAX + meta saves: `inc/woocommerce.php:449`, `inc/builders/elementor-compat.php:155`, `inc/woocommerce-kids-capsule.php:116`, `inc/woocommerce-preorder.php:110`, `inc/skyyrose-product-meta.php:456`, `inc/experience-engine.php:310`, `inc/accessibility-seo.php:250`.

### 3.3 wpdb Query Safety — PASS

44+ `$wpdb->` call sites. Spot-checked `inc/experience-analyzer.php:70–160` + `inc/experience-engine.php:250–251`. All use `$wpdb->prepare()` with placeholders. No string concatenation found.

### 3.4 ABSPATH Guards — PASS

All live-code PHP files have `defined('ABSPATH') || exit`. Missing-guard list (404.php, index.php, etc.) are WP template registration / test stubs / vendor — not directly accessible.

### 3.5 Input Sanitization — PASS

`inc/ajax-handlers.php`: `sanitize_text_field()`, `sanitize_email()`, `sanitize_textarea_field()`, `absint()`, `sanitize_key()` consistent. Length limits (`mb_substr(..., 0, 100)` names, `0, 5000` body). Password correctly unsanitized w/ phpcs ignore.

### 3.6 Output Escaping — PASS

`wp_send_json_error/success` payloads pass strings through `esc_html__()` across `inc/ajax-handlers.php`, `inc/immersive-ajax.php`, `inc/wishlist-functions.php`.

---

## 4. XSS Surface — innerHTML in JavaScript

Cerebrum claim "No innerHTML in JS" — **partially stale.** 5 active uses found.

### SEC-06 HIGH — `smart-showcase.js` static HTML template injection

`assets/js/smart-showcase.js:34`:
```javascript
dialog.innerHTML = [
  '<div class="skyy-qv__backdrop" aria-hidden="true"></div>',
  '<div class="skyy-qv__panel" role="document">',
  ...
].join('');
```
Hardcoded static HTML — no user data. Not exploitable but violates codebase ban + sets bad pattern for future contributors.

`smart-showcase.js:107`:
```javascript
dialog.querySelector('#skyy-qv-price').innerHTML = priceEl ? priceEl.innerHTML : '';
```
Clones WC server-rendered price HTML. Currently safe (WC escaping), but fragile if WC ever injects unescaped content.

`smart-showcase.js:115`:
```javascript
sizesContainer.innerHTML = '';
```
Empty-string clear. Not XSS; prefer `replaceChildren()` or `while (el.firstChild) el.removeChild(el.firstChild)`.

**Fix L34:** Replace with `document.createElement` + `appendChild` / `DocumentFragment`.
**Fix L107:** Use `textContent` for price text. If formatted HTML needed (sale price strikethrough), use `document.createRange().createContextualFragment(sanitizedHtml)`.

### SEC-07 HIGH — `immersive-wc-bridge.js` WooCommerce cart fragment injection

`assets/js/immersive-wc-bridge.js:53–62`:
```javascript
// "Sandboxed parse" comment, but intermediate tmp.innerHTML parses+executes
var tmp = document.createElement('div');
tmp.innerHTML = html;  // ← WC cart fragment
var fresh = tmp.firstElementChild;
if (fresh && node.parentNode) {
    node.parentNode.replaceChild(fresh, node);
}
```
Comment claims sandboxed; intermediate `tmp.innerHTML = html` parses + executes. `html` is WC AJAX response. If WC plugin ever injects unescaped content, this runs it. `innerHTML` always executes event-handler attributes (`onerror`, `onload`).

**Fix:**
```javascript
var parser = new DOMParser();
var doc = parser.parseFromString(html, 'text/html');
var fresh = doc.body.firstElementChild;
if (fresh && node.parentNode) {
    node.parentNode.replaceChild(document.adoptNode(fresh), node);
}
```

### Confirmed safe (non-issues)

- `contact.js:449` — `div.innerHTML` is a READ (HTML-entity-encoding helper pattern). Safe.
- `micro-interactions.js:127` — `HEART_SVG` module constant, no user data.
- `personalization.js:216` — `gridEl.innerHTML = ''` clear, then `appendChild(buildCard(product))` via `createElement`.

**Update cerebrum:** Claim "All innerHTML Uses Cleared" (obs #6378) is stale as of v1.1.2. Two active injectable usages in `smart-showcase.js` + `immersive-wc-bridge.js`.

---

## 5. Mixed Content + Transport

`http://` refs in theme-owned files:

| File | Line | Value | Risk |
|------|------|-------|------|
| `style.css:17` | License URI | `http://www.gnu.org/licenses/gpl-2.0.html` | None (metadata) |
| `inc/fastapi-client.php:34` | Localhost fallback | `http://localhost:8000` | See SEC-08 |
| `assets/js/lib/three-examples/loaders/RGBELoader.js:15` | Code comment | URL in comment | None |

**SEC-08 Low** — `inc/fastapi-client.php:34` hardcodes `http://localhost:8000` fallback. SSRF allowlist (`skyyrose_see_is_safe_url`) permits localhost only when `wp_get_environment_type() === 'local'` (L74). Functionally safe; could mask misconfigured env var on production.

**Fix:**
```php
if ( empty( $url ) ) {
    if ( WP_DEBUG ) {
        error_log( 'SkyyRose SEE: FastAPI URL not configured. Set SEE_FASTAPI_URL.' );
    }
    return '';
}
```

No `http://` external resources in CSS/JS/template HTML. `upgrade-insecure-requests` CSP directive present. **PASS.**

---

## 6. Cookie Security

**WC session cookie (platform-set):**
```
set-cookie: wp_woocommerce_session_...; expires=...; path=/; secure; HttpOnly
```
`Secure` + `HttpOnly` present. `SameSite` not explicit — browser default Lax. **PASS, SameSite absence Low.**

**`sr_ref` referral cookie (`inc/ajax-handlers.php:516–525`):**
```php
setcookie('sr_ref', $ref_code, time() + 30*DAY, COOKIEPATH, COOKIE_DOMAIN, is_ssl(), true);
```
`Secure` + `HttpOnly` correct. **Missing SameSite** — positional `setcookie()` API doesn't support it.

**`skyy_visitor` personalization cookie (`inc/personalization.php:47–57`):**
```php
setcookie($cookie_name, $hash, [
    'expires' => ..., 'path' => '/', 'secure' => is_ssl(),
    'httponly' => false,  // JS must read it
    'samesite' => 'Lax',
]);
```
Array syntax, `SameSite=Lax`. **PASS.**

**SEC-09 Low** — `sr_ref` missing `SameSite`. Fix:
```php
setcookie('sr_ref', $ref_code, [
    'expires'  => time() + (30 * DAY_IN_SECONDS),
    'path'     => COOKIEPATH,
    'domain'   => COOKIE_DOMAIN,
    'secure'   => is_ssl(),
    'httponly' => true,
    'samesite' => 'Lax',
]);
```

---

## 7. SSRF Defense

`inc/fastapi-client.php` — `skyyrose_see_is_safe_url()` (L49–83):
- Scheme allowlist: http, https
- Hostname blocklist: 169.254.169.254, metadata.google.internal
- DNS-resolved IP validation via `FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE`
- Localhost permitted only in `local` env

**SEC-10 Low** — DNS TOCTOU gap. `gethostbyname()` resolves at validation, `wp_remote_post()` resolves again at request. DNS rebinding can return different IPs. On WP.com hosting near-zero practical risk (egress controlled). Hardening: pass resolved IP via curl `resolve` option, OR restrict to explicit allowlist (api.skyyrose.co, devskyy.app only).

---

## 8. Subresource Integrity (SRI)

Self-hosted fonts confirmed — 19 woff2 in `assets/fonts/`, no Google Fonts CDN.

External CDN scripts in CSP allowlist (`inc/security.php:48`): `cdn.jsdelivr.net`, `cdnjs.cloudflare.com`, `cdn.babylonjs.com`, `cdn.elementor.com`, `ajax.googleapis.com`, `unpkg.com`. **No SRI hashes applied** to any `wp_enqueue_script/style` calls.

**SEC-11 Medium** — External CDN scripts without SRI. Compromised CDN → arbitrary JS in skyyrose.co context. Highest risk: `cdn.babylonjs.com`, `cdn.elementor.com`, `ajax.googleapis.com`.

**Fix (start with babylonjs.com):**
```php
add_filter('script_loader_tag', function($tag, $handle, $src) {
    $sri_map = ['babylonjs' => 'sha384-<hash>'];
    if (isset($sri_map[$handle])) {
        $tag = str_replace(' src=', ' integrity="' . $sri_map[$handle] . '" crossorigin="anonymous" src=', $tag);
    }
    return $tag;
}, 10, 3);
```
SRI requires version-pinning + hash refresh per CDN release.

---

## 9. WP.com Hosting File Permissions

Deploy log `mv: preserving permissions Operation not permitted` cosmetic. WP.com manages permissions platform-side. No world-writable paths theme-configurable. **Not a finding.**

---

## 10. Additional Hardening (Informational — In-Place Controls Verified)

- XML-RPC disabled (`inc/security.php:116–119`)
- WordPress version removed (generator meta, feed version, ?ver= for core)
- REST `/wp/v2/users` 403 unauth (`inc/security.php:322–336`)
- `?author=N` + author archives redirect home (L364–389)
- `DISALLOW_FILE_EDIT = true` (L399–401)
- Application passwords: only `manage_options` users (L409–416)
- Rate limiting: newsletter, incentive signup, mascot chat (20 req/min), add-to-cart (30/min)
- Honeypot on contact form

---

## Finding Summary

| ID | Sev | Title | File:Line | Blocker |
|----|-----|-------|-----------|---------|
| SEC-06 | HIGH | innerHTML static template in smart-showcase.js | `assets/js/smart-showcase.js:34,107,115` | No |
| SEC-07 | HIGH | innerHTML WC fragment parsing | `assets/js/immersive-wc-bridge.js:56` | No |
| SEC-02 | Med | CSP `'unsafe-inline'` in script-src | `inc/security.php:48` | No |
| SEC-05 | Med | HSTS includeSubDomains/preload stripped by WP.com | Platform | No |
| SEC-11 | Med | External CDN scripts without SRI | `inc/enqueue.php` | No |
| SEC-01 | Low | X-Frame-Options redundant w/ CSP frame-ancestors | `inc/security.php:71` | No |
| SEC-03 | Low | unpkg.com in script-src | `inc/security.php:48` | No |
| SEC-04 | Low | devskyy.app in connect-src | `inc/security.php:52` | No |
| SEC-08 | Low | http://localhost:8000 hardcoded fallback | `inc/fastapi-client.php:34` | No |
| SEC-09 | Low | sr_ref cookie missing SameSite | `inc/ajax-handlers.php:516` | No |
| SEC-10 | Low | SSRF DNS TOCTOU gap | `inc/fastapi-client.php:71–82` | No |

---

## Prioritized Fix Plan

**This sprint (HIGH):**
1. `inc/ajax-handlers.php:516` — `setcookie` array syntax + `SameSite=Lax` (SEC-09, 10-min)
2. `assets/js/smart-showcase.js:34` — `innerHTML` → `createElement` (SEC-06)
3. `assets/js/immersive-wc-bridge.js:56` — `innerHTML` → `DOMParser.parseFromString` (SEC-07)

**Next sprint (Medium):**
4. `inc/security.php:48` — remove `https://unpkg.com` if no live usage (SEC-03, 5-min)
5. `inc/enqueue.php` — SRI hashes starting with `cdn.babylonjs.com` (SEC-11)
6. WP.com support ticket for HSTS pass-through (SEC-05)

**Backlog:**
7. CSP nonce migration to remove `'unsafe-inline'` (SEC-02)
8. Verify `devskyy.app` in `connect-src` intent (SEC-04)
9. FastAPI SSRF IP-pinning hardening (SEC-10)
