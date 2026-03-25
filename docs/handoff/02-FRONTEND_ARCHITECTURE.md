# DevSkyy Dashboard — Frontend Architecture

## System Overview

```
Browser
  │
  ├── Public Pages (/, /collections, /pre-order)
  │     └── Static/SSG — no auth required
  │
  └── Admin Dashboard (/admin/*)
        │
        ├── middleware.ts ── NextAuth JWT check ── /login redirect
        │
        ├── layout.tsx ── SessionProvider + Sidebar + Header
        │
        └── page.tsx (per section)
              │
              ├── lib/api/endpoints/* ── fetchWithTimeout + Zod validation
              │     │
              │     ├── Backend API (NEXT_PUBLIC_API_URL)
              │     │   └── FastAPI @ localhost:8000
              │     │
              │     └── Next.js API Routes (/app/api/*)
              │         ├── /api/wordpress/proxy ── WooCommerce (server-side credentials)
              │         ├── /api/v1/3d/* ── 3D pipeline proxy
              │         ├── /api/social-media/* ── Social media proxy
              │         └── /api/monitoring/* ── Health + metrics
              │
              └── components/*
                    ├── ui/ ── shadcn/ui primitives
                    ├── dashboard/ ── analytics, sidebar, charts
                    ├── admin/ ── pipeline, qa, assets, wordpress
                    └── shared/ ── LoadingState, ErrorState, EmptyState
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | Next.js 16 (App Router) | Routing, SSR, API routes |
| UI | shadcn/ui + Radix UI | Accessible component primitives |
| Styling | Tailwind CSS 3.4 | Utility-first CSS |
| State (client) | Zustand 5 | Cart, UI preferences |
| State (server) | TanStack React Query 5 | API data caching, synchronization |
| Forms | React Hook Form + Zod | Validated form handling |
| Charts | Recharts 3.7 | Data visualization |
| Animation | Framer Motion 12 | Page transitions, micro-interactions |
| 3D | React Three Fiber + drei | Product viewer, 3D logos |
| Auth | NextAuth.js v4 | JWT sessions, credential login |
| Icons | Lucide React | 500+ icon set |

## Folder Structure

```
frontend/
├── app/
│   ├── admin/                  # 19 dashboard pages
│   │   ├── layout.tsx          # Admin shell (sidebar + auth)
│   │   ├── page.tsx            # Main dashboard
│   │   ├── agents/             # Agent management
│   │   ├── round-table/        # LLM competitions
│   │   ├── 3d-pipeline/        # 3D generation
│   │   ├── assets/             # Asset library
│   │   ├── imagery/            # Image pipeline
│   │   ├── monitoring/         # System health
│   │   ├── wordpress/          # WordPress CRUD
│   │   ├── vercel/             # Deployment management
│   │   ├── social-media/       # Social scheduling
│   │   ├── conversion/         # Conversion analytics
│   │   ├── journey-analytics/  # User behavior
│   │   ├── pipeline/           # ML pipeline
│   │   ├── jobs/               # Background jobs
│   │   ├── tasks/              # Task queue
│   │   ├── qa/                 # Quality assurance
│   │   ├── autonomous/         # Self-healing controls
│   │   ├── huggingface/        # HF integration
│   │   ├── mascot/             # Mascot management
│   │   └── settings/           # Admin settings
│   ├── api/                    # Next.js API routes (server-side)
│   ├── (storefront)/           # Public pages (collections, pre-order)
│   ├── login/                  # Auth page
│   ├── layout.tsx              # Root layout (fonts, providers)
│   └── globals.css             # CSS variables + design system
├── components/
│   ├── ui/                     # shadcn/ui (button, card, dialog, tabs, etc.)
│   ├── dashboard/              # Sidebar, stats cards, analytics charts
│   ├── admin/                  # Domain-specific (pipeline, qa, assets)
│   ├── 3d/                     # Three.js viewers, 3D logos
│   ├── collections/            # Product cards, grids, heroes
│   ├── shared/                 # Loading, Error, Empty states
│   └── navigation/             # Site nav
├── lib/
│   ├── api/
│   │   ├── client.ts           # HTTP utilities (fetch, auth headers, Zod validation)
│   │   ├── config.ts           # API_URL resolution
│   │   ├── schemas.ts          # Zod schemas for all API responses
│   │   ├── types.ts            # TypeScript types (inferred from schemas)
│   │   ├── errors.ts           # ApiError class
│   │   └── endpoints/          # 7 endpoint modules
│   ├── auth.ts                 # NextAuth configuration
│   ├── stores/                 # Zustand stores
│   ├── wordpress/              # WordPress proxy client + operations
│   └── providers/              # React Query provider
├── hooks/                      # Custom React hooks
├── middleware.ts               # Route protection (/admin/* → login)
├── tailwind.config.ts          # Design tokens
├── next.config.ts              # Framework config
└── vercel.json                 # Deployment config
```

## Authentication Flow

```
1. User visits /admin/*
2. middleware.ts checks for NextAuth JWT token
3. No token → redirect to /login?callbackUrl=/admin/...
4. User submits email + password on /login
5. NextAuth CredentialsProvider calls POST /api/v1/auth/token (backend)
6. Backend returns { access_token, refresh_token }
7. Tokens stored in NextAuth JWT (15-minute session)
8. Client reads session.accessToken for API calls
9. API client (lib/api/client.ts) attaches Bearer token to every request
```

**Key files**:
- `lib/auth.ts` — NextAuth config, token callbacks
- `middleware.ts` — Route protection matcher
- `app/api/auth/[...nextauth]/route.ts` — NextAuth handler

## Data Flow Pattern

Every admin page follows the same pattern:

```
Page Component
  └── calls lib/api/endpoints/[domain].ts
        └── uses fetchWithTimeout() from lib/api/client.ts
              ├── Attaches auth headers (Bearer token)
              ├── Sets 30s timeout (120s for uploads)
              └── Validates response with Zod schema
                    ├── Valid → returns typed data
                    └── Invalid → throws ApiError
```

**Input validation**: Done at the endpoint module level (max lengths, format checks) before the request is sent.

**Response validation**: Done with Zod schemas after the response arrives. Invalid items in arrays are skipped with a console warning rather than failing the entire request.

## Key Conventions

1. **One page per directory** — Each admin section is `app/admin/[section]/page.tsx`
2. **API calls through endpoint modules** — Never call `fetch()` directly in components
3. **Zod at the boundary** — All API responses validated against schemas in `lib/api/schemas.ts`
4. **Server-side secrets** — WordPress/WooCommerce credentials stay in API routes, never in client bundles
5. **shadcn/ui for primitives** — Don't install alternative component libraries
6. **Tailwind for styling** — No CSS modules, styled-components, or inline styles
7. **Immutable state** — Zustand stores use immutable update patterns
8. **Dark mode ready** — Use CSS variables from globals.css, not hardcoded colors

## Security Architecture

| Layer | Protection |
|-------|-----------|
| Routes | `middleware.ts` — JWT check on `/admin/*` |
| API calls | Bearer token from NextAuth session |
| WordPress proxy | Server-side credentials (never in browser) |
| SSRF | Proxy validates endpoints start with `/wp/` or `/wc/` |
| Headers | CSP, X-Frame-Options, XSS protection (vercel.json) |
| CORS | API routes allow `https://skyyrose.co` only |
| Input | Zod validation on all form submissions |

## Deployment

| Setting | Value |
|---------|-------|
| Platform | Vercel |
| Region | iad1 (US East) |
| Framework | Next.js |
| Root directory | `frontend/` |
| Build command | `next build` |
| Package manager | npm |
| Function timeout | 60s for API routes |
| Node version | 22.x |
