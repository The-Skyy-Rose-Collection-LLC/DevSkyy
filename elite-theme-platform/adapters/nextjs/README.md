# Elite Theme Platform — Next.js Adapter

## What this adapter is

The Next.js adapter implements the six-method Elite Theme Platform contract
(`scaffold / build / deploy / monitor / commerceBind / heal`) for
**theme-type: dashboard**. This is M2 of the platform roadmap, following the
WordPress/WooCommerce reference adapter (M0).

Where the WordPress adapter emits PHP templates + WooCommerce hooks for a
customer-facing storefront (`skyyrose.co`), this adapter emits JSX/RSC +
Tailwind/CSS for a **Next.js 16 App Router dashboard** that exposes autonomous
control interfaces to the brand owner (`devskyy.app`).

These are two different theme-types on the same agnostic core:

| Axis              | WordPress (storefront)            | Next.js (dashboard)                        |
|-------------------|-----------------------------------|--------------------------------------------|
| Output language   | PHP templates + CSS/JS            | JSX/RSC + Tailwind                         |
| Deploy path       | `deploy-theme.sh` SFTP hot-swap   | `vercel deploy` via Vercel CLI             |
| Commerce-bind     | WooCommerce REST API              | Shopify / Medusa / Stripe SDK              |
| Monitor signals   | HTTP / size / PHP-err / canon     | HTTP / RSC console / canon / Core Web Vitals |
| Heal agent        | `theme-heal-doctor.md` PHP rules  | same agent, JSX/RSC rules                  |
| Design surface    | Holo cards, 3D portals, luxury CSS| Dark ops cockpit, data-dense, signal cards |

## Contract implementation

The adapter fulfills the six methods defined in `contract.ts`:

### `scaffold(brief)`
Produces the Next.js 16 App Router project skeleton:
- `app/admin/` route tree seeded from `brief.sections`
- `components/ui/` populated from the shadcn/ui registry entries named in `brief.componentKit`
- `lib/autonomy/` hexagonal data-port layer (types → mock-adapter → fs-adapter → index)
- `lib/api/endpoints/` module per domain (autonomy, monitoring, agents…)
- `hooks/` with polling hooks per domain

### `build(designSystem)`
Converts design-system tokens into the dashboard's Tailwind config and globals.css
utilities. Key outputs:
- Tailwind theme extension from `tokens.ts` `DASHBOARD_TOKENS`
- `luxury-text-gradient` + `font-display` utility classes in globals.css
- shadcn/ui component variants using `bg-*-500/10 text-*-400 border-*-500/30` color system
- framer-motion page-entry pattern (`opacity: 0, y: 12` → `opacity: 1, y: 0`)

### `deploy()`
Calls `vercel deploy --prod` from `frontend/`. Gated by the deploy keyhole:
the owner grants `STOPSHOW_ACK=1` once from the local terminal;
the agent never self-grants (STOP-AND-SHOW guardrail, per platform §4).

On Vercel, the `fs-adapter` is unavailable (`.claude/state/` is outside
`frontend/` and is not uploaded). The `index.ts` adapter selector detects this
via `fs.accessSync` and falls back to `mock-adapter` — the cockpit is non-blank
in every environment.

### `monitor()`
Produces structured signal data (`AutonomyCockpitData`) from:
- `tasks/heal-log.jsonl` — cycle verdicts, regressions, healed list
- `.claude/state/heal-knowledge.json` — KB signatures + recurrence trend
- `.claude/state/theme-health-baseline.json` — expected HTTP/size/canon baselines

Three signal layers (S1 = HTTP health, S2 = canon-drift, S3 = asset version)
feed the `StorefrontHealthPanel`. S4 is advisory-only.

### `commerceBind()`
For the dashboard theme-type this wires the **admin read surface** to commerce
data — product counts, order summaries, pipeline status — not the purchase flow.
The purchase flow is the WordPress storefront's responsibility. Full storefront
commerce-bind (Shopify/Medusa/Stripe) is in scope for M2 when the adapter
targets a customer-facing Next.js headless storefront.

### `heal(regression)`
Delegates to the `theme-heal-doctor` agent (same agent as WordPress, parametrized
for JSX rules). For the dashboard theme-type, regressions are dashboard-specific:
broken API routes, missing Suspense boundaries, RSC console errors, stale mock
data shipped to production, badge color drift.

## Cockpit: Storefront Autonomy page

The first concrete output of this adapter is `frontend/app/admin/storefront-autonomy/`.
It is a **monitoring cockpit for the WordPress self-heal loop** — a dashboard page
that surfaces the WordPress adapter's heal-log and knowledge base as a real-time
read-only control surface.

This cockpit is the canonical reference for all five section patterns:

1. `LoopStatusBar` — top-chrome ribbon (last verdict, cycle#, AUTO_DEPLOY flag)
2. `StorefrontHealthPanel` — S1/S2/S3 signal grid
3. `HealLogTimeline` — reverse-chron cycle list + recharts trend sparkline
4. `LearningKBPanel` — regression signatures + preventions
5. `DeployKeyholePanel` — dry manifest + version delta + deploy callout

See `component-kit.md` for the reusable vocabulary extracted from these five.

## Key architectural constraints

- **`'use client'` boundary**: page shell is a Server Component; `*Content`
  components carry the `'use client'` pragma. Suspense is installed at the page
  shell as a Cache Components guard (Next.js 16 `cacheComponents: true`).
- **`fs-adapter` is `server-only`**: `import 'server-only'` at the top of
  `lib/autonomy/fs-adapter.ts` prevents accidental client bundle inclusion.
  Build fails fast if violated.
- **`process.cwd()` not hardcoded paths**: fs reads resolve from `process.cwd()
  + '../'` (one level above `frontend/`) so the adapter is portable across
  machines. Never hardcode `/Users/theceo/…`.
- **mock-adapter is a production path, not a test stub**: it is the Vercel
  deployment read path. It must contain realistic non-empty data so the cockpit
  is meaningful when `heal-log.jsonl` is unreachable.
- **No deploy button in the dashboard**: the Deploy Keyhole panel renders the
  dry manifest and a callout banner only. Deploys run from the terminal with
  `STOPSHOW_ACK=1 bash scripts/deploy-theme.sh`. This is by design (platform §4).

## Files in this adapter

```
elite-theme-platform/adapters/nextjs/
├── README.md          — this file
├── contract.ts        — TypeScript interface stubs for all six methods
├── tokens.ts          — Dashboard design-token set (dark ops, data-dense)
└── component-kit.md   — Cockpit component vocabulary mapped to real frontend/ paths
```

## Relationship to the platform spec

Platform spec of record: `docs/superpowers/specs/elite-theme-platform.html`

This adapter is M2 ("queued #2") in the roadmap. M0 (WordPress reference + self-heal
loop) is in build as of 2026-05-29. M1 (extract agnostic core) is next. This adapter
seed pre-positions the Next.js contract so M1 extraction has a concrete target to
align to.

The learning knowledge base (`.claude/state/heal-knowledge.json`) is provider-neutral.
Fix-patterns for a11y, contrast, canon, and performance transfer from the WordPress
adapter. Each new adapter inherits accumulated intelligence — the platform compounds,
never resets.
