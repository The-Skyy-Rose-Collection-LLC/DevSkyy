# Dashboard & Configuration Management

This skill provides comprehensive knowledge for managing admin dashboards, environment configurations, and multi-environment setups. It activates when users mention "dashboard configuration", "admin panel", "environment management", "multi-environment", "staging setup", "production config", or "deployment settings".

---

## Environment Configuration Strategy

### Environment Types
```
├── development     # Local development
├── preview         # Vercel preview deployments
├── staging         # Pre-production testing
└── production      # Live environment
```

### Environment Variables Structure

```bash
# .env.local (development - never commit)
NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:3000/api
WORDPRESS_API_URL=http://localhost:8080
WC_CONSUMER_KEY=ck_dev_key
WC_CONSUMER_SECRET=cs_dev_secret

# .env.staging (staging environment)
NODE_ENV=production
NEXT_PUBLIC_APP_URL=https://staging.example.com
NEXT_PUBLIC_API_URL=https://staging.example.com/api
WORDPRESS_API_URL=https://staging-cms.example.com
WC_CONSUMER_KEY=ck_staging_key
WC_CONSUMER_SECRET=cs_staging_secret

# .env.production (production - use Vercel env vars)
NODE_ENV=production
NEXT_PUBLIC_APP_URL=https://example.com
NEXT_PUBLIC_API_URL=https://example.com/api
WORDPRESS_API_URL=https://cms.example.com
WC_CONSUMER_KEY=ck_production_key
WC_CONSUMER_SECRET=cs_production_secret
```

## Vercel Environment Configuration

### Setting Up Environments
```bash
# Add variable for specific environment
vercel env add WORDPRESS_API_URL production
vercel env add WORDPRESS_API_URL preview
vercel env add WORDPRESS_API_URL development

# Pull env vars to local
vercel env pull .env.local

# List all variables
vercel env ls
```

### vercel.json Environment Config
```json
{
  "env": {
    "NEXT_PUBLIC_APP_URL": "https://example.com"
  },
  "build": {
    "env": {
      "NODE_ENV": "production",
      "ANALYZE": "false"
    }
  }
}
```

## Multi-Environment WordPress Setup

### wp-config.php Environment Handling
```php
// wp-config.php
define('WP_ENVIRONMENT_TYPE', getenv('WP_ENVIRONMENT_TYPE') ?: 'production');

switch (WP_ENVIRONMENT_TYPE) {
  case 'development':
    define('WP_DEBUG', true);
    define('WP_DEBUG_LOG', true);
    define('SCRIPT_DEBUG', true);
    break;
  case 'staging':
    define('WP_DEBUG', true);
    define('WP_DEBUG_LOG', true);
    define('SCRIPT_DEBUG', false);
    break;
  case 'production':
  default:
    define('WP_DEBUG', false);
    define('WP_DEBUG_LOG', false);
    define('SCRIPT_DEBUG', false);
    break;
}

// CORS for headless setup
define('HEADLESS_FRONTEND_URL', getenv('HEADLESS_FRONTEND_URL'));
```

## Configuration Files

### Runtime Config (next.config.js)
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Public runtime config (available client-side)
  publicRuntimeConfig: {
    apiUrl: process.env.NEXT_PUBLIC_API_URL,
    wordpressUrl: process.env.NEXT_PUBLIC_WORDPRESS_URL,
  },

  // Server runtime config (server-only)
  serverRuntimeConfig: {
    wordpressApiUrl: process.env.WORDPRESS_API_URL,
    wcConsumerKey: process.env.WC_CONSUMER_KEY,
    wcConsumerSecret: process.env.WC_CONSUMER_SECRET,
  },
}

module.exports = nextConfig
```

### Feature Flags Configuration
```typescript
// config/features.ts
export const featureFlags = {
  enableWooCommerce: process.env.NEXT_PUBLIC_ENABLE_WOOCOMMERCE === 'true',
  enableBlog: process.env.NEXT_PUBLIC_ENABLE_BLOG === 'true',
  enableReviews: process.env.NEXT_PUBLIC_ENABLE_REVIEWS === 'true',
  maintenanceMode: process.env.NEXT_PUBLIC_MAINTENANCE_MODE === 'true',
}

// Usage
if (featureFlags.enableWooCommerce) {
  // Show cart, checkout, etc.
}
```

## Admin Dashboard Patterns

### Dashboard Layout Structure
```typescript
// app/admin/layout.tsx
import { redirect } from 'next/navigation'
import { getSession } from '@/lib/auth'
import { AdminSidebar } from '@/components/admin/Sidebar'

export default async function AdminLayout({
  children
}: {
  children: React.ReactNode
}) {
  const session = await getSession()

  if (!session?.user?.isAdmin) {
    redirect('/login')
  }

  return (
    <div className="flex h-screen">
      <AdminSidebar />
      <main className="flex-1 overflow-auto p-8">
        {children}
      </main>
    </div>
  )
}
```

### Settings Management
```typescript
// app/admin/settings/page.tsx
import { getSettings, updateSettings } from '@/lib/settings'

export default async function SettingsPage() {
  const settings = await getSettings()

  async function saveSettings(formData: FormData) {
    'use server'
    await updateSettings({
      siteName: formData.get('siteName') as string,
      siteDescription: formData.get('siteDescription') as string,
      // ...
    })
  }

  return (
    <form action={saveSettings}>
      <input name="siteName" defaultValue={settings.siteName} />
      <textarea name="siteDescription" defaultValue={settings.siteDescription} />
      <button type="submit">Save Settings</button>
    </form>
  )
}
```

## Deployment Configuration

### Branch-Based Deployments
```json
// vercel.json
{
  "git": {
    "deploymentEnabled": {
      "main": true,
      "staging": true,
      "develop": false
    }
  }
}
```

### Production Checklist Config
```typescript
// config/deployment-checks.ts
export const deploymentChecks = {
  preDeployment: [
    { name: 'TypeScript compilation', command: 'npx tsc --noEmit' },
    { name: 'ESLint', command: 'npm run lint' },
    { name: 'Unit tests', command: 'npm test' },
    { name: 'Build', command: 'npm run build' },
  ],
  postDeployment: [
    { name: 'Homepage loads', url: '/' },
    { name: 'API health check', url: '/api/health' },
    { name: 'WordPress connection', url: '/api/health/wordpress' },
    { name: 'WooCommerce connection', url: '/api/health/woocommerce' },
  ],
}
```

### Health Check Endpoint
```typescript
// app/api/health/route.ts
import { NextResponse } from 'next/server'

export async function GET() {
  const checks = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV,
    version: process.env.NEXT_PUBLIC_VERSION || 'unknown',
    services: {
      wordpress: await checkWordPress(),
      woocommerce: await checkWooCommerce(),
    }
  }

  const isHealthy = Object.values(checks.services).every(s => s.status === 'healthy')

  return NextResponse.json(checks, {
    status: isHealthy ? 200 : 503
  })
}

async function checkWordPress() {
  try {
    const response = await fetch(`${process.env.WORDPRESS_API_URL}/wp-json`)
    return { status: response.ok ? 'healthy' : 'unhealthy' }
  } catch {
    return { status: 'unhealthy', error: 'Connection failed' }
  }
}

async function checkWooCommerce() {
  try {
    const response = await fetch(
      `${process.env.WOOCOMMERCE_API_URL}/wp-json/wc/v3/system_status?consumer_key=${process.env.WC_CONSUMER_KEY}&consumer_secret=${process.env.WC_CONSUMER_SECRET}`
    )
    return { status: response.ok ? 'healthy' : 'unhealthy' }
  } catch {
    return { status: 'unhealthy', error: 'Connection failed' }
  }
}
```

## Secrets Management

### Do NOT Commit Secrets
```gitignore
# .gitignore
.env
.env.local
.env.*.local
.vercel
```

### Use Vercel Secrets
```bash
# Store sensitive values as secrets
vercel secrets add wc-consumer-key "ck_xxx"
vercel secrets add wc-consumer-secret "cs_xxx"

# Reference in vercel.json
{
  "env": {
    "WC_CONSUMER_KEY": "@wc-consumer-key",
    "WC_CONSUMER_SECRET": "@wc-consumer-secret"
  }
}
```

## Autonomous Configuration Steps

When configuring environments:

1. **Identify required variables** - List all env vars needed
2. **Separate public vs private** - Use NEXT_PUBLIC_ prefix appropriately
3. **Configure Vercel environments** - Set vars for production, preview, development
4. **Verify WordPress CORS** - Ensure frontend URL allowed
5. **Test each environment** - Deploy and verify all connections
6. **Set up health checks** - Monitor service connectivity
7. **Document configuration** - Keep env.example updated
