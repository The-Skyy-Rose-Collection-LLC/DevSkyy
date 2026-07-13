# Vercel "systemic failure" — corrected diagnosis (2026-07-12)

## TL;DR
The red Vercel check on the open PRs is a **false blocker**, not a code break.
There is **nothing to fix on `main`** — main's Vercel Production deploy is green.

## Evidence (authoritative, this session)
- `gh api repos/:owner/:repo/commits/main/status` → **`Vercel :: success :: Deployment has completed`**.
  Main's exact frontend code builds and deploys on Vercel.
- Failing PRs' frontend footprint (`gh pr view <n> --json files`):
  | PR | frontend files changed | total files |
  |----|------------------------|-------------|
  | #684 | 0 | 77 |
  | #672 | 0 | 94 |
  | #686 | 0 | 4 |
  | #689 | 0 | 6 |
  | #656 | 0 | 9 |
  | #648 | 0 | 5 |
  | #645 | 0 | 18 |
  | #690 | 1 (`frontend/CLAUDE.md` docs, not code) | 1 |
- `next.config.ts` `isVercel` guard present on 7/8 heads (guard=2, identical to main).
  The earlier "stale next.config" hypothesis is **disproven**.

## Conclusion
Identical frontend code cannot build-fail on **Preview** while succeeding on **Production**.
The Vercel red is a **Preview-environment / project-settings artifact**, most likely:
1. A required env var set for the **Production** environment but not **Preview**
   (`@t3-oss/env-nextjs` validates env at build time and throws if missing), and/or
2. Vercel **Deployment Protection** / plan limits on preview builds.

Neither is fixable by editing repo code or by any change to `main`.
Requires the **Vercel dashboard** (Project → Settings → Environment Variables →
add missing vars to the *Preview* scope; and/or Settings → Deployment Protection).

## Impact on the merge queue
For every PR that does **not** touch `frontend/`, the Vercel red is **noise** — it does
not reflect the PR's diff. The real gating signal for those PRs is the Python/test/lint
suite, not Vercel. After merge, main's Production Vercel re-runs and stays green (as now).

Frontend-touching PRs (some Dependabot bumps of frontend packages) still need a real
Preview signal — fix the Preview env first, or verify those locally with `cd frontend && VERCEL=1 npx next build`.

## Token note
`frontend/.env.local` has `VERCEL_TOKEN=` with an **empty value** (placeholder) — so
`vercel inspect --logs` cannot authenticate locally. Real preview logs need either a
valid token or the dashboard.
