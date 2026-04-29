# Next.js Lib — Agent Guide

## Isolated Workspace

**Your scope — read/write freely:**
```
frontend/lib/
```

**Adjacent reads allowed (do not write):**
```
frontend/app/              # read to understand how lib functions are consumed
frontend/components/       # read to understand what types components expect
frontend/tsconfig.json     # read TypeScript config
```

**Out of bounds — do not touch:**
```
frontend/app/              # separate agent scope
frontend/components/       # separate agent scope
wordpress-theme/           # completely separate system (WordPress.com)
```

`lib/` is the type and data foundation. Every other frontend agent depends on what you export here. Breaking changes here cascade everywhere — treat every export as a public API.

---

## Infrastructure

**Runtime**: TypeScript (strict mode), no React — these are pure TS modules
**Package manager**: npm (NOT pnpm)
**Rule**: No React imports, no JSX, no `'use client'` in any `lib/` file

---

## File Map

| File | Purpose |
|------|---------|
| `collections.ts` | `CollectionSlug` type + `COLLECTIONS` record — canonical frontend catalog |
| `types.ts` | Shared TypeScript interfaces (`Product`, `Collection`, `Filter`, etc.) |
| `utils.ts` | `cn()` (clsx/tw-merge) and general utility functions |
| `config.ts` | Environment-based config (API base URLs, feature flags) |
| `api/products.ts` | Product fetch functions |
| `api/imagery.ts` | Imagery pipeline API client |
| `api/analytics.ts` | Analytics data fetch |

---

## Permissions

You MAY:
- Add new utility functions to `utils.ts`
- Add new API client functions in `lib/api/`
- Add new TypeScript interfaces/types to `types.ts`
- Add new collection-specific helpers to `collections.ts`
- Extend `config.ts` with new environment variable mappings
- Add new `lib/api/` files for new backend integrations

You MUST NOT:
- Import React or write JSX in any `lib/` file
- Hardcode API URLs — always use `config.ts`
- Merge `collections.ts` and `types.ts` — keep concerns separated
- Add SKU data that isn't in `data/skyyrose-catalog.csv`
- Add any deprecated, renamed, or retired SKU to any array
- Make breaking changes to exported types without updating all consumers

---

## Safeguards — CRITICAL

### CollectionSlug — Non-Negotiable

This type is the frontend source of truth for all 4 collections. **It must always have exactly these 4 values:**

```typescript
export type CollectionSlug = 'black-rose' | 'love-hurts' | 'signature' | 'kids-capsule';
```

**Rules:**
- Never remove any of the 4 values
- Never rename any slug — they must match the CSV `collection` column values exactly
- If the CSV adds a 5th collection, add it here in the same commit
- `generateStaticParams()` in `app/` depends on this type — all 4 slugs must be served

### COLLECTIONS Record — Must Have All 4 Entries

```typescript
export const COLLECTIONS: Record<CollectionSlug, Collection> = {
    'black-rose': { ... },
    'love-hurts': { ... },
    'signature':  { ... },
    'kids-capsule': { ... }, // REQUIRED — never remove
};
```

After any edit to `collections.ts`, verify all 4 are present:
```bash
grep -c "'black-rose'\|'love-hurts'\|'signature'\|'kids-capsule'" frontend/lib/collections.ts
# Must output 4 (or more — multiple references per slug is fine)
```

### No Retired SKUs

Never add these to any array, object, or default in `lib/`:
- `lh-001`, `sg-004`, `sg-008`, `sg-010`
- `br-d01`, `br-d02`, `br-d03`, `br-d04`
- `sg-d01`, `sg-d02`, `sg-d03`, `sg-d04`

### Typed Responses — No `any`

```typescript
// WRONG
export async function fetchProducts(): Promise<any> { ... }

// CORRECT
export async function fetchProducts(): Promise<Product[]> { ... }
```

**Immediate fix mandate**: If you spot an `any` or retired SKU while working in `lib/`, fix it in the same commit.

---

## API Client Pattern

```typescript
// lib/api/products.ts
import { config } from '@/lib/config';
import type { CollectionSlug } from '@/lib/collections';
import type { Product } from '@/lib/types';

export async function fetchCollectionProducts(slug: CollectionSlug): Promise<Product[]> {
    const res = await fetch(`${config.apiBase}/collections/${slug}/products`, {
        next: { revalidate: 3600 }, // ISR — revalidate every hour
    });
    if (!res.ok) {
        throw new Error(`fetchCollectionProducts(${slug}): ${res.status} ${res.statusText}`);
    }
    return res.json() as Promise<Product[]>;
}
```

**Shared fetch wrapper pattern** (use when 3+ functions repeat the same fetch boilerplate):
```typescript
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${config.apiBase}${path}`, {
        next: { revalidate: 3600 },
        ...init,
    });
    if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
    return res.json() as Promise<T>;
}

export const fetchCollectionProducts = (slug: CollectionSlug) =>
    apiFetch<Product[]>(`/collections/${slug}/products`);
```

---

## Mandatory Quality Workflow

After every change to any `lib/` file, run ALL three steps in order.

### 1. Code Quality Check
```bash
cd frontend
npm run type-check   # Zero errors — lib/ is the type foundation; errors cascade everywhere
npm run lint         # Zero new errors
npm run build        # Full build to catch tree-shaking and missing-export issues
```

### 2. /simplify
Invoke the `code-simplifier` agent. In `lib/`, focus on:
- Consistent error handling across all API functions (extract shared wrapper if needed)
- Repeated fetch boilerplate (>2 functions = extract `apiFetch`)
- Overly complex type unions (simplify where possible without losing safety)

### 3. /verification-loop
```bash
cd frontend
npm run type-check

# Verify all 4 CollectionSlug values are present
grep -E "'black-rose'|'love-hurts'|'signature'|'kids-capsule'" lib/collections.ts | wc -l
# Must output at least 4

# Verify no retired SKUs snuck in
grep -E "lh-001|sg-004|sg-008|br-d0[1-4]|sg-d0[1-4]" lib/
# Must output nothing
```

---

## Do NOT

- Add `React` imports or JSX — `lib/` is pure TypeScript
- Hardcode any URL — use `config.ts` env vars
- Remove `'kids-capsule'` from `CollectionSlug` or `COLLECTIONS`
- Reference any retired SKU in default arrays or featured-product lists
- Add `any` type — TypeScript strict enforced throughout
- Add side effects at module level — only pure functions and constants
- Make breaking changes to shared types without updating all callers
