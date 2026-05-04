# scripts/measurement/

**Status:** Phase 0.5 deliverable. Scripts in this directory are not yet built.

## Why this directory exists in Phase 0

`eval/measurement-access-requests.md` references this directory's scripts (`verify-all-grants.js`, `verify-google-service-account.js`, `verify-gsc.js`, `verify-gtm.js`, `verify-meta.js`, `verify-sentry.js`) as the verification gate after the access packet is actioned.

In Phase 0, only the dispatcher stub `verify-all-grants.js` exists — and it intentionally exits with code 1 plus an explicit message so anyone running it sees "not built yet" instead of "Cannot find module" (which is the silent-disable failure mode this audit pass eliminated).

## What gets built in Phase 0.5

| Script | What it verifies |
|--------|-----------------|
| `verify-all-grants.js` | Aggregator — runs every individual verifier, reports PASS/FAIL per grant, exits 0 only when all pass |
| `verify-google-service-account.js` | GA4 + GSC + GTM service account auth via `GOOGLE_SERVICE_ACCOUNT_JSON` env var |
| `verify-gsc.js` | Google Search Console API — returns indexed page count, top 10 queries by clicks |
| `verify-gtm.js` | Google Tag Manager API — returns container ID, last published version |
| `verify-meta.js` | Meta Business System User token — returns pixel events 30d + ad spend if applicable |
| `verify-sentry.js` | Sentry Auth Token — returns project list, last 30d issue count per project |

Plus the supporting infra in Phase 0.5.e:

- `scripts/measurement/pull-baselines.js` — populates `eval/baselines.md` from the verifiers
- `scripts/measurement/weekly-report.js` — Monday cron via `vercel.json`'s (to-be-added) `crons` block
- `scripts/measurement/loop-stats.js` — compound-learning meta-verification per WP §1.5 Layer 6

## Why the stub fails loudly

The original failure mode for missing scripts is "Cannot find module" with a Node stack trace — easy to miss, looks like an environment problem. The stub returns a one-paragraph explanation pointing at this README and the access packet. Same exit code (non-zero), but the operator now knows *why* and *what to do next*.

## Cross-references

- `eval/measurement-access-requests.md` — the packet whose `test_command` runs `verify-all-grants.js`
- `eval/silent-disable-audit.md` — the audit that surfaced this gap as instance S5
- `docs/SKYYROSE_WORDPRESS_PLAN.md` §WP-0.5 — Phase 0.5 deliverable specification
- `docs/SKYYROSE_V2_MASTER_PLAN.md` §5 Phase 0.5 — verification sweep specification
