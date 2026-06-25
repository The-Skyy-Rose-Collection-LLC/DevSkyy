# AGENTS.md — `frontend/` (Vercel — Next.js dashboard + API routes)

**Scope:** All code in `frontend/` — the Next.js 16 / React 19 dashboard at `devskyy.app`. Includes API routes (`frontend/app/api/`), admin pages (`frontend/app/admin/`), and client-side dashboard UI.

---

## Allowed agents/skills

| Agent / Skill | Why |
|---------------|-----|
| **vercel:ai-architect** | Claude Lab admin tool architecture (Phase 5.9), Vercel-native AI patterns |
| **vercel:deployment-expert** | Deploy, env management, route optimization |
| **design-taste-frontend** | RSC safety, Tailwind lock, viewport stability for dashboard UI |

## Forbidden

- **WP PHP edits.** Vercel and WordPress are isolated. WP work happens through the `inc/fastapi-client.php` bridge — never by directly modifying WP from a Vercel agent context.
- **Storing secrets in code, in `.env.local` committed to git, or in client-side bundles.** Secrets live in Vercel project env vars only. The `next.config.js` allowlist controls which env vars reach the client (default: none).
- **Calling paid APIs without rate limiting + cost ceiling.** FASHN, AIDesigner, Anthropic, Pinecone calls all need server-side guards (per V2 §1.2 and `eval/cost-cap-policy.md`).
- **Server Components doing client-only work** (e.g., `useState`, `useEffect`, `window` references). Default to RSC; opt into client (`'use client'`) only when needed.

## Mandatory per-edit workflow

Same 6-step workflow. Phase 0.5+ enforces fully.

**Lint step for this directory:**

```bash
cd frontend && npm run lint && npm run type-check
```

## Cross-boundary handoff protocol

If the task requires WP changes:

- WP needs a new endpoint to call → handoff to `inc/` agent for the REST route
- WP needs to display Vercel data → coordinate via `inc/fastapi-client.php` extension; sequence the work

Vercel work and WP work never merge in the same commit.

## Architecture invariants

- **Stateless Vercel.** Each route handler is stateless; persistent state lives in Pinecone, Postgres, Stripe, or Klaviyo — never in Vercel function memory.
- **HMAC-signed bridge.** All WP→Vercel calls carry a shared-secret HMAC header, validated server-side before any work.
- **Cron via `vercel.json` `crons` block.** No external schedulers. (Added Phase 0.5.e.)
- **Edge runtime preferred** for read-only routes (semantic search query, dashboard data fetch). Node runtime for write routes (Stripe webhooks, FASHN proxy with file uploads).

## Routes inventory (target — built across Phases 0.5 + 5)

| Route | Phase | Purpose |
|-------|-------|---------|
| `/admin/measurement` | 0.5.e | Live KPI dashboard |
| `/api/fashn-tryon` | 5.6 | AR proxy → FASHN with cost guard |
| `/api/semantic-search` | 5.7 | Pinecone query proxy |
| `/api/embed-products` | 5.7 | Cron: index WC products nightly |
| `/api/drop-queue` | 5.4 | WebSocket-backed live drop queue (Pusher) |
| `/admin/claude-lab/*` | 5.9 | Persistent prompt-eval admin tool |

## Performance budgets

- TTFB < 200ms on edge routes
- TTFB < 600ms on node routes (per WP §4.5)
- Bundle budget for `/admin/*` pages: < 300KB initial JS
- Cron timeout: 300s max (Vercel limit on Pro)

## Trusted references for this directory

- Next.js docs (nextjs.org/docs) — App Router patterns
- React 19 docs (react.dev) — RSC, Suspense, transitions
- Vercel docs (vercel.com/docs) — runtime selection, edge config, env vars, crons
- TanStack Query (if used) for client data fetching
- Tailwind CSS (tailwindcss.com/docs)
