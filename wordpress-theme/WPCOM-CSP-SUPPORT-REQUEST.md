# WordPress.com CSP Support Request

**Site**: https://skyyrose.co
**Issue**: Content Security Policy blocking required CDN resources
**Date**: 2026-02-06

## Problem

WordPress.com's platform-level CSP is blocking essential CDNs and inline scripts/styles required by our luxury fashion e-commerce theme (SkyyRose 2025).

Current CSP header:
```
content-security-policy: default-src 'self';
  script-src 'self' 'nonce-XXXX' https://cdn.jsdelivr.net https://fonts.googleapis.com;
  style-src 'self' 'nonce-XXXX' https://fonts.googleapis.com;
  img-src 'self' data: https:;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.skyyrose.co;
```

## Required Domains

### script-src
- `https://cdn.babylonjs.com` - 3D product viewer (Three.js alternative)
- `https://stats.wp.com` - WordPress.com stats tracking
- `https://widgets.wp.com` - WordPress.com widgets
- `https://s0.wp.com` - WordPress.com static assets
- `https://cdn.elementor.com` - Elementor page builder
- `https://cdnjs.cloudflare.com` - CDN libraries

### style-src
- `https://fonts-api.wp.com` - WordPress.com fonts API
- `https://s0.wp.com` - WordPress.com stylesheets
- `https://cdn.elementor.com` - Elementor styles

### font-src
- `https://fonts-api.wp.com` - WordPress.com fonts

### frame-src
- `https://widgets.wp.com` - WordPress.com widgets
- `https://jetpack.wordpress.com` - Jetpack features

## Business Impact

- **109 console errors** on every page load
- 3D product viewer (core luxury feature) completely blocked
- Elementor page builder not functioning
- WordPress.com's own stats and widgets blocked
- Poor user experience, potential revenue loss

## Theme Configuration

Our theme implements proper security hardening:
- Nonce-based inline script/style handling
- X-Frame-Options, X-Content-Type-Options, HSTS
- Rate limiting, CSRF protection, XSS prevention
- OWASP Top 10 compliance

The theme is designed to work WITH WordPress.com's nonce-based CSP, but requires the above domains to be whitelisted.

## Request

Please add the above domains to the platform-level CSP for skyyrose.co.

Alternatively, if there's a `wpcom_csp_allowed_sources` filter or similar mechanism we can use, please provide documentation.

## Contact

- Username: skyyroseco
- Email: [your email]
- Plan: Business

## Technical Details

- Theme: SkyyRose 2025 (custom theme)
- PHP Version: 8.1+
- WordPress Version: Latest
- Active Plugins: Elementor, WooCommerce, Jetpack

Thank you for your assistance!
