<claude-mem-context>

</claude-mem-context>

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

## Deployment

- Vercel project linked at `.vercel/project.json`
- `rootDirectory` is set to `frontend/` — Vercel reads `frontend/vercel.json`, not root `vercel.json`
- Node 22.x on Vercel. Use npm, not pnpm.
- Environment vars managed via `vercel env` — never hardcode API URLs or keys.

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
