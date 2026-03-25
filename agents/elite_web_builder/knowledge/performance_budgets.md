# Performance Budgets

## Core Web Vitals Targets

| Metric | Target | Unit |
|--------|--------|------|
| LCP (Largest Contentful Paint) | < 2.5s | seconds |
| FID (First Input Delay) | < 100ms | milliseconds |
| CLS (Cumulative Layout Shift) | < 0.1 | unitless |
| INP (Interaction to Next Paint) | < 200ms | milliseconds |
| TTFB (Time to First Byte) | < 800ms | milliseconds |

## Lighthouse Score Targets

| Category | Minimum Score |
|----------|--------------|
| Performance | 80 |
| Accessibility | 95 |
| Best Practices | 90 |
| SEO | 90 |

## Asset Budgets

| Asset Type | Max Size | Notes |
|-----------|----------|-------|
| HTML | 50 KB | Gzipped |
| CSS (total) | 100 KB | Gzipped, critical CSS inlined |
| JavaScript (total) | 250 KB | Gzipped, deferred loading |
| Images (hero) | 200 KB | WebP, responsive srcset |
| Images (product) | 150 KB | WebP, lazy loaded |
| Web fonts (total) | 100 KB | WOFF2, font-display: swap |
| Total page weight | 1.5 MB | Including all assets |

## Font Loading Strategy

```css
@font-face {
  font-family: 'Playfair Display';
  font-display: swap;
  src: url('playfair.woff2') format('woff2');
}
```

- Use `font-display: swap` on ALL web fonts
- Preconnect to Google Fonts: `<link rel="preconnect" href="https://fonts.googleapis.com">`
- Subset fonts to used characters when possible

## Image Optimization

- Format: WebP primary, JPEG fallback
- Responsive: Use `srcset` with 3-4 sizes
- Lazy load: `loading="lazy"` on below-fold images
- Dimensions: Always specify `width` and `height` to prevent CLS
- Hero images: Preload with `<link rel="preload" as="image">`

## JavaScript Loading

- Critical: Inline in `<head>` (< 1 KB)
- Non-critical: `defer` attribute
- Heavy libraries (Three.js, GSAP): Dynamic import / conditional load
- No `async` on dependent scripts

## Caching Strategy

| Resource | Cache-Control | CDN TTL |
|----------|--------------|---------|
| HTML | no-cache | 5 min |
| CSS/JS (hashed) | max-age=31536000, immutable | 1 year |
| Images | max-age=86400 | 24 hours |
| Fonts | max-age=31536000, immutable | 1 year |
| API responses | max-age=300 | 5 min |
