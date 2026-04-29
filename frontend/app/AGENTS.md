# Next.js App Routes — Agent Guide

## Isolated Workspace

**Your scope — read/write freely:**
```
frontend/app/
```

**Adjacent reads allowed (do not write):**
```
frontend/lib/              # import types and API functions from here
frontend/components/       # import UI components from here
frontend/package.json      # read to understand available scripts
frontend/tsconfig.json     # read to understand TypeScript config
```

**Out of bounds — do not touch:**
```
frontend/lib/              # separate agent scope — request changes, don't make them
frontend/components/       # separate agent scope — request changes, don't make them
wordpress-theme/           # completely separate system (WordPress.com hosted)
```

If a page requires a new component, describe it and request the components agent creates it. If it needs a new lib function, request the lib agent creates it. Do not reach across workspace boundaries.

---

## Infrastructure

**CRITICAL SEPARATION — Two independent systems:**
| System | URL | Stack | Deploy |
|--------|-----|-------|--------|
| Customer store | `skyyrose.co` | WordPress.com + WooCommerce | `scripts/deploy-theme.sh` or SFTP |
| Agent dashboard | `devskyy.app` | Next.js 16, React 19, Vercel | `cd frontend && npm run deploy` |

**Never mix API calls between these systems** without explicit integration code. They do not share a database, auth system, or session.

**Build stack:**
- Next.js 16, React 19, TypeScript (strict mode)
- Package manager: **npm** (NOT pnpm — ERR_INVALID_THIS on Node 22+)
- Node: 22.x
- Deploys to Vercel at `devskyy.app`

---

## Route Map

| Route | Purpose |
|-------|---------|
| `app/page.tsx` | Dashboard home |
| `app/layout.tsx` | Root layout — providers, fonts, nav shell |
| `app/collections/[slug]/page.tsx` | Per-collection product management |
| `app/products/page.tsx` | Product listing / catalog view |
| `app/imagery/page.tsx` | AI imagery pipeline UI |
| `app/3d/page.tsx` | 3D generation pipeline UI |
| `app/analytics/page.tsx` | Performance analytics |
| `app/api/` | API route handlers — server-side only, never import client-side |

---

## Permissions

You MAY:
- Create new pages and layouts in `app/` following Next.js App Router conventions
- Add `'use client'` directive where truly needed (browser APIs, hooks, event handlers)
- Add `loading.tsx`, `error.tsx`, `not-found.tsx` files alongside pages
- Add API routes in `app/api/` for new backend integrations
- Import from `frontend/lib/` and `frontend/components/`
- Add `generateStaticParams()` and `generateMetadata()` to any page

You MUST NOT (without explicit user confirmation):
- Use pnpm — use npm
- Change `rootDirectory` in Vercel config
- Add server actions that write to production WordPress/WooCommerce
- Deploy to Vercel without passing type-check + lint + build
- Expose secrets to the browser (only prefix with `NEXT_PUBLIC_` for truly public values)
- Import from `wordpress-theme/` — separate system

---

## Safeguards — Hard Rules

**TypeScript strict — no `any`:**
```typescript
// WRONG
const data: any = await fetchProducts();

// CORRECT
const data: Product[] = await fetchProducts();
```

**Server Components are the default** — add `'use client'` only when required:
```typescript
// Server Component (default — no directive)
export default async function CollectionPage({ params }: { params: { slug: CollectionSlug } }) {
    const products = await fetchCollectionProducts(params.slug); // server-side fetch ✓
    return <ProductGrid products={products} />;
}

// Client Component — only when using hooks/events/browser APIs
'use client';
export function FilterPanel({ onFilter }: { onFilter: (f: Filter) => void }) { ... }
```

**All data fetching belongs in `lib/`** — not inline in page files:
```typescript
// WRONG — inline fetch in page
const res = await fetch('/api/products'); // belongs in lib/api/

// CORRECT — import from lib
import { fetchCollectionProducts } from '@/lib/api/products';
const products = await fetchCollectionProducts(params.slug);
```

**Never hardcode URLs:**
```typescript
// WRONG
const res = await fetch('https://api.devskyy.app/products');

// CORRECT
import { config } from '@/lib/config';
const res = await fetch(`${config.apiBase}/products`);
```

**CollectionSlug must include all 4 values — never remove any:**
```typescript
// Defined in frontend/lib/collections.ts — verify this stays correct:
type CollectionSlug = 'black-rose' | 'love-hurts' | 'signature' | 'kids-capsule';
```

**Immediate fix mandate**: If you discover a type error or `any` in surrounding code, fix it in the same PR.

---

## Route Pattern

```typescript
// app/collections/[slug]/page.tsx
import type { Metadata } from 'next';
import { CollectionSlug } from '@/lib/collections';
import { fetchCollectionProducts } from '@/lib/api/products';
import { ProductGrid } from '@/components/products/ProductGrid';

interface PageProps {
    params: { slug: CollectionSlug };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
    return { title: `${params.slug} — SkyyRose Dashboard` };
}

export function generateStaticParams() {
    const slugs: CollectionSlug[] = ['black-rose', 'love-hurts', 'signature', 'kids-capsule'];
    return slugs.map(slug => ({ slug }));
}

export default async function CollectionPage({ params }: PageProps) {
    const products = await fetchCollectionProducts(params.slug);
    return (
        <main className="p-6">
            <ProductGrid products={products} collection={params.slug} />
        </main>
    );
}
```

---

## Mandatory Quality Workflow

After every change to any file in `app/`, run ALL three steps in order.

### 1. Code Quality Check
```bash
cd frontend
npm run type-check   # Zero TypeScript errors required — blocking
npm run lint         # Zero new errors; pre-existing warnings acceptable
npm run build        # Must succeed — build failure = deploy blocker
```

### 2. /simplify
Invoke the `code-simplifier` agent on the modified file(s). Focus on: unnecessary `'use client'` directives, data fetching moved inline that should live in `lib/`, and prop drilling that could be server-passed.

### 3. /verification-loop
```bash
cd frontend
npm run dev &
# Navigate to the affected route in the browser
# Verify: correct data renders, no console errors, no 404s on sub-routes
# Test loading state if the page has Suspense
# Test at 375px mobile viewport
curl -s -o /dev/null -w "%{http_code}" https://devskyy.app/
# Must return 200
```

---

## Do NOT

- Use pnpm — ERR_INVALID_THIS on Node 22+, always npm
- Add `'use client'` to a Server Component that doesn't need browser APIs
- Fetch data inline in page files — use `lib/api/` functions
- Hardcode any URL — use `config.ts` env vars
- Import from `wordpress-theme/` — these are completely separate systems
- Ship TypeScript `any` or `@ts-ignore` without an explanatory comment
- Deploy without passing all three quality checks
