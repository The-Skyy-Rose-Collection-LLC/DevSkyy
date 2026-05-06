# Frontend Codebase Digest — devskyy.app (Next.js 16 Dashboard)

**Generated:** 2026-05-05  
**Scope:** `/Users/theceo/DevSkyy/frontend/` — all source files excluding `node_modules/`, `.next/`, build artifacts, lockfiles  
**Runtime:** Next.js 16 + React 19, Node 22, deployed on Vercel (region iad1)

---

## 1. Architecture Overview

`devskyy.app` is an **internal operations dashboard** for the SkyyRose AI fashion pipeline — it is NOT the customer storefront (that is `skyyrose.co`, a separate WordPress/WooCommerce installation).

The dashboard sits at the center of a multi-system integration mesh:

```
                        ┌─────────────────────────┐
                        │   devskyy.app (Next.js)  │
                        │                          │
  Browser ◄────────────►│  App Router (RSC + CC)   │
                        │  TanStack Query v5        │
                        │  NextAuth v4 sessions     │
                        └───────────┬──────────────┘
                                    │
          ┌─────────────────────────┼──────────────────────────┐
          │                         │                          │
          ▼                         ▼                          ▼
  FastAPI backend          WordPress/WooCommerce         External providers
  (Python, port 8000)      (skyyrose.co via proxy)       (Gemini, OpenAI,
  REST + WebSocket          /api/wordpress/proxy          Stripe, Meshy,
  JWT auth                  injects Basic auth            Tripo, HF, etc.)
```

**Key architectural decisions:**
- **App Router** throughout, with `'use client'` directives on interactive components
- **React 19 `use(params)`** in dynamic routes for async param unwrapping
- **WordPress proxy pattern** — all WP REST calls route through `/api/wordpress/proxy` (Next.js route handler); WooCommerce credentials never reach the browser
- **Dual API client architecture** (architectural debt — see Gotchas)
- **BullMQ + Redis** for async job queues, accessed only at runtime (dynamic imports avoid build-time failures when Redis is absent)
- **Three.js** for 3D product visualization, wired through `@react-three/fiber` and `@react-three/drei`

---

## 2. Directory Structure

```
frontend/
├── app/                          # Next.js App Router root
│   ├── (storefront)/             # Route group: public storefront pages
│   │   ├── HomePage.tsx          # Client component, 549L — particles, parallax hero
│   │   └── page.tsx              # Server wrapper for HomePage
│   ├── admin/                    # Internal dashboard pages (protected by proxy.ts)
│   │   ├── layout.tsx            # Dashboard shell with sidebar
│   │   ├── page.tsx              # Dashboard overview
│   │   ├── round-table/          # LLM Round Table competition UI
│   │   ├── 3d-pipeline/          # 3D generation job runner
│   │   ├── assets/               # Asset library with bulk operations
│   │   ├── imagery/              # AI image generation pipeline
│   │   ├── qa/                   # QA report viewer
│   │   ├── jobs/                 # BullMQ job queue monitor
│   │   ├── elite-studio/         # Multi-agent creative studio
│   │   ├── marketing/            # Social media + mascot
│   │   ├── social-media/         # Per-platform publisher
│   │   ├── wordpress/            # WP sync + agent chat
│   │   ├── huggingface/          # HF Spaces manager
│   │   ├── vercel/               # Vercel deployment UI
│   │   ├── agents/               # Agent registry
│   │   ├── pipeline/             # Pipeline config hub
│   │   ├── monitoring/           # Health + uptime + memory
│   │   ├── analytics/            # Journey analytics
│   │   ├── journey-analytics/    # Conversion journey viewer
│   │   ├── conversion/           # Conversion pulse
│   │   ├── experience/           # Experience analytics
│   │   └── settings/             # App settings (5 tabs)
│   ├── api/                      # Next.js Route Handlers
│   │   ├── auth/[...nextauth]/   # NextAuth catch-all
│   │   ├── wordpress/proxy/      # SSRF-protected WP proxy
│   │   ├── products/             # Canonical catalog reader
│   │   ├── checkout/             # Stripe session creator
│   │   ├── jobs/                 # BullMQ queue interface
│   │   ├── pipeline-status/      # 8-pipeline status reporter
│   │   ├── v1/3d/status/         # Meshy+Tripo health check
│   │   ├── imagery/              # Image generation proxy
│   │   ├── mascot/               # Mascot job manager
│   │   ├── monitoring/health/    # Health endpoint
│   │   ├── social-media/publish/ # Platform publishers
│   │   ├── huggingface/          # HF Hub proxy
│   │   └── conversion/           # Analytics event collector
│   ├── checkout/                 # Stripe checkout page
│   ├── collections/[slug]/       # Static collection pages (generateStaticParams)
│   ├── login/                    # Auth page (standalone, rate-limited)
│   └── pre-order/                # Pre-order gateway
├── components/
│   ├── ui/                       # shadcn/ui "new-york" — 30+ primitives
│   ├── dashboard/                # Dashboard-specific (sidebar, headers, cards)
│   ├── collections/              # ProductCard, CollectionGrid, filters
│   ├── 3d/                       # LuxuryProductViewer, model loaders
│   ├── mascot/                   # MascotBubble state machine
│   └── three-viewer.tsx          # Full Three.js viewer (510L)
├── hooks/                        # Custom React hooks
│   ├── useWebSocket.ts           # Full-featured WS with JWT sanitization
│   ├── useAssets.ts              # Asset library state (24/page, bulk ops)
│   ├── useDebounce.ts            # Generic debounce
│   ├── useToggle.ts              # Boolean toggle
│   └── use-mobile.tsx            # 768px breakpoint detector
├── contexts/
│   └── AuthContext.tsx           # useReducer auth (localStorage 'auth_token')
├── lib/
│   ├── api.ts                    # ROOT MONOLITH (legacy — see Gotchas)
│   ├── api/                      # Modular API client (canonical)
│   │   ├── client.ts             # Base client (localStorage 'access_token')
│   │   ├── types.ts              # Shared types + Zod schemas
│   │   └── endpoints/            # Domain-grouped endpoint modules
│   ├── animations/               # Framer Motion variant library
│   ├── autonomous/               # RoundTableAutoTrigger + SelfHealingService
│   ├── catalog.ts                # Server-only CSV reader (walks 6 dirs up)
│   ├── fonts.ts                  # next/font/google declarations
│   ├── meshy/                    # Meshy 3D API wrapper
│   ├── pipeline-config/          # 8-pipeline registry + validators
│   ├── providers/                # QueryProvider (TanStack)
│   ├── queue/                    # BullMQ queue interface
│   ├── social-media/             # Platform config
│   ├── stores/                   # Zustand stores
│   │   └── cart-store.ts         # Cart (persist → localStorage 'skyyrose-cart')
│   ├── tripo/                    # Tripo v2 API wrapper
│   ├── utils.ts                  # cn() (twMerge + clsx)
│   └── wordpress/                # WP proxy client, agent client, sync service
├── e2e/                          # Older Playwright specs (separate implicit config)
│   └── auth.setup.ts             # Auth state setup for test runs
├── tests/e2e/                    # Active Playwright tests (playwright.config.ts)
│   ├── smoke.spec.ts             # Public route smoke tests
│   └── settings-page.spec.ts     # Admin settings tab tests
├── scripts/
│   └── deploy.ts                 # VercelDeployer class
├── proxy.ts                      # NextAuth JWT guard for /admin/* (NOT middleware.ts)
├── tailwind.config.ts            # Luxury palette, golden-ratio spacing
├── playwright.config.ts          # testDir: './tests/e2e', Desktop Chrome + iPhone 14
├── next.config.ts                # (standard Next.js config)
├── package.json                  # devskyy-dashboard v1.0.0
└── vercel.json                   # installCommand: npm install, regions: iad1
```

---

## 3. State Management

Three distinct state layers coexist:

### Global Persistent State
**Zustand** (`lib/stores/cart-store.ts`) with `persist` middleware:
- Key: `'skyyrose-cart'` in localStorage
- CartItem shape: `{ productId, productName, collection, size, price, quantity }`
- Operations: `addItem` (merges by productId+size), `removeItem`, `updateQuantity`, `clearCart`
- Selectors: `itemCount()`, `subtotal()`

### Server State / Data Fetching
**TanStack Query v5** (`lib/providers/query-provider.tsx`):
- `staleTime`: 30 seconds
- `retry`: 2
- `refetchOnWindowFocus`: false
- `useState(() => new QueryClient(...))` pattern to prevent shared state across SSR renders
- Wraps the entire app in `app/layout.tsx`

### Auth State
**React Reducer** (`contexts/AuthContext.tsx`):
- Actions: `AUTH_START`, `AUTH_SUCCESS`, `AUTH_FAILURE`, `LOGOUT`, `CLEAR_ERROR`
- Persists to `localStorage['auth_token']` **and** a cookie on login
- CRITICAL: key is `'auth_token'`, NOT `'access_token'` (which the modular API client uses)

### Local UI State
Standard `useState` throughout admin pages for:
- Form fields, modal open/close, selected tab, filter values
- WebSocket message history (capped at 100 messages in `useWebSocket.ts`)
- Asset selection sets in `useAssets.ts`

### WebSocket State
`useWebSocket.ts` manages connection state, message history, reconnect backoff — not in any global store. Specialized hooks `useRoundTableWS()` and `use3DPipelineWS()` wrap it with fixed channel names.

---

## 4. API Layer

### Modular API Client (canonical) — `lib/api/`

```
lib/api/
├── client.ts        # Base client: reads 'access_token' from localStorage
├── types.ts         # Zod schemas + TypeScript types for all API responses
└── endpoints/
    ├── agents.ts    # Agent registry + execution
    ├── assets.ts    # Asset CRUD + generation
    ├── imagery.ts   # Image generation
    ├── jobs.ts      # BullMQ job management
    ├── pipeline.ts  # 3D pipeline (uses RELATIVE URLs — /api/v1/3d)
    ├── products.ts  # Product catalog
    ├── threed.ts    # 3D model generation
    └── wordpress.ts # WP sync operations
```

**`lib/api/client.ts`** base pattern:
- Reads auth token from `localStorage['access_token']`
- `handleResponse<T>(schema)` — Zod `safeParse`, throws on failure
- `handleArrayResponse<T[]>(schema)` — soft skip on invalid items (returns partial array)
- All requests: `Authorization: Bearer <token>`, `Content-Type: application/json`

**Backend URL split:**
- All standard endpoints → `process.env.NEXT_PUBLIC_API_URL` (external FastAPI)
- 3D pipeline endpoints (`lib/api/endpoints/pipeline.ts`) → relative Next.js URLs (`/api/v1/3d/*`)

### Root Monolith — `lib/api.ts` (legacy, do not extend)

An older version of the entire API client duplicated in a single 700+ line file. Contains all the same types, schemas, and endpoint functions as `lib/api/`. Key difference: uses `API_URL` env var for 3D endpoints (external), which diverges from the modular client's relative URL approach.

### WordPress Proxy — `app/api/wordpress/proxy/route.ts`

- Receives calls from `lib/wordpress/proxy-client.ts` (`wpProxyFetch()`)
- SSRF protection: validates endpoint starts with `/wp/` or `/wc/`
- Injects `Authorization: Basic <base64(key:secret)>` before forwarding to `WORDPRESS_URL`
- Final URL form: `${WORDPRESS_URL}/index.php?rest_route=${endpoint}`

### Next.js Route Handlers

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/auth/[...nextauth]` | NextAuth session | NextAuth |
| `/api/wordpress/proxy` | WP REST proxy | Server env vars |
| `/api/products` | Canonical catalog (CSV) | None (public) |
| `/api/checkout` | Stripe checkout session | None |
| `/api/jobs` | BullMQ enqueue + stats | None |
| `/api/pipeline-status` | 8-pipeline health | None |
| `/api/v1/3d/status` | Meshy + Tripo health | None |
| `/api/imagery` | AI image generation | None |
| `/api/mascot` | Mascot job management | None |
| `/api/monitoring/health` | Uptime, memory, git SHA | None |
| `/api/social-media/publish` | Platform publishers | Server env vars |
| `/api/huggingface` | HF Hub proxy | Server env vars |
| `/api/conversion` | Analytics event bridge | None |

---

## 5. Auth & Authorization

### Session Auth (dashboard pages)
**NextAuth v4** (`app/api/auth/[...nextauth]/route.ts`):
- `CredentialsProvider` bridges to FastAPI OAuth2 JWT
- Sessions: 15-minute access tokens
- `proxy.ts` (NOT `middleware.ts` — Next.js 16 convention) guards `/admin/:path*`
- Failed auth → redirect to `/login?callbackUrl=...`

### Token Auth (API calls from client components)
**Dual system:**
1. `contexts/AuthContext.tsx` → stores token as `localStorage['auth_token']`
2. `lib/api/client.ts` → reads token from `localStorage['access_token']`
3. `app/login/page.tsx` → writes to `localStorage['access_token']` AND `localStorage['refresh_token']`

These three use different localStorage key names. `AuthContext` stores `'auth_token'`; the API client reads `'access_token'`. Components using `AuthContext` will have an **empty token** when calling API methods through `lib/api/client.ts` unless the user went through the `/login` page (which correctly writes `'access_token'`).

### WebSocket Auth
`useWebSocket.ts` sanitizes the JWT before adding it to the connection URL:
- Validates base64url format before sending
- Rejects on auth failure (WS close code 4001, no reconnect)

### WordPress Auth
Injected server-side by the proxy route handler. Browser never sees credentials.

---

## 6. Component System

### Design System
**shadcn/ui "new-york"** style built on Radix UI primitives:
- 30+ components in `components/ui/` (Button, Card, Dialog, Select, Tabs, etc.)
- CSS HSL variables for theming (`--primary`, `--secondary`, `--accent`, etc.)
- Dark mode forced: `html` element always has `class="dark"`
- No light mode toggle — this is a dark-only internal dashboard

### Brand Tokens (Tailwind)
```typescript
luxury: {
  'rose-gold': '#B76E79',
  'rose-dark': '#8B5465',
  charcoal:    '#1A1A1A',
}
spacing: {
  phi:   '1.618rem',   // Golden ratio unit
  phi2:  '2.618rem',   // phi²
  phi3:  '4.236rem',   // phi³
}
```

### Animation Library
`lib/animations/luxury-transitions.ts` — full Framer Motion variant set:
- Easings: `luxuryEasing.smooth/elegant/swift/bounce`
- Page transitions: `pageTransition`
- Product: `productReveal`, `productCard` (with hover/tap states), `staggerContainer`
- Text: `textReveal`, `textWord` (per-word stagger)
- Modal: `modalOverlay`, `modalContent`
- Infinite: `shimmer`
- Parallax: `parallaxScroll(speed)` (takes speed factor)
- Magnetic: `magneticHover`
- Hero: `heroTitle`, `heroSubtitle`, `heroCTA`
- Nav: `navMenu`, `navItem`

### Key Components

**`components/three-viewer.tsx`** (510L) — Full Three.js viewer:
- Collection-specific lighting configs (black_rose: night/silver, love_hurts: apartment/gold, signature: studio/white)
- Post-processing: Bloom + ToneMapping via `@react-three/postprocessing`
- Controls: fullscreen, screenshot, zoom, orbit rotation

**`components/3d/LuxuryProductViewer.tsx`** (247L) — Product 3D viewer:
- `PresentationControls` + `Stage` + `EffectComposer`
- Forces all mesh materials to metalness 0.9, roughness 0.1
- `AccumulativeShadows` + `RandomizedLight`

**`components/mascot/MascotBubble.tsx`** (314L) — 4-state machine:
- States: `minimized → walking-out → open → walking-back`
- Collection-aware greetings keyed by route segment
- Chat interface with suggestion chips
- NOT a chatbot widget — a full-body walk-on character

**`components/collections/ProductCard.tsx`** — Magnetic hover:
- `useMotionValue` + `useSpring` + `useTransform`
- rotateX/Y limited to ±5°

**`components/dashboard/app-sidebar.tsx`** (293L) — Full nav tree:
- Main: dashboard, round-table, 3d-pipeline, assets, qa, jobs
- Elite Studio section
- Marketing: imagery, social-media, mascot
- Analytics: monitoring, journey-analytics, conversion, experience
- Integrations: wordpress, huggingface, vercel, agents, pipeline
- Settings

**`components/dashboard/conversion-pulse.tsx`** (670L) — Real-time event simulation:
- Event types: `pre-order`, `add-to-cart`, `page-view`
- Per-collection color coding

---

## 7. Data Flow

### Product Catalog Flow (server-side)
```
wordpress-theme/.../data/skyyrose-catalog.csv
        │
        ▼
lib/catalog.ts (getCatalog, getProduct, getCollectionProducts)
  - server-only (uses node:fs)
  - walks up 6 directories to find CSV
  - caches by mtimeMs for hot-reload
        │
        ▼
app/api/products/route.ts
  - maps CatalogProduct → Product shape
  - adds status/badge/social derived fields
        │
        ▼
Client components via fetch('/api/products?...')
```

**CRITICAL:** `lib/catalog.ts` is server-only. Do NOT import it from `'use client'` components. The `/api/products` route handler is the correct boundary.

### Round Table Data Flow
```
Admin triggers competition
        │
        ▼
lib/autonomous/round-table-auto-trigger.ts (RoundTableAutoTrigger)
  - compete() → backend API
  - exponential backoff retry (maxRetries=3, 2s×2^attempt)
  - auto-publishes winner as WP post (not draft!)
  - records sync history in localStorage['wp-sync-history']
  - fires CustomEvents: 'wp-sync-success' / 'wp-sync-error'
        │
        ├── WebSocket updates → useRoundTableWS() → admin/round-table UI
        │
        └── lib/wordpress/sync-service.ts
              WordPressSyncService.syncRoundTableResult()
              - creates WP post with HTML leaderboard
              - winner banner: rose gold gradient
              - entry cards sorted by rank
```

### Image Generation Flow
```
Admin UI → /api/imagery (in-memory Map, LRU cap 500)
  Providers: gemini, imagen, flux, replicate
  Gemini model: gemini-2.0-flash-preview-image-generation
        │
        ▼
BullMQ queue ('process-image') → background worker
        │
        ▼
Result stored, accessible via asset library
```

### WordPress Sync Flow
```
Client component
  ↓
lib/wordpress/proxy-client.ts (wpProxyFetch)
  ↓
/api/wordpress/proxy (Next.js Route Handler)
  - SSRF validation: endpoint must start with /wp/ or /wc/
  - Injects Basic auth
  ↓
skyyrose.co/index.php?rest_route=${endpoint}
```

### 3D Pipeline Flow
```
Admin submits 3D job
  ↓
/api/v1/3d/* (Next.js route — relative URL)
  ↓
Meshy or Tripo (via lib/meshy/ or lib/tripo/)
  - dry-run mode when API key absent
  ↓
BullMQ queue ('generate-3d-asset') for async processing
  ↓
WebSocket updates → use3DPipelineWS() → admin/3d-pipeline UI
```

---

## 8. Testing

### E2E Testing (Playwright)
Two test directories with separate configs:

**Active** — `tests/e2e/` (referenced by `playwright.config.ts`):
- `playwright.config.ts`: `testDir: './tests/e2e'`, Desktop Chrome + iPhone 14 Pro, retries 2 on CI
- `smoke.spec.ts`: covers `/`, `/collections`, `/login`, `/pre-order`, `/checkout`, `/collections/signature`, `/collections/black-rose`, `/collections/love-hurts`. Includes console error check (ignores favicon). Mobile viewport test.
- `settings-page.spec.ts`: tests `devskyy.app/admin/settings` directly. Verifies 5 tabs (WordPress, Vercel, Autonomous, UI Preferences, System). Checks password inputs are hidden.

**Older** — `e2e/` (implicit config, separate from playwright.config.ts):
- `auth.setup.ts`: Two strategies — API auth first (POST `/api/v1/auth/token` form-encoded), UI login fallback. Saves `user.json` and `admin.json` auth state files.

**Gotcha:** The two directories have different config resolution. The `e2e/` directory specs won't run under the `playwright.config.ts` unless `testDir` is changed. Treat them as independent suites.

### Unit / Integration Tests
No unit test files were found in the frontend. Testing is Playwright-only for this workspace.

### Coverage
No coverage tooling configured in `package.json` for the frontend. Backend Python has `make test-cov`.

---

## 9. Build & Deployment

### Vercel Configuration (`vercel.json`)
```json
{
  "installCommand": "npm install",
  "regions": ["iad1"],
  "framework": "nextjs"
}
```
- `rootDirectory: frontend` in Vercel project settings → reads this `vercel.json`, NOT root `vercel.json`
- All API routes: `maxDuration: 60s`
- CORS: `Access-Control-Allow-Origin: https://skyyrose.co`
- Bakes `NEXT_PUBLIC_*` env vars at build time

**CRITICAL:** Use `npm`, NOT `pnpm`. Node 22 raises `ERR_INVALID_THIS` with pnpm on Vercel.

### Build Commands
```bash
npm run dev          # Development server
npm run type-check   # tsc --noEmit
npm run lint         # ESLint
npm run build        # Production build
```

### Environment Variables (required for full functionality)
```
# Backend
NEXT_PUBLIC_API_URL          # FastAPI backend URL
NEXT_PUBLIC_WS_URL           # WebSocket backend URL

# Auth
NEXTAUTH_SECRET              # NextAuth session signing
NEXTAUTH_URL                 # Full app URL

# WordPress
WORDPRESS_URL                # skyyrose.co base URL
WOOCOMMERCE_KEY              # WC consumer key
WOOCOMMERCE_SECRET           # WC consumer secret

# 3D Providers
MESHY_API_KEY                # Meshy 3D (dry-run if absent)
TRIPO_API_KEY                # Tripo v2 (dry-run if absent)

# Payments
STRIPE_SECRET_KEY            # Stripe (sk_ prefix)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

# AI
ANTHROPIC_API_KEY            # For social media LLM
GOOGLE_API_KEY               # Gemini image generation

# Social
INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_BUSINESS_ACCOUNT_ID
TIKTOK_ACCESS_TOKEN
TWITTER_API_KEY + TWITTER_API_SECRET + TWITTER_ACCESS_TOKEN + TWITTER_ACCESS_TOKEN_SECRET
FACEBOOK_ACCESS_TOKEN + FACEBOOK_PAGE_ID

# Infrastructure
REDIS_URL                    # BullMQ (optional — dynamic import)
HF_TOKEN                     # HuggingFace
```

### Deploy Script
`scripts/deploy.ts` — `VercelDeployer` class:
- Pre-deployment checks before invoking Vercel CLI
- Runs build step
- Wraps `vercel deploy --prod`

---

## 10. Key Patterns & Conventions

### Server Components vs Client Components
- Default: Server Components (no directive needed)
- Add `'use client'` when: using hooks, event handlers, browser APIs, WebSocket, Zustand
- Heavy interactive pages (3D viewer, round table, asset library) are all client components
- Static collection pages use `generateStaticParams()` with server-side catalog reads

### React 19 Async Params
Dynamic routes use the React 19 `use()` hook to unwrap `params`:
```typescript
// app/collections/[slug]/page.tsx
const { slug } = use(params) // NOT await params (React 19 convention)
```

### Zod Validation at API Boundary
```typescript
// Hard fail (handleResponse) — used for single objects
const schema = z.object({ ... })
const result = schema.safeParse(data)
if (!result.success) throw new Error(...)

// Soft skip (handleArrayResponse) — returns valid items, discards invalid
const items = rawArray.flatMap(item => {
  const r = schema.safeParse(item)
  return r.success ? [r.data] : []
})
```

### WordPress Proxy Pattern
All WP REST calls from browser components MUST go through `wpProxyFetch()` in `lib/wordpress/proxy-client.ts`. Never call `skyyrose.co` directly from client components — credentials would be exposed.

### Dry-Run Mode
Both Meshy and Tripo clients check for their API keys at initialization:
```typescript
if (!process.env.MESHY_API_KEY) {
  return { dryRun: true, mockData: ... }
}
```
Same pattern in social media publishers — real API calls only when env vars present.

### Circuit Breaker
`lib/autonomous/self-healing-service.ts`:
- Opens after 5 consecutive failures
- Enters half-open after 60s
- `retryWithBackoff()` adds ±20% jitter to avoid thundering herd

### BullMQ Queue Pattern
Dynamic import to avoid build-time Redis connection:
```typescript
// app/api/jobs/route.ts
const { addJob } = await import('@/lib/queue/queues')
```
4 queues: `generate-3d-asset`, `process-image`, `sync-wordpress`, `send-email`  
All: exponential backoff (5s base), 3 retries, keep 100 completed / 500 failed.

### Font Loading
`lib/fonts.ts` declares fonts via `next/font/google`:
- Playfair Display → `--font-playfair`
- Cormorant Garamond → `--font-cormorant`
- Space Mono → `--font-space-mono`
These match the brand fonts declared in the WordPress theme.

### Golden Ratio Spacing
Tailwind `spacing.phi` = 1.618rem, `phi2` = 2.618rem, `phi3` = 4.236rem. Used for luxury visual rhythm throughout dashboard layouts.

### Auto-Publish Pattern
`RoundTableAutoTrigger` publishes Round Table winners as live WordPress posts (status `publish`, not `draft`). This means every automated Round Table run can immediately create public content on skyyrose.co. Ensure this is intentional before running competitions in production.

---

## 11. Known Issues / Gotchas

### GOTCHA 1: Dual Authentication Token Keys
**Severity: High — causes silent auth failures**

Three different localStorage keys are used for the auth token across the codebase:
- `AuthContext.tsx` writes/reads `'auth_token'`
- `app/login/page.tsx` writes `'access_token'` and `'refresh_token'`
- `lib/api/client.ts` reads `'access_token'`

**Impact:** Components that use `AuthContext` for login state but call API methods through `lib/api/client.ts` will silently send empty Bearer tokens. API calls from these components will get 401 responses unless the user previously logged in through `/login` (not just through the NextAuth session).

**Fix needed:** Normalize to one key (`'access_token'`) in `AuthContext.tsx`, or route all token reads through a single helper.

### GOTCHA 2: Dual API Client Architecture
**Severity: High — schema drift, inconsistent behavior**

`lib/api.ts` (root monolith, ~700L) and `lib/api/` (modular directory) are parallel implementations with the same types, schemas, and endpoint functions. They diverge in one critical way:

- `lib/api.ts` uses `API_URL` (external) for 3D pipeline endpoints
- `lib/api/endpoints/pipeline.ts` uses relative URLs (`/api/v1/3d/*`) routing through Next.js

If a component imports from `lib/api.ts` instead of `lib/api/`, 3D pipeline calls will attempt to reach the external FastAPI directly, bypassing the Next.js route handler. This may work in some environments (if FastAPI is reachable) and silently fail in others (Vercel production where the backend may not be publicly accessible).

**Fix needed:** Delete `lib/api.ts` and migrate all imports to `lib/api/`. Run `grep -r "from.*lib/api'" --include="*.ts" --include="*.tsx"` to find importers.

### GOTCHA 3: `lib/catalog.ts` Is Server-Only
**Severity: Medium — causes runtime errors if misused**

`lib/catalog.ts` uses `node:fs` and will throw at runtime if imported from a `'use client'` component (Next.js will refuse to bundle `fs` in client bundles). The file walks up 6 directory levels to find the canonical CSV — this path resolution works from the Next.js server runtime but not from the browser.

**Safe pattern:** Always access product data through `/api/products` route handler. The route handler can call `getCatalog()` safely.

### GOTCHA 4: Round Table Auto-Publishes as Live Posts
**Severity: Medium — production content risk**

`RoundTableAutoTrigger.compete()` submits Round Table results to WordPress with `status: 'publish'`, not `'draft'`. Every automated Round Table run can create publicly visible content on skyyrose.co immediately, without manual review.

**Fix needed:** Change default `status` to `'draft'` in `sync-service.ts` unless live auto-publishing is intentional.

### GOTCHA 5: Playwright Test Directory Split
**Severity: Low — test coverage gap**

`playwright.config.ts` sets `testDir: './tests/e2e'`. Specs in `./e2e/` (the older directory) use a separate implicit config and won't run in the standard `npx playwright test` invocation. The `e2e/auth.setup.ts` auth state setup file is in the older directory and may not be wired to the active test suite.

**Fix needed:** Either consolidate to one directory or add a separate `playwright.config.e2e.ts` that references `./e2e/` explicitly.

### GOTCHA 6: `proxy.ts` Not `middleware.ts`
**Severity: Low — documentation/onboarding confusion**

Next.js 16 renamed the middleware file from `middleware.ts` to `proxy.ts`. This is a convention change not documented in the standard Next.js docs (which still reference `middleware.ts`). New contributors will look for `middleware.ts` and not find the auth guard.

**Note:** The file is at `frontend/proxy.ts` and protects `/admin/:path*`.

### GOTCHA 7: Imagery API In-Memory Store Not Persisted
**Severity: Low — data loss on restart**

`app/api/imagery/route.ts` uses an in-memory `Map` with LRU cap at 500 records. All generated image metadata is lost on server restart or Vercel function cold start. There is no database or Redis persistence for imagery job state.

**Fix needed:** Persist imagery job state to Redis (BullMQ store) or a database if job history must survive cold starts.

### GOTCHA 8: Client-Side Particles in Homepage
**Severity: Low — SSR safety pattern**

`app/(storefront)/HomePage.tsx` generates particle positions with `Math.random()` inside `useEffect` only (never during SSR). This prevents React hydration mismatches but means particles are invisible until client JS loads. This is intentional but fragile — any future SSR of particle data will cause hydration errors.

---

## Appendix: External Service Dependencies

| Service | Config Location | Dry-Run Available |
|---------|----------------|-------------------|
| FastAPI backend | `NEXT_PUBLIC_API_URL` | No |
| WordPress/WooCommerce | `WORDPRESS_URL` + keys | No |
| Stripe | `STRIPE_SECRET_KEY` | No (build-time lazy init) |
| Meshy 3D | `MESHY_API_KEY` | Yes |
| Tripo 3D | `TRIPO_API_KEY` | Yes |
| Gemini | `GOOGLE_API_KEY` | No |
| HuggingFace | `HF_TOKEN` | No |
| Instagram | `INSTAGRAM_ACCESS_TOKEN` | Yes (simulated response) |
| TikTok | `TIKTOK_ACCESS_TOKEN` | Yes (simulated response) |
| Twitter/X | `TWITTER_API_KEY` + 3 more | Yes (simulated response) |
| Facebook | `FACEBOOK_ACCESS_TOKEN` + ID | Yes (simulated response) |
| Redis/BullMQ | `REDIS_URL` | Yes (dynamic import skip) |

---

*Digest covers all source files in `frontend/` as of commit `8d5e640f8`. Files skipped: `node_modules/`, `.next/`, `*.lock`, build artifacts.*
