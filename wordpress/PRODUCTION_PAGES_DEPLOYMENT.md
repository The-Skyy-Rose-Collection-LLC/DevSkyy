# Production Pages Deployment Guide

Deploy Elementor templates and custom CSS to SkyyRose WordPress production pages.

## Overview

Two deployment methods are available:

| Method | Best For | Requirements |
|--------|----------|--------------|
| **Python Script** | REST API access, remote deployment | WordPress REST API enabled |
| **WP-CLI Script** | Full Elementor support, direct DB access | SSH access or local WP install |

## Quick Start

### Method 1: Python REST API (Remote)

```bash
# Set credentials
export WORDPRESS_URL='https://skyyrose.co'
export WORDPRESS_USERNAME='your-username'
export WORDPRESS_APP_PASSWORD='your-app-password'

# Dry run first
python scripts/create_wordpress_production_pages.py --dry-run

# Deploy
python scripts/create_wordpress_production_pages.py --deploy
```

### Method 2: WP-CLI (Full Elementor Support)

```bash
# Local WordPress
./scripts/wp-cli-deploy-templates.sh --dry-run --local /path/to/wordpress
./scripts/wp-cli-deploy-templates.sh --local /path/to/wordpress

# Remote via SSH
./scripts/wp-cli-deploy-templates.sh --ssh user@skyyrose.co:/var/www/html
```

## Pages Deployed

| Page | URL | Template | Description |
|------|-----|----------|-------------|
| Home | `/` | `home.json` | Hero section + collections grid |
| Experiences | `/experiences/` | `collections.json` | 3D experiences overview |
| Signature | `/experiences/signature/` | `signature.json` | Rose gold collection |
| Black Rose | `/experiences/black-rose/` | `black_rose.json` | Cosmic silver collection |
| Love Hurts | `/experiences/love-hurts/` | `love_hurts.json` | Crimson collection |
| About | `/about/` | `about.json` | Brand story + mission |

## Templates Location

```
wordpress/elementor_templates/
├── home.json          # 492 lines - Hero + collections
├── collections.json   # 493 lines - Experiences overview
├── signature.json     # 306 lines - Rose gold theme
├── black_rose.json    # 306 lines - Cosmic theme
├── love_hurts.json    # 306 lines - Crimson theme
├── about.json         # 666 lines - Brand story
└── blog.json          # 205 lines - Blog template
```

## CSS Injected

The following CSS files are combined and injected:

```
wordpress/skyyrose-immersive/assets/css/
├── luxury-design-system.css   # Design tokens (80+ CSS variables)
├── luxury-overrides.css       # WooCommerce customization
└── immersive.css              # 3D experience styling
```

### Key CSS Variables

```css
--rose-gold: #C9A962;
--pink-cloud: #B76E79;
--cosmic-silver: #C0C0C0;
--obsidian: #0A0A0A;
--font-display: 'Playfair Display';
--font-body: 'Inter';
```

## Troubleshooting

### REST API Meta Fields Not Updating

**Cause**: WordPress requires `register_post_meta()` with `show_in_rest => true` for meta writes.

**Solution**: Use WP-CLI method or add this to theme's `functions.php`:

```php
add_action('rest_api_init', function() {
    register_post_meta('page', '_elementor_data', [
        'show_in_rest' => true,
        'single' => true,
        'type' => 'string',
    ]);
});
```

### Rate Limiting (429 Errors)

**Cause**: WordPress.com or Jetpack rate limits API requests.

**Solution**: The Python script includes automatic 2-second delays between requests. If still hitting limits, increase `API_RATE_LIMIT_DELAY` in the script.

### Elementor Not Rendering

**Cause**: Elementor data not properly saved to `_elementor_data` meta.

**Solution**: Use WP-CLI method for direct database access:
```bash
./scripts/wp-cli-deploy-templates.sh --local /path/to/wordpress
```

## Verification

After deployment, verify each page:

1. **Visual Check**: Visit each URL in browser
2. **Elementor Editor**: Edit page → Should show template elements
3. **API Check**: `curl https://skyyrose.co/index.php?rest_route=/wp/v2/pages`

## Security Features

Both scripts include hardening:

- ✅ Input validation (regex patterns)
- ✅ File size limits (5MB templates, 1MB CSS)
- ✅ Rate limiting between API calls
- ✅ Correlation IDs for request tracing
- ✅ Safe JSON loading with error handling
- ✅ HTTPS enforcement
- ✅ Sanitized error messages

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/create_wordpress_production_pages.py` | Python REST API deployment |
| `scripts/wp-cli-deploy-templates.sh` | WP-CLI direct deployment |
| `scripts/deploy_wordpress_pages.py` | URL structure deployment only |
| `wordpress/elementor_templates/*.json` | Elementor templates |
| `wordpress/skyyrose-immersive/assets/css/*.css` | Custom CSS files |
