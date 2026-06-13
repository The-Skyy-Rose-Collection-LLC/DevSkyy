# frontend/ — DevSkyy dashboard (Next.js 16, React 19)

Package: `devskyy-dashboard`. Internal admin UI for the AI agent pipeline. Deploys to Vercel at devskyy.app.
**This is NOT the customer storefront.** The storefront is the WordPress theme at skyyrose.co.

## Quick commands

```bash
cd frontend
npm install                           # use npm, NOT pnpm (ERR_INVALID_THIS on Node 22+)
npm run dev                           # dev server
npm run type-check && npm run lint    # verify before every commit
npm run build                         # production build
npm run e2e                           # Playwright suite
```

## Layout

- `app/` — Next.js 16 App Router routes
- `components/` — UI components (shadcn/ui-based per `components.json`)
- `contexts/` — React context providers
- `hooks/` — custom React hooks
- `lib/` — API clients, utilities, type defs
- `lib/collections.ts` — Collection + product data for the dashboard UI
- `e2e/` — Playwright tests
- `docs/` — area-specific docs (DASHBOARD_STATUS, DEPLOYMENT, IMPLEMENTATION_SUMMARY)

## Product / Collection Data

`lib/collections.ts` defines product data for the dashboard UI. It mirrors (but does not replace)
the canonical product catalog at `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`.

4 collections: `black-rose`, `love-hurts`, `signature`, `kids-capsule`.

**Retired SKUs — never re-add to collections.ts:**
- `sg-004` — retired 2026-04-26 (was a duplicate of `br-005`, same physical product)
- `lh-001`, `sg-008`, `sg-010`, `br-d01–d04`, `sg-d01–d04`

When a SKU is removed from the catalog CSV, also remove it from `lib/collections.ts`.

## Conventions

- TypeScript strict mode. No `any` without an inline comment explaining why.
- Server components by default; mark client with `"use client"` only when needed (state, effects, browser APIs).
- Tailwind via configured tokens only — do not add ad-hoc CSS files.
- API calls live in `lib/api/`. Components never call `fetch` directly.
- Form state via shadcn/ui + Zod. No new form libraries.

## Cache Components (`cacheComponents: true`)

`next.config.ts` enables Next.js 16's experimental Cache Components mode. Every request-time data reader **must** live inside a `<Suspense>` boundary or the build fails with `Error: Route "X": Uncached data was accessed outside of <Suspense>`. Affected hooks/calls:

- `usePathname()`, `useSearchParams()` (from `next/navigation`)
- `use(params)`, `use(searchParams)` (when unwrapping page props)
- `cookies()`, `headers()` (from `next/headers`)

**Two patterns**:

1. **Wrap at mount point** — best for shared chrome:
   ```tsx
   <Suspense fallback={null}>
     <AppSidebar />
   </Suspense>
   ```

2. **Internal split** — best for pages and reusable components. Rename the original function to `*Content`, export a wrapper:
   ```tsx
   export default function Page({ params }: Props) {
     return (
       <Suspense fallback={<PageSkeleton />}>
         <PageContent params={params} />
       </Suspense>
     );
   }
   function PageContent({ params }: Props) {
     const { id } = use(params); // dynamic data inside the boundary
     // ...
   }
   ```

For decorative chrome, `fallback={null}` is fine (the component would render nothing pre-hydration anyway). For data-heavy pages, the fallback is a skeleton matching content shape. Routes correctly using the pattern show as `◐ (Partial Prerender)` in the build's route table — that's the desired outcome.

Reference implementations (don't reinvent): `app/layout.tsx` (mascot mount-point wrap), `app/admin/layout.tsx` (sidebar mount-point wrap), `app/admin/elite-studio/operations/[id]/page.tsx` (canonical internal split with skeleton fallback).

## Deployment

- Vercel project linked at `.vercel/project.json`
- `rootDirectory` is set to `frontend/` — Vercel reads `frontend/vercel.json`, not root `vercel.json`
- Node 22.x on Vercel. Use npm, not pnpm.
- Environment vars managed via `vercel env` — never hardcode API URLs or keys.
- **`outputFileTracingRoot` and `turbopack.root` in `next.config.ts` are gated on `process.env.VERCEL`.** They set the workspace root one level above the project (because the repo has lockfiles at both `/` and `/frontend`). On Vercel that override breaks the post-build trace stage with a doubled-path `routes-manifest.json` ENOENT. Locally both lockfiles are visible so the override stays and prevents Turbopack/Webpack divergence. Don't remove the env gate without also removing the root lockfile. (Discovered PR #494, 2026-05-07.)

## Don't

- Don't use `pnpm` — use `npm` in this workspace.
- Don't hardcode the API base URL — use `lib/api/config.ts`.
- Don't ship without `npm run type-check && npm run lint` passing.
- Don't introduce a new state-management library — contexts + React Query is sufficient.
- Don't reference retired SKUs in collections.ts.

## Related

- Backend API: `api/dashboard.py` (at project root)
- Customer storefront: `wordpress-theme/skyyrose-flagship/` (completely separate, WordPress)
- Deployment config: `frontend/docs/VERCEL_PROJECT_CONFIG.md`
