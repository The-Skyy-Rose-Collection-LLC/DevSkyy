# Performance Budgets

## Core Web Vitals Targets
- LCP (Largest Contentful Paint): < 2.5s
- FID (First Input Delay): < 100ms
- CLS (Cumulative Layout Shift): < 0.1
- INP (Interaction to Next Paint): < 200ms

## PageSpeed Targets
- Mobile: > 80
- Desktop: > 90

## Asset Budgets
- Total page weight: < 1.5MB (mobile)
- JavaScript: < 300KB (compressed)
- CSS: < 100KB (compressed)
- Images: WebP/AVIF preferred, lazy load below fold
- Fonts: < 100KB total, font-display: swap

## Loading Strategy
- Critical CSS: inline in `<head>` (< 14KB)
- Scripts: async/defer, no render-blocking
- Images: lazy loading, responsive srcset
- Fonts: preload critical font, swap fallback
