# Collection Pages Deployment Guide

**Last Updated**: 2026-01-11
**Status**: Production Ready

---

## Overview

This guide covers deploying the interactive collection pages (SIGNATURE, LOVE_HURTS, BLACK_ROSE) to Vercel and embedding them in the WordPress site at skyyrose.com.

---

## Prerequisites

- Vercel account with SkyyRose organization access
- Vercel CLI installed: `npm i -g vercel`
- Git repository connected to Vercel
- WordPress admin access to skyyrose.com
- Environment variables configured

---

## Environment Variables

### Required Variables

Create `.env.local` in `frontend/` directory:

```bash
# WordPress API
NEXT_PUBLIC_WORDPRESS_URL=https://skyyrose.com
WORDPRESS_APP_PASSWORD=your_app_password_here

# Site Configuration
NEXT_PUBLIC_SITE_URL=https://app.devskyy.app

# Optional: Sentry (already configured)
NEXT_PUBLIC_SENTRY_DSN=your_sentry_dsn_here
SENTRY_AUTH_TOKEN=your_sentry_token_here
```

### Vercel Environment Variables

Configure in Vercel Dashboard → Project Settings → Environment Variables:

1. **Production Variables**:
   - `NEXT_PUBLIC_WORDPRESS_URL` = `https://skyyrose.com`
   - `NEXT_PUBLIC_SITE_URL` = `https://app.devskyy.app`
   - `WORDPRESS_APP_PASSWORD` = [WordPress app password]
   - `SENTRY_AUTH_TOKEN` = [Sentry token] (if using Sentry)

2. **Preview Variables**: Same as production

3. **Development Variables**: Can use localhost WordPress

---

## Deployment Steps

### Option 1: Automatic Deployment (Recommended)

Vercel automatically deploys when you push to the `main` branch:

```bash
git add .
git commit -m "feat: ready for production deployment"
git push origin main
```

Vercel will:
1. Detect the push to `main`
2. Install dependencies
3. Run Next.js build
4. Deploy to production
5. Send Slack/email notification

**Build Time**: ~3-5 minutes
**Deployment URL**: https://app.devskyy.app

### Option 2: Manual Deployment via CLI

```bash
# From project root
cd frontend

# Preview deployment (test before production)
vercel

# Production deployment
vercel --prod

# Check deployment status
vercel ls

# View logs
vercel logs [deployment-url]
```

### Option 3: Deploy Specific Branch

```bash
# Deploy feature branch for preview
git checkout feature/new-collection
git push origin feature/new-collection

# Vercel creates preview URL: https://devskyy-[hash].vercel.app
```

---

## Post-Deployment Verification

### 1. Check Deployment Status

```bash
vercel ls
```

Expected output:
```
Age  Deployment                          Status    Duration
1m   app-devskyy-xyz.vercel.app         Ready     2m 34s
```

### 2. Test Collection Pages

Visit each collection page and verify:

- ✅ https://app.devskyy.app/collections/signature
- ✅ https://app.devskyy.app/collections/love-hurts
- ✅ https://app.devskyy.app/collections/black-rose

**Test Checklist**:
- [ ] Page loads without errors
- [ ] 3D canvas renders (wait for "Loading 3D Experience..." to complete)
- [ ] Products load from WordPress API
- [ ] Filters work (size, color, price)
- [ ] Modal opens on product click
- [ ] Metadata visible in page source (View → Source)
- [ ] JSON-LD structured data present
- [ ] Images load with WebP/AVIF formats

### 3. Run Lighthouse Audit

```bash
# Install Lighthouse CLI
npm i -g lighthouse

# Run audit
lighthouse https://app.devskyy.app/collections/signature --view

# Expected scores:
# Performance: 90+
# Accessibility: 95+
# Best Practices: 100
# SEO: 95+
```

### 4. Test Mobile Responsiveness

Use Chrome DevTools → Device Toolbar to test:
- iPhone SE (375px)
- iPhone 12 Pro (390px)
- iPad (768px)
- Desktop (1920px)

---

## Custom Domain Configuration

### Current Setup

- **Vercel Domain**: `app.devskyy.app`
- **Custom Domain**: Configured via Vercel DNS

### Add New Domain (if needed)

1. **Vercel Dashboard**:
   - Go to Project Settings → Domains
   - Click "Add Domain"
   - Enter domain: `collections.skyyrose.com`
   - Click "Add"

2. **DNS Configuration**:
   - Add CNAME record in DNS provider:
     ```
     collections.skyyrose.com → cname.vercel-dns.com
     ```

3. **Verify Domain**:
   - Vercel automatically provisions SSL certificate
   - Wait 5-10 minutes for DNS propagation
   - Visit https://collections.skyyrose.com

---

## WordPress Embed Integration

### Method 1: Full-Page Embed (Recommended)

Create a new WordPress page for each collection:

1. **WordPress Admin** → Pages → Add New

2. **Page Setup**:
   - Title: "SIGNATURE Collection"
   - Slug: `collections/signature`
   - Template: Full Width (no sidebar)

3. **Add HTML Block**:
```html
<!-- SIGNATURE Collection Embed -->
<div class="collection-embed-container">
  <iframe
    src="https://app.devskyy.app/collections/signature"
    width="100%"
    height="100vh"
    frameborder="0"
    scrolling="auto"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen
    loading="lazy"
    title="SIGNATURE Collection - SkyyRose"
  ></iframe>
</div>

<style>
  .collection-embed-container {
    margin: -20px -20px 0 -20px; /* Remove WordPress padding */
    width: calc(100% + 40px);
    min-height: 100vh;
  }

  .collection-embed-container iframe {
    display: block;
    border: none;
  }

  /* Hide WordPress header/footer for immersive experience */
  body.page-template-full-width .site-header,
  body.page-template-full-width .site-footer {
    display: none;
  }
</style>
```

4. **Publish**: Click "Publish" button

5. **Test**: Visit `https://skyyrose.com/collections/signature`

### Method 2: Elementor Embed

If using Elementor:

1. **Edit Page with Elementor**

2. **Add HTML Widget**:
   - Drag "HTML" widget to page
   - Paste iframe code (same as Method 1)

3. **Configure Section**:
   - Section Settings → Layout → Content Width: Full Width
   - Section Settings → Advanced → Margin: 0px all sides
   - Section Settings → Advanced → Padding: 0px all sides

4. **Publish**: Click "Publish" button

### Method 3: Shortcode Embed

Create a custom shortcode in `functions.php`:

```php
// Add to theme's functions.php
function skyyrose_collection_embed($atts) {
    $atts = shortcode_atts(array(
        'collection' => 'signature', // default
        'height' => '100vh',
    ), $atts);

    $collection = sanitize_text_field($atts['collection']);
    $height = sanitize_text_field($atts['height']);
    $url = "https://app.devskyy.app/collections/{$collection}";

    return sprintf(
        '<iframe src="%s" width="100%%" height="%s" frameborder="0" scrolling="auto" allowfullscreen loading="lazy" title="%s Collection"></iframe>',
        esc_url($url),
        esc_attr($height),
        esc_attr(ucwords(str_replace('-', ' ', $collection)))
    );
}
add_shortcode('skyyrose_collection', 'skyyrose_collection_embed');
```

**Usage in WordPress Editor**:
```
[skyyrose_collection collection="signature" height="100vh"]
[skyyrose_collection collection="love-hurts" height="100vh"]
```

---

## Security Headers

The `vercel.json` configuration includes security headers:

- ✅ `X-Content-Type-Options: nosniff`
- ✅ `X-XSS-Protection: 1; mode=block`
- ✅ `Referrer-Policy: strict-origin-when-cross-origin`
- ✅ `Content-Security-Policy: frame-ancestors` for collection pages
- ⚠️ `X-Frame-Options` removed to allow WordPress embedding

**Collection pages** allow framing from:
- `https://skyyrose.com`
- `https://*.skyyrose.com`
- `'self'`

---

## Monitoring & Analytics

### Vercel Analytics

Enable in Vercel Dashboard:
1. Project Settings → Analytics
2. Enable Web Analytics
3. View real-time metrics and Core Web Vitals

### Sentry Error Tracking

Already configured via `next.config.mjs`:
- Errors automatically reported to Sentry
- Source maps uploaded for debugging
- Performance monitoring enabled

### Google Analytics (Optional)

Add to `frontend/app/layout.tsx`:
```typescript
<Script
  src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"
  strategy="afterInteractive"
/>
<Script id="google-analytics" strategy="afterInteractive">
  {`
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-XXXXXXXXXX');
  `}
</Script>
```

---

## Rollback Procedure

### Instant Rollback via Vercel Dashboard

1. **Vercel Dashboard** → Deployments
2. Find previous successful deployment
3. Click "..." → "Promote to Production"
4. Confirm promotion

**Rollback Time**: < 30 seconds

### Rollback via CLI

```bash
# List recent deployments
vercel ls

# Promote specific deployment
vercel promote [deployment-url] --prod
```

### Rollback via Git

```bash
# Find commit to revert to
git log --oneline

# Revert to previous commit
git revert HEAD

# Or reset to specific commit (careful!)
git reset --hard [commit-hash]
git push --force origin main
```

---

## Troubleshooting

### Build Failures

**Error**: `Module not found`
- **Fix**: Check import paths, run `npm install`

**Error**: `Type error: ... is not assignable`
- **Fix**: Run `npm run type-check` locally first

**Error**: `Out of memory`
- **Fix**: Increase Node memory in `package.json`:
  ```json
  "build": "NODE_OPTIONS='--max-old-space-size=4096' next build"
  ```

### Runtime Errors

**Error**: `CORS error when fetching WordPress API`
- **Fix**: Check `NEXT_PUBLIC_WORDPRESS_URL` environment variable
- **Fix**: Verify WordPress CORS headers configured

**Error**: `Three.js not rendering`
- **Fix**: Check browser console for WebGL errors
- **Fix**: Verify dynamic import working (check Network tab)

**Error**: `Images not loading`
- **Fix**: Check `next.config.mjs` `remotePatterns`
- **Fix**: Verify WordPress images accessible

### Iframe Embedding Issues

**Error**: `Refused to display ... in a frame`
- **Fix**: Check `Content-Security-Policy` header in `vercel.json`
- **Fix**: Verify domain in `frame-ancestors` directive

**Error**: `Mixed content warning`
- **Fix**: Ensure WordPress site uses HTTPS
- **Fix**: Update `NEXT_PUBLIC_WORDPRESS_URL` to use `https://`

---

## Performance Optimization Checklist

Post-deployment optimization tasks:

- [ ] Run Lighthouse audit (target: 90+ performance)
- [ ] Check Core Web Vitals in Google Search Console
- [ ] Verify bundle sizes: `ANALYZE=true npm run build`
- [ ] Test image loading (WebP/AVIF formats)
- [ ] Verify Three.js lazy loading (Network tab)
- [ ] Test on 3G network (Chrome DevTools)
- [ ] Monitor Vercel Analytics for real-user metrics
- [ ] Create Open Graph images (1200x630):
  - `/public/images/collections/signature-og.jpg`
  - `/public/images/collections/love-hurts-og.jpg`

---

## Continuous Integration

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Type check
        run: cd frontend && npm run type-check

      - name: Build
        run: cd frontend && npm run build

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## Support & Resources

- **Vercel Docs**: https://vercel.com/docs
- **Next.js Deployment**: https://nextjs.org/docs/deployment
- **Lighthouse CLI**: https://github.com/GoogleChrome/lighthouse
- **SkyyRose Support**: support@skyyrose.com

---

**Deployment Status**: ✅ Production Ready
**Last Deployment**: [Date]
**Deployed By**: [Name]
**Git Commit**: [Hash]
