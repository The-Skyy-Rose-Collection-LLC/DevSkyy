# Content Security Policy Root Cause Analysis

**Site**: https://skyyrose.co
**Date**: 2026-02-06
**Status**: ⚠️ BLOCKED - Requires WordPress.com Support

---

## Root Cause

WordPress.com injects Content Security Policy headers at the **Nginx/platform level** BEFORE WordPress/PHP executes.

This means:
- ✅ CSP is set at reverse proxy layer
- ❌ PHP cannot modify or override it
- ❌ WordPress filters don't apply (wpcom_csp_allowed_sources doesn't exist)
- ❌ Theme code cannot add domains
- ❌ `headers_list()` doesn't see the header (added after PHP)

---

## Current CSP (Platform-Level)

```
content-security-policy:
  default-src 'self';
  script-src 'self' 'nonce-XXXX' https://cdn.jsdelivr.net https://fonts.googleapis.com;
  style-src 'self' 'nonce-XXXX' https://fonts.googleapis.com;
  img-src 'self' data: https:;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.skyyrose.co;
```

**Issue**: Essential CDNs are missing, causing 109+ console errors.

---

## What We Tried (All Failed)

### Attempt 1: wpcom_csp_allowed_sources Filter
```php
add_filter('wpcom_csp_allowed_sources', [$this, 'add_domains'], 999);
```
**Result**: ❌ Filter doesn't exist or doesn't work
**Why**: CSP set before WordPress loads

### Attempt 2: header() Override
```php
header('Content-Security-Policy: ...');
```
**Result**: ❌ Overridden by platform
**Why**: Nginx adds CSP after PHP executes

### Attempt 3: Nonce Extraction
```php
$headers = headers_list();
preg_match("/'nonce-([^']+)'/", $headers, $matches);
```
**Result**: ❌ headers_list() doesn't see platform headers
**Why**: Added outside PHP context

---

## Required Domains (Not Currently Allowed)

### script-src
- `https://cdn.babylonjs.com` - 3D product viewer
- `https://stats.wp.com` - WordPress.com stats (**WordPress.com's own domain**)
- `https://widgets.wp.com` - WordPress.com widgets (**WordPress.com's own domain**)
- `https://s0.wp.com` - WordPress.com static assets (**WordPress.com's own domain**)
- `https://cdn.elementor.com` - Elementor page builder
- `https://cdnjs.cloudflare.com` - Common CDN libraries

### style-src
- `https://fonts-api.wp.com` - WordPress.com fonts API (**WordPress.com's own domain**)
- `https://s0.wp.com` - WordPress.com stylesheets (**WordPress.com's own domain**)
- `https://cdn.elementor.com` - Elementor styles

### font-src
- `https://fonts-api.wp.com` - WordPress.com fonts

### frame-src
- `https://widgets.wp.com` - WordPress.com widgets (**WordPress.com's own domain**)
- `https://jetpack.wordpress.com` - Jetpack features

**NOTE**: WordPress.com is blocking **its own domains** (stats.wp.com, widgets.wp.com, s0.wp.com, fonts-api.wp.com).

---

## Impact

- **109 console errors** on every page
- 3D product viewer completely non-functional
- Elementor page builder broken
- WordPress.com's own stats/widgets blocked
- Poor user experience
- SEO impact (browser console errors)
- Potential revenue loss (broken shopping features)

---

## ONLY Solution

**Contact WordPress.com Support** to add domains to platform-level CSP.

### Support Channels
1. **Email**: support@wordpress.com
2. **Live Chat**: https://wordpress.com/help/contact
3. **Support Ticket**: WordPress.com → Help → Contact Support

### What to Include
1. **Site URL**: https://skyyrose.co
2. **Plan**: Business
3. **Issue**: Platform CSP blocking required domains
4. **Required Domains**: (list from above)
5. **Impact**: 109+ console errors, broken features
6. **Reference**: This document + WPCOM-CSP-SUPPORT-REQUEST.md

---

## Alternative (If Support Refuses)

If WordPress.com support cannot/will not modify platform CSP:

### Option A: Migrate to Self-Hosted WordPress
- Full control over headers and CSP
- Can set custom CSP with all required domains
- No platform restrictions

### Option B: Remove Blocked Features
- Remove 3D viewer (use static images)
- Disable Elementor advanced features
- Use only WordPress.com-approved CDNs
- Accept limited functionality

### Option C: Accept CSP Violations
- Ignore console errors (not recommended)
- Users still see site (but with errors)
- Some features may not work
- Poor developer experience

---

## Why This Happened

WordPress.com manages hosting for security and performance. Part of this includes:
- Platform-level security headers (CSP, HSTS, X-Frame-Options)
- Nonce-based CSP for inline scripts/styles
- CDN domain whitelisting

**This is by design** to prevent XSS attacks and improve security. However, it creates restrictions for custom themes using external CDNs.

---

## Evidence

### Console Errors (Sample)
```
Refused to load the script 'https://cdn.babylonjs.com/babylon.js'
because it violates the following Content Security Policy directive:
"script-src 'self' 'nonce-XXXX' https://cdn.jsdelivr.net https://fonts.googleapis.com"

Refused to load the script 'https://stats.wp.com/e-202606.js'
because it violates the following Content Security Policy directive:
"script-src 'self' 'nonce-XXXX' https://cdn.jsdelivr.net https://fonts.googleapis.com"
```

### curl Proof
```bash
$ curl -sI "https://skyyrose.co/" | grep content-security-policy

content-security-policy: default-src 'self'; script-src 'self' 'nonce-d840e7b086'
https://cdn.jsdelivr.net https://fonts.googleapis.com; style-src 'self' 'nonce-d840e7b086'
https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self'
https://fonts.gstatic.com; connect-src 'self' https://api.skyyrose.co;
```

**Notable**: WordPress.com's own domains (stats.wp.com, widgets.wp.com) are missing.

---

## Timeline

1. **Day 1**: Deployed theme, saw 109 CSP errors
2. **Day 2**: Tried wpcom_csp_allowed_sources filter → Failed
3. **Day 3**: Tried header() override → Failed (overridden)
4. **Day 4**: Tried nonce extraction → Failed (headers_list() issue)
5. **Day 5**: Diagnosed root cause: Platform-level CSP, unfixable by theme
6. **Next**: Contact WordPress.com support for domain whitelisting

---

## Recommendation

**File WordPress.com support ticket immediately** using WPCOM-CSP-SUPPORT-REQUEST.md.

**Escalate** if first-line support says "not possible" - this is a legitimate business need and WordPress.com blocking its own domains (stats.wp.com, widgets.wp.com) is likely unintentional.

---

## Files Created

- `CSP-ROOT-CAUSE-ANALYSIS.md` (this file)
- `WPCOM-CSP-SUPPORT-REQUEST.md` (formatted support request)
- `inc/security-hardening.php` (attempts at theme-level fixes - all failed)

---

**Status**: Waiting for WordPress.com support response
