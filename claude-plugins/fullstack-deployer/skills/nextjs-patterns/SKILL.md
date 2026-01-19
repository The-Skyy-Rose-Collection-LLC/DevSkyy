# Next.js Patterns

This skill provides comprehensive knowledge for Next.js development and deployment. It activates when users mention "next.js", "nextjs build", "next build error", "app router", "pages router", "server components", "API routes", "SSR", "SSG", "ISR", or encounter Next.js-related errors.

---

## Project Structure (App Router)

```
app/
├── layout.tsx          # Root layout
├── page.tsx            # Home page
├── loading.tsx         # Loading UI
├── error.tsx           # Error boundary
├── not-found.tsx       # 404 page
├── api/
│   └── route.ts        # API route handler
├── (routes)/
│   ├── products/
│   │   ├── page.tsx
│   │   └── [id]/
│   │       └── page.tsx
│   └── cart/
│       └── page.tsx
└── components/
    └── Header.tsx
```

## Server vs Client Components

### Server Components (Default)
```typescript
// app/products/page.tsx - Server Component
async function ProductsPage() {
  const products = await fetch('https://api.example.com/products')
    .then(res => res.json())

  return (
    <div>
      {products.map(p => <ProductCard key={p.id} product={p} />)}
    </div>
  )
}
```

### Client Components
```typescript
// components/AddToCart.tsx
'use client'

import { useState } from 'react'

export function AddToCart({ productId }: { productId: string }) {
  const [loading, setLoading] = useState(false)

  const handleAdd = async () => {
    setLoading(true)
    await fetch('/api/cart', {
      method: 'POST',
      body: JSON.stringify({ productId })
    })
    setLoading(false)
  }

  return <button onClick={handleAdd} disabled={loading}>Add to Cart</button>
}
```

## API Routes (App Router)

```typescript
// app/api/products/route.ts
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const products = await fetchProducts()
  return NextResponse.json(products)
}

export async function POST(request: Request) {
  const body = await request.json()
  const product = await createProduct(body)
  return NextResponse.json(product, { status: 201 })
}
```

### Dynamic API Routes
```typescript
// app/api/products/[id]/route.ts
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const product = await getProduct(params.id)
  if (!product) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }
  return NextResponse.json(product)
}
```

## Data Fetching Patterns

### Static Generation (SSG)
```typescript
// Generates at build time
export async function generateStaticParams() {
  const products = await getProducts()
  return products.map(p => ({ id: p.id }))
}
```

### Incremental Static Regeneration (ISR)
```typescript
// Revalidate every 60 seconds
export const revalidate = 60

async function Page() {
  const data = await fetch('https://api.example.com/data', {
    next: { revalidate: 60 }
  })
  return <div>{/* content */}</div>
}
```

### Server-Side Rendering (SSR)
```typescript
// Always fetch fresh data
export const dynamic = 'force-dynamic'

async function Page() {
  const data = await fetch('https://api.example.com/data', {
    cache: 'no-store'
  })
  return <div>{/* content */}</div>
}
```

## next.config.js Configuration

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode
  reactStrictMode: true,

  // Image optimization
  images: {
    domains: ['example.com', 'cdn.wordpress.org'],
    formats: ['image/avif', 'image/webp'],
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/old-page',
        destination: '/new-page',
        permanent: true,
      },
    ]
  },

  // Headers
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
        ],
      },
    ]
  },

  // Output configuration for deployment
  output: 'standalone',
}

module.exports = nextConfig
```

## Common Build Errors and Solutions

### "Module not found"
- Check import paths are correct
- Verify package is installed in dependencies
- Check tsconfig.json paths configuration

### "Hydration mismatch"
- Ensure server and client render same content
- Use `useEffect` for client-only code
- Add `suppressHydrationWarning` for dynamic content

### "Dynamic server usage"
- Page uses dynamic features (cookies, headers, searchParams)
- Add `export const dynamic = 'force-dynamic'` if intended
- Use static alternatives if possible

### "Build optimization failed"
- Check for circular dependencies
- Verify all imports resolve correctly
- Review webpack configuration in next.config.js

## Environment Variables

```bash
# .env.local (local development)
DATABASE_URL=postgresql://localhost:5432/db
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# .env.production (production)
DATABASE_URL=postgresql://prod:5432/db
NEXT_PUBLIC_API_URL=https://api.example.com
```

**Important:**
- `NEXT_PUBLIC_` prefix exposes variable to browser
- Without prefix, variable is server-only
- Never expose secrets with `NEXT_PUBLIC_` prefix

## Autonomous Recovery Steps

When encountering build errors:

1. **Read the full error message** - Note file path and line number
2. **Use Context7 to fetch Next.js documentation** with query like "nextjs [error type]"
3. **Check component type** - Should it be 'use client'?
4. **Verify imports** - All packages installed and paths correct?
5. **Review next.config.js** - Configuration valid?
6. **Clear cache and rebuild**: `rm -rf .next && npm run build`
7. **Check TypeScript errors**: `npx tsc --noEmit`
