# Vercel Speed Insights Setup Guide

This guide explains how to use Vercel Speed Insights in the DevSkyy Enterprise Platform for monitoring application performance.

## Overview

Speed Insights is now fully integrated into the DevSkyy platform with:

- **Backend Performance Monitoring**: FastAPI middleware tracks API response times, error rates, and per-endpoint metrics
- **Client-Side Web Vitals**: Browser-based monitoring of Core Web Vitals (LCP, FID, CLS)
- **Metrics Dashboard**: Access performance metrics via dedicated endpoints
- **Vercel Integration**: Seamless integration with Vercel Speed Insights dashboard

## Prerequisites

- A Vercel account ([sign up for free](https://vercel.com/signup))
- The DevSkyy project deployed to Vercel
- The Vercel CLI installed: `npm install -g vercel`

## Backend: FastAPI Speed Insights

### Automatic Integration

The Speed Insights middleware is automatically integrated into the FastAPI application at startup. No additional configuration is required for basic functionality.

### Accessing Backend Metrics

#### Get Overall Performance Stats
```bash
curl https://your-devskyy-app.vercel.app/_vercel/speed-insights/metrics
```

Response:
```json
{
  "status": "healthy",
  "total_requests": 1234,
  "total_errors": 12,
  "error_rate_percent": 0.97,
  "avg_response_time_ms": 125.45,
  "min_response_time_ms": 10.2,
  "max_response_time_ms": 2450.8,
  "endpoint_count": 24,
  "timestamp": "2024-01-15T10:30:45.123456+00:00"
}
```

#### Get Per-Endpoint Metrics
```bash
curl https://your-devskyy-app.vercel.app/_vercel/speed-insights/endpoint-metrics
```

Response:
```json
{
  "endpoints": {
    "GET /api/v1/products": {
      "count": 456,
      "total_time": 45230.5,
      "errors": 2,
      "avg_time": 99.2
    },
    "POST /api/v1/orders": {
      "count": 234,
      "total_time": 52450.2,
      "errors": 8,
      "avg_time": 224.1
    }
  },
  "timestamp": "2024-01-15T10:30:45.123456+00:00"
}
```

#### Record Custom Events
```bash
curl -X POST https://your-devskyy-app.vercel.app/_vercel/speed-insights/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_metric",
    "value": 123.45,
    "type": "timing"
  }'
```

#### Health Check
```bash
curl https://your-devskyy-app.vercel.app/_vercel/speed-insights/health
```

## Frontend: Client-Side Speed Insights

### Installation

Speed Insights is already added as a dependency. To use it in your frontend application:

```bash
npm install @vercel/speed-insights
# or
pnpm install @vercel/speed-insights
# or
yarn add @vercel/speed-insights
```

### Basic Setup (React/Vue/Next.js)

#### For React Applications

```typescript
import { initializeSpeedInsights } from '../src/speed-insights';

function App() {
  useEffect(() => {
    initializeSpeedInsights();
  }, []);

  return (
    <div>
      {/* Your app content */}
    </div>
  );
}
```

#### For Vue Applications

```typescript
// In main.ts or main.js
import { initializeFullSpeedInsights } from './speed-insights';

initializeFullSpeedInsights();
```

#### For Next.js Applications

**pages/_app.tsx** (Next.js 12 and below):
```typescript
import { initializeSpeedInsights } from '../src/speed-insights';

function MyApp({ Component, pageProps }) {
  useEffect(() => {
    initializeSpeedInsights();
  }, []);

  return <Component {...pageProps} />;
}

export default MyApp;
```

**app/layout.tsx** (Next.js 13+):
```typescript
'use client';

import { initializeFullSpeedInsights } from '../src/speed-insights';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    initializeFullSpeedInsights();
  }, []);

  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

### Advanced Usage

#### Track Custom Metrics

```typescript
import { trackMetric } from '../src/speed-insights';

// Track custom timing
trackMetric('api_response_time', 234, {
  endpoint: '/api/v1/products',
  status: 'success'
});
```

#### Track Page Views

```typescript
import { trackPageView } from '../src/speed-insights';

router.afterEach((to) => {
  trackPageView(to.path, {
    title: to.name
  });
});
```

#### Track Events

```typescript
import { trackEvent } from '../src/speed-insights';

// Track when user completes an action
trackEvent('product_purchased', {
  productId: '12345',
  price: 99.99
});
```

#### Auto-Monitor Core Web Vitals

```typescript
import { monitorCoreWebVitals } from '../src/speed-insights';

// Automatically track LCP, FID, and CLS
monitorCoreWebVitals();
```

#### Filter Sensitive Data

```typescript
import { setBeforeSendCallback } from '../src/speed-insights';

setBeforeSendCallback((data) => {
  // Remove sensitive query parameters from URLs
  if (data.url) {
    data.url = data.url.replace(/[?&]token=[^&]*/g, '');
    data.url = data.url.replace(/[?&]apiKey=[^&]*/g, '');
  }
  return data;
});
```

## Vercel Dashboard

Once your application is deployed to Vercel and has received traffic:

1. Go to your [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your **DevSkyy** project
3. Click the **Speed Insights** tab
4. View your performance metrics and trends

### Metrics Available

- **Largest Contentful Paint (LCP)**: Time until the largest content element renders
- **First Input Delay (FID)**: Time between user input and page response
- **Cumulative Layout Shift (CLS)**: Visual stability during page load
- **Time to First Byte (TTFB)**: Server response time
- **Custom Metrics**: Any metrics you instrument in your application

## Environment Configuration

### Development vs. Production

Speed Insights middleware respects the `ENVIRONMENT` variable:

- **development**: Verbose logging enabled for debugging
- **production**: Optimized for performance with minimal logging

Set in `.env`:
```bash
ENVIRONMENT=production
```

### Disabling Speed Insights

To disable Speed Insights in specific environments:

In `main_enterprise.py`:
```python
speed_insights_middleware = create_speed_insights_middleware(
    enabled=os.getenv("ENVIRONMENT") == "production"
)
```

## Troubleshooting

### Speed Insights Script Not Loading

Check that the Speed Insights script loads correctly:

```bash
# Check if the script is being served
curl https://your-devskyy-app.vercel.app/_vercel/speed-insights/script.js
```

### No Data Appearing in Dashboard

1. Ensure your app is deployed to Vercel
2. Wait a few minutes after deployment
3. Visit your application to generate traffic
4. Check browser console for any errors
5. Verify Speed Insights is enabled in Vercel project settings

### High Error Rates Detected

Check the backend metrics endpoint:

```bash
curl https://your-devskyy-app.vercel.app/_vercel/speed-insights/metrics | jq '.error_rate_percent'
```

Review logs for error patterns:

```bash
vercel logs --follow
```

## Next Steps

- [Explore Speed Insights Metrics](https://vercel.com/docs/speed-insights/metrics)
- [Advanced Package Features](https://vercel.com/docs/speed-insights/package)
- [Privacy and Compliance](https://vercel.com/docs/speed-insights/privacy-policy)
- [Pricing and Limits](https://vercel.com/docs/speed-insights/limits-and-pricing)
- [Troubleshooting Guide](https://vercel.com/docs/speed-insights/troubleshooting)

## Support

For issues or questions about Speed Insights:

- [Vercel Documentation](https://vercel.com/docs/speed-insights)
- [DevSkyy Issues](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues)
