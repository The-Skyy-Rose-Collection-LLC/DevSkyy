# Next.js Components — Agent Guide

## Isolated Workspace

**Your scope — read/write freely:**
```
frontend/components/
```

**Adjacent reads allowed (do not write):**
```
frontend/lib/collections.ts   # import CollectionSlug type
frontend/lib/types.ts         # import shared interfaces
frontend/lib/utils.ts         # import cn() utility
frontend/app/                 # read to understand how components are used
```

**Out of bounds — do not touch:**
```
frontend/app/                 # separate agent scope
frontend/lib/                 # separate agent scope — request changes, don't make them
wordpress-theme/              # completely separate system (WordPress.com)
```

If a component requires a new type or API function, describe the requirement and request the lib agent creates it. Do not write files outside `frontend/components/`.

---

## Infrastructure

**Stack**: React 19, TypeScript strict, Tailwind CSS, shadcn/ui
**Design library**: shadcn/ui — the ONLY component library in this project
**Deploy target**: Vercel at `devskyy.app` (internal dashboard)
**Package manager**: npm (NOT pnpm)

**No competing component libraries** — no MUI, Chakra, Radix direct imports outside shadcn wrappers, Ant Design, or similar.

---

## Component Map

| Directory | Purpose |
|-----------|---------|
| `ui/` | shadcn/ui generated components (button, card, dialog, input, etc.) |
| `layout/` | Shell components (sidebar, header, page wrapper, breadcrumb) |
| `products/` | ProductCard, ProductGrid, ProductDetail |
| `collections/` | CollectionHero, CollectionFilter, CollectionNav |
| `imagery/` | ImagePipelineStatus, RenderPreview, GenerationQueue |
| `charts/` | Analytics charts (recharts wrapped) |
| `forms/` | Form components — react-hook-form + zod |

---

## Permissions

You MAY:
- Create new components in any subdirectory — follow existing naming conventions
- Modify existing components — maintain prop interface compatibility (no breaking changes)
- Add new shadcn/ui components via `npx shadcn@latest add [component]`
- Use Tailwind utility classes — no inline `style={{}}` props
- Add `'use client'` when the component needs hooks, events, or browser APIs
- Use `cn()` from `@/lib/utils` for conditional class composition

You MUST NOT:
- Install competing component libraries
- Use inline `style={{ }}` for anything achievable with Tailwind
- Skip TypeScript prop types — all props must be typed
- Add `any` to component props
- Ignore WCAG AA accessibility requirements
- Import from `wordpress-theme/` — separate system
- Break the prop interface of an existing component (add optional props, don't remove or rename required ones)

---

## Safeguards — Hard Rules

**Tailwind-only styling:**
```typescript
// WRONG
<div style={{ backgroundColor: '#B76E79', padding: '16px' }}>

// CORRECT — use design token class or Tailwind
<div className="bg-[#B76E79] p-4">
// Better — extend tailwind.config.ts with brand tokens
<div className="bg-rose-gold p-4">
```

**TypeScript strict props — every prop typed:**
```typescript
interface ProductCardProps {
    sku: string;
    name: string;
    price: number | null;       // null = "Coming Soon"
    collection: CollectionSlug; // import from @/lib/collections
    imageUrl: string;
    isPreorder?: boolean;
    className?: string;
}
```

**Conditional classes via `cn()`:**
```typescript
import { cn } from '@/lib/utils';

<button
    className={cn(
        'base-button-styles',
        isActive && 'ring-2 ring-offset-2',
        className
    )}
>
```

**WCAG AA — non-negotiable:**
- All interactive elements have a visible focus ring (`focus-visible:ring-2`)
- Color contrast ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- All images have meaningful `alt` attributes
- Icon-only buttons must have `aria-label`
- Form inputs must have associated `<label>` or `aria-label`

**Server vs Client**: Default to Server Component. Add `'use client'` only when using:
- React hooks (`useState`, `useEffect`, `useRef`, etc.)
- Event handlers (`onClick`, `onChange`, etc.)
- Browser APIs (`window`, `document`, `localStorage`)

**Immediate fix mandate**: If you spot an `any` type or missing `aria-label` while working, fix it in the same PR.

---

## Component Pattern

```typescript
// components/products/ProductCard.tsx
import { cn } from '@/lib/utils';
import type { CollectionSlug } from '@/lib/collections';

interface ProductCardProps {
    sku: string;
    name: string;
    price: number | null;
    collection: CollectionSlug;
    imageUrl: string;
    className?: string;
}

export function ProductCard({ sku, name, price, collection, imageUrl, className }: ProductCardProps) {
    const displayPrice = price === null ? 'Coming Soon' : `$${price}`;

    return (
        <article
            className={cn('rounded-lg overflow-hidden bg-card border', className)}
            aria-label={name}
        >
            <img
                src={imageUrl}
                alt={name}
                className="w-full aspect-square object-cover"
                loading="lazy"
            />
            <div className="p-4 space-y-1">
                <h3 className="font-semibold text-card-foreground">{name}</h3>
                <p className="text-sm text-muted-foreground">{displayPrice}</p>
            </div>
        </article>
    );
}
```

---

## Mandatory Quality Workflow

After every change to any component, run ALL three steps in order.

### 1. Code Quality Check
```bash
cd frontend
npm run type-check   # Zero errors required — components are imported everywhere
npm run lint         # Zero new errors
```

### 2. /simplify
Invoke the `code-simplifier` agent. In components, focus on:
- Prop drilling (>2 levels = context or composition)
- Repeated Tailwind class strings (extract to `cn()` variable)
- Components over 100 lines (consider splitting)
- Unnecessary `'use client'` directives

### 3. /verification-loop
```bash
cd frontend
npm run dev &
# Navigate to the page that renders the component
# Check at 375px mobile viewport
# Tab through every interactive element — focus ring must be visible
# Verify 0 console errors
# Run type-check to confirm no type regressions:
npm run type-check
```

---

## Do NOT

- Install component libraries that compete with shadcn/ui
- Use `style={{ }}` props when a Tailwind class exists
- Skip `aria-label` on icon-only buttons or unlabeled inputs
- Add `any` to component props — TypeScript strict throughout
- Import from `wordpress-theme/` — completely separate system
- Add `'use client'` to components that only render — Server Components are faster
- Remove or rename props that existing callers depend on
