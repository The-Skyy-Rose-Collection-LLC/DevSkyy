# Frontend Codemap

<!-- Generated: 2026-07-06 | Files scanned: frontend/app route tree (~30 dirs), proxy.ts, frontend/CLAUDE.md, src/ (63 files, legacy) | Token estimate: ~700 -->

**Active dashboard:** `frontend/` — Next.js 16 (App Router) + React 19, deployed to devskyy.app on Vercel (`cd frontend && npm run deploy`).

## App Router tree (frontend/app/)

| Area | Routes |
|---|---|
| Storefront (public) | `/`, `/checkout`, `/collections`, `/login`, `/pre-order` |
| Admin (`/admin/*`, NextAuth-gated) | 3d-pipeline, agents, assets, autonomous, catalog, catalog-search, conversion, elite-studio, experience, huggingface, imagery, jobs, journey-analytics, mascot, mcp, monitoring, pipeline, qa, renders, round-table, settings, social-media, tasks, vercel, wordpress |
| API routes (`/api/*`) | auth, catalog, checkout, conversion, huggingface, imagery, jobs, mascot, mcp, monitoring, pipeline(+`-status`), products, renders, settings, social-media, v1, wordpress |

Recently shipped: `/admin/catalog` (lossless CSV editor, SOT read-only) and `/admin/renders/review` (render QC queue).

## Auth gate — proxy.ts, not middleware.ts

`frontend/proxy.ts:27` exports `async function proxy()` — Next.js 16 renamed `middleware.ts` → `proxy.ts`. It checks the NextAuth JWT via `getToken()`: unauthenticated page requests redirect to `/login?callbackUrl=`, unauthenticated `/api/*` requests get a 401 JSON body (a redirect would corrupt a fetch). `config.matcher` (`proxy.ts:42-49`) gates `/admin/:path*` and every `/api/*` route **except** `/api/auth/*` (NextAuth itself) and `/api/checkout/*` (public storefront checkout). Two separate auth systems coexist and must not be conflated: **NextAuth v4** (`lib/auth.ts`, `getServerSession`/`useSession`, admin-only) and legacy **`AuthContext.tsx` + localStorage `access_token`** (storefront only; calling `useAuth()` on an admin page returns undefined context).

## Key libraries

| Concern | Location |
|---|---|
| API barrel | `lib/api.ts` → `lib/api/index.ts` — never import `lib/api/endpoints/*` directly |
| Catalog (server-only, `node:fs`) | `lib/catalog.ts`, `lib/catalog-server.ts` — crashes the build if imported from a `'use client'` component |
| Cart state | `lib/stores/cart-store.ts` (Zustand + `persist`) |
| Server data | TanStack Query (`@tanstack/react-query`) |
| UI components | shadcn/ui "new-york" style (`components.json`, `rsc: true`); icons `lucide-react` only |
| E2E tests | `tests/e2e/` (Playwright, `playwright.config.ts:4`) — **not** the legacy `frontend/e2e/`, which is not executed |

## Legacy: src/ (repo root) — separate TypeScript SDK, not wired to frontend/

63 files, builds via `config/typescript/tsconfig.json` (`rootDir: ../../src` → `dist/`). Contains Three.js collection experiences (`BlackRoseExperience.ts`, `SignatureExperience.ts`, `LoveHurtsExperience.ts`, etc.), cart/checkout/Stripe libs, `AgentService.ts`. Verified this pass: not imported anywhere under `frontend/` (only `frontend/node_modules` type-defs matched the search), and absent from both the root CLAUDE.md workspace table and `frontend/CLAUDE.md`. Treat as a standalone/legacy SDK, **not** the active dashboard's 3D layer — the live 3D experience is the WordPress theme's vanilla-Three.js `front-page.php` portals (see [wordpress.md](wordpress.md)).

## Related codemaps

[architecture.md](architecture.md) · [backend.md](backend.md) · [dependencies.md](dependencies.md)
