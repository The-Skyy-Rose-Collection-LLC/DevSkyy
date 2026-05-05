# scripts/measurement/

**Status:** Phase 0.5 verifier set is built (2026-05-03). Baseline-capture and weekly-report scripts are still Phase 0.5.e deliverables and not yet implemented.

## Why this directory exists in Phase 0

`eval/measurement-access-requests.md` references this directory's scripts as the verification gate after the access packet is actioned. The verifiers don't try to provision anything — they only confirm that the credentials Corey added in the packet actually work end-to-end against each platform's read API.

## What's built

| Script | What it verifies | Required env |
|--------|-----------------|--------------|
| `verify-all-grants.js` | Aggregator — runs every verifier, prints PASS/FAIL/SKIP per row, exits 0 only when all pass | (delegates) |
| `verify-google-service-account.js` | JWT auth and access-token issuance using the service account | `GOOGLE_SERVICE_ACCOUNT_JSON` |
| `verify-ga4.js` | GA4 Data API `runReport` — returns last-30d sessions count | `GOOGLE_SERVICE_ACCOUNT_JSON`, `GA4_PROPERTY_ID` |
| `verify-gsc.js` | Search Console `searchAnalytics.query` — returns top 10 queries by clicks | `GOOGLE_SERVICE_ACCOUNT_JSON`, `GSC_SITE_URL` |
| `verify-gtm.js` | Tag Manager containers list + version_headers — confirms `GTM-XXXX` is reachable | `GOOGLE_SERVICE_ACCOUNT_JSON`, `GTM_ACCOUNT_ID`, `GTM_CONTAINER_ID` |
| `verify-meta.js` | Graph API `debug_token` — confirms System User token is valid + has `ads_read`/`business_management` | `META_SYSTEM_USER_TOKEN` |
| `verify-sentry.js` | Sentry projects API — confirms both `skyyrose-co` and `devskyy-app` projects exist | `SENTRY_AUTH_TOKEN_READ`, `SENTRY_ORG_SLUG` |

Shared infra in `_lib/`:

- `_lib/google-jwt.js` — single source of truth for `JWT` client construction + `authedFetch()`. All three Google verifiers consume this so a scope typo or JSON-parse bug is fixed in one place.
- `_lib/format.js` — exit-code constants (`EXIT_PASS=0`, `EXIT_FAIL=1`, `EXIT_MISSING_ENV=2`), colored PASS/FAIL/SKIP printers, and `requireEnv()` early-exit helper.

## Exit-code contract (read by the dispatcher)

| Code | Meaning | Dispatcher behaviour |
|------|---------|---------------------|
| 0 | PASS — credentials work, resource readable | Counted in PASS bucket |
| 1 | FAIL — credentials present but API call failed (auth scope, wrong ID, network, quota) | Counted in FAIL bucket; dispatcher exits 1 |
| 2 | MISSING_ENV — required env var not set | Counted in SKIP bucket; dispatcher exits 2 if no FAIL but at least one SKIP |

This split lets the operator distinguish "you skipped a step" (2) from "you broke a step" (1) without reading colour codes.

## Still to build (Phase 0.5.e)

- `scripts/measurement/pull-baselines.js` — populates `eval/baselines.md` from the verifiers
- `scripts/measurement/weekly-report.js` — Monday cron via `vercel.json`'s (to-be-added) `crons` block
- `scripts/measurement/loop-stats.js` — compound-learning meta-verification per WP §1.5 Layer 6

## Cross-references

- `eval/measurement-access-requests.md` — the packet whose `test_command` runs `verify-all-grants.js`
- `eval/silent-disable-audit.md` — the audit that surfaced this gap as instance S5
- `docs/SKYYROSE_WORDPRESS_PLAN.md` §WP-0.5 — Phase 0.5 deliverable specification
- `docs/SKYYROSE_V2_MASTER_PLAN.md` §5 Phase 0.5 — verification sweep specification

## Local testing

After Step 7 of the access packet:

```bash
vercel env pull .env.local                     # gitignored; delete after testing
node --env-file=.env.local scripts/measurement/verify-all-grants.js
```

Node ≥ 22 supports `--env-file` natively; no `dotenv` dependency required.
