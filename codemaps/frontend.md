# DevSkyy Frontend Codemap

> Freshness: 2026-03-03 | Next.js 16.1.6 | React 19 | Turbopack | App Router

## Routes (23 pages)

### Public
| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/(storefront)/page.tsx` | Homepage (hero, collections, pre-order CTA) |
| `/login` | `app/login/page.tsx` | Authentication |
| `/checkout` | `app/checkout/page.tsx` | Stripe checkout flow |
| `/pre-order` | `app/pre-order/page.tsx` | Pre-order gateway (6 products) |
| `/collections` | `app/collections/page.tsx` | All collections landing |
| `/collections/[slug]` | `app/collections/[slug]/page.tsx` | SSG collection pages |

### Admin (protected by NextAuth middleware)
| Route | Purpose |
|-------|---------|
| `/admin` | Dashboard home |
| `/admin/agents` | AI agents monitoring |
| `/admin/assets` | Asset management (upload, preview, batch) |
| `/admin/3d-pipeline` | 3D model generation pipeline |
| `/admin/pipeline` | Job queue & provider status |
| `/admin/imagery` | Imagery generation |
| `/admin/social-media` | Social scheduling & analytics |
| `/admin/qa` | QA review dashboard |
| `/admin/mascot` | Mascot generation |
| `/admin/monitoring` | System health & metrics |
| `/admin/round-table` | Multi-agent discussions |
| `/admin/wordpress` | WordPress sync & deployment |
| `/admin/huggingface` | HuggingFace Spaces |
| `/admin/vercel` | Vercel deployment & logs |
| `/admin/settings` | Configuration |

## API Routes (`app/api/`)

| Group | Endpoints | Purpose |
|-------|-----------|---------|
| `/api/v1/3d/*` | providers, generate/text, generate/image, status, jobs | 3D generation |
| `/api/social-media/*` | CRUD, generate, publish, schedule, analytics | Social media |
| `/api/products` | GET | Product catalog |
| `/api/imagery` | POST | AI imagery generation |
| `/api/wordpress/proxy/*` | POST | WordPress API proxy |
| `/api/checkout` | POST | Stripe checkout session |
| `/api/conversion` | POST | Conversion event tracking |
| `/api/monitoring/*` | health, metrics | Liveness, Prometheus |
| `/api/auth/[...nextauth]` | GET/POST | NextAuth.js endpoints |

## Components (60+)

| Group | Key Components |
|-------|---------------|
| `collections/` | CollectionHero, CollectionScene, ProductCard, ProductGrid, ProductQuickView |
| `3d/` | LuxuryProductViewer, RotatingCollectionLogo, three-viewer |
| `admin/` | AssetCard, AssetEditModal, UploadZone, JobCard, ProviderCard, ReviewDetail |
| `dashboard/` | app-sidebar, analytics-charts, conversion-pulse, StatsCard |
| `shared/` | LoadingState, ErrorState, EmptyState |
| `ui/` | 20+ Radix primitives (button, card, dialog, tabs, tooltip, etc.) |

## Libraries (`lib/`)

| Module | Purpose |
|--------|---------|
| `api/client.ts` | HTTP client (fetch-based) |
| `api/endpoints/` | assets, batch, health, pipeline, QA, round-table, social |
| `pipeline-config/` | 8 pipeline definitions (HF, imagery, LLM, payments, 3D, WP) |
| `meshy/`, `tripo/` | 3D provider API clients |
| `queue/` | BullMQ job queue |
| `wordpress/` | Proxy client, sync service, menu manager |
| `autonomous/` | Round-table auto-trigger, self-healing service |
| `stores/cart-store.ts` | Zustand cart state |
| `collections.ts` | Collection metadata (Black Rose, Love Hurts, Signature) |
| `animations/` | Framer Motion luxury transitions |

## State Management

| Tool | Usage |
|------|-------|
| TanStack Query | Server state (products, assets, jobs) |
| Zustand | Client state (cart) |
| Jotai | Atom-based state |
| NextAuth | Auth session |

## Key Dependencies

| Category | Packages |
|----------|----------|
| Framework | Next.js 16.1.6, React 19.2.3, TypeScript 5.9.3 |
| UI | Tailwind 3.4.17, Radix UI (20+ primitives), Framer Motion 12 |
| 3D | Three.js 0.172, @react-three/fiber, @google/model-viewer |
| AI | Vercel AI SDK 6.0, @ai-sdk/anthropic, @ai-sdk/openai, @google/genai |
| Commerce | Stripe 20.3.1 |
| Data | TanStack Query 5.90, Zustand 5.0, Zod 4.3 |
| Testing | Playwright 1.58 |
| Deploy | Vercel (KV, Blob, Analytics, Speed Insights) |

## Security

- NextAuth middleware protects `/admin/*`
- CORS for `skyyrose.co` only
- CSP, X-Frame-Options, X-XSS-Protection headers
- Permissions-Policy: camera, microphone, geolocation (self only)
- API routes: no-store cache, 60s max duration

## Deployment

- **Platform**: Vercel (iad1 region)
- **Node**: 22.x, npm
- **Build**: `next build` (Turbopack)
- **URLs**: devskyy.app, www.devskyy.app, devskyy.vercel.app
