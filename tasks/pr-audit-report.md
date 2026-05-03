# PR Audit Report — DRY-RUN
**Generated:** 2026-04-29 | **Repo:** The-Skyy-Rose-Collection-LLC/DevSkyy | **Default branch:** main

---

## Top Concerns

- **CI is broken for ALL human PRs.** Both #467 and #468 (SkyyRoseLLC author) show 20–21 CI failures across every workflow — Lint, Python Tests, Security Gate, CodeQL, Frontend Tests, WordPress Theme, Vercel. The failures start at the earliest jobs (lint, secrets scan) which means downstream jobs are cascade-failing. Root issue likely a CI config regression, not code failures. **Investigate before merging anything.**
- **Secrets Scan is failing on every PR.** Security Gate's `🔑 Secrets Scan` and `📦 Dependency Review` fail on both human PRs and nearly all dependabot PRs. If this is a legitimate finding (vs. a workflow config error) it must be resolved before any merge.
- **48 dependabot PRs are piling up with UNKNOWN mergeability.** None can be assessed for conflicts until CI is fixed and GitHub re-evaluates mergeability. The stacking is hiding real security patches (cryptography, pillow, socket.io-parser, handlebars, tar, etc.) behind green-field noise.
- **PR #467 (VisionAudit hardening) is superseded by the main branch.** Per git log, `fix/vision-audit-stage-15-hardening` changes were merged into `main` directly (commits `b72bb4cc8`, `79f07ad86`, `9049ad885`). PR #467 may be a stale open PR for work already landed — verify and close if confirmed.
- **No SAFE_MERGE or APPROVED PRs exist.** Zero PRs meet the auto-merge bar. Every single PR has at least one CI failure.

---

## Per-PR Table

| # | Title | Author | Class | CI | Review | Age (days) | Recommendation |
|---|-------|--------|-------|----|----|-----|----------------|
| 468 | feat(pipeline): wire PG checkpointing, real LangGraph, Claude ADK + immersive routes | SkyyRoseLLC | `BLOCKED_CI` | FAIL (20) | NONE | 0 | Fix CI, then review — this is the Phase B2-C3 work just opened by the user. Do NOT self-merge. |
| 467 | fix(audit): harden Stage 1.5 region normalization and VisionAuditAgent | SkyyRoseLLC | `BLOCKED_CI` | FAIL (21) | NONE | 0 | Verify if already merged into main. If yes, close. If no, fix CI and review. |
| 465 | deps(python)(deps-dev): bump the dev-dependencies group | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 2 | Batch with other python dev-dep updates. |
| 464 | bump protobufjs 7.5.4→7.5.5 in /skyyrose | dependabot | `DEPENDABOT_BATCH` | FAIL (16) | NONE | 6 | Security-relevant — protobuf. Batch with #457. |
| 463 | bump flatted 3.3.3→3.4.2 in /frontend | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 7 | Batch with #417. |
| 462 | bump basic-ftp 5.2.0→5.3.0 in /frontend | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 7 | Batch with frontend deps. |
| 461 | bump @modelcontextprotocol/sdk 1.25.3→1.26.0 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 7 | Batch with npm deps. |
| 459 | bump cryptography 46.0.5→47.0.0 (security group) | dependabot | `DEPENDABOT_BATCH` | FAIL (16) | NONE | 9 | **SECURITY PATCH** — cryptography security group. Fast-track after CI fixed. |
| 457 | bump protobufjs 7.5.4→7.5.5 in /frontend | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 10 | Security-relevant — protobuf. Batch with #464. |
| 456 | bump pillow 12.1.1→12.2.0 in /mcp_servers | dependabot | `DEPENDABOT_BATCH` | FAIL (16) | NONE | 12 | Security-relevant — Pillow CVEs. Batch with #452, #451. |
| 455 | bump fastify 5.8.1→5.8.5 in /skyyrose | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 14 | Batch with #454. |
| 454 | bump fastify 5.7.1→5.8.5 | dependabot | `DEPENDABOT_BATCH` | FAIL (16) | NONE | 14 | Batch with #455. |
| 452 | bump pillow 12.1.1→12.2.0 in /skyyrose | dependabot | `DEPENDABOT_BATCH` | FAIL (16) | NONE | 15 | Batch with #456, #451. |
| 451 | bump pillow 11.0.0→12.2.0 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 15 | **SECURITY PATCH** — large Pillow version jump, likely CVE fixes. Fast-track. |
| 447 | bump axios 1.13.2→1.15.0 in /skyyrose | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 17 | Batch with #446. |
| 446 | bump axios 1.13.2→1.15.0 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 17 | Batch with #447. |
| 445 | bump simple-git 3.30.0→3.35.2 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 17 | Batch with npm deps. |
| 443 | bump next 16.1.3→16.2.3 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 19 | Batch with #409 (next bumps). |
| 442 | bump drizzle-orm 0.45.1→0.45.2 in /skyyrose | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 21 | Batch with skyyrose npm deps. |
| 441 | bump vite 6.4.1→6.4.2 in /skyyrose | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 22 | Batch with #440. |
| 440 | bump vite 7.3.1→7.3.2 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 22 | Batch with #441. |
| 439 | bump langchain-openai 1.1.7→1.1.12 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 23 | Batch with langchain group (#437, #418). |
| 438 | bump onnxruntime 1.24.1→1.24.4 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 23 | Batch with python ML deps. |
| 437 | bump langchain 1.2.9→1.2.15 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 23 | Batch with #439, #418. |
| 436 | bump torch 2.9.1→2.11.0 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 23 | Major torch bump — test carefully. Batch separately. |
| 435 | bump psutil 6.1.0→7.2.2 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 23 | Batch with python deps. |
| 427 | bump defu 6.1.4→6.1.6 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 25 | Batch with #426. |
| 426 | bump defu 6.1.4→6.1.6 in /skyyrose | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 25 | Batch with #427. |
| 425 | bump tar 7.5.6→7.5.13 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 25 | **SECURITY PATCH** — tar has known path traversal CVEs. Fast-track. |
| 424 | bump bentoml 1.4.33→1.4.38 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 25 | Batch with python deps. |
| 423 | bump linting group (2 updates) | dependabot | `DEPENDABOT_BATCH` | FAIL (16) | NONE | 29 | Batch with dev tooling PRs. |
| 422 | bump rollup 4.55.1→4.60.0 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 30 | Batch with npm build deps. |
| 421 | bump node-forge 1.3.3→1.4.0 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 31 | Security-relevant — node-forge. Batch. |
| 420 | bump path-to-regexp 0.1.12→0.1.13 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 32 | Security-relevant — ReDoS CVE history. Batch. |
| 419 | bump handlebars 4.7.8→4.7.9 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 32 | Security-relevant — handlebars prototype pollution history. |
| 418 | bump langchain-core 1.2.7→1.2.22 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 32 | Batch with #437, #439. |
| 417 | bump flatted 3.3.3→3.4.2 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 33 | Batch with #463. |
| 416 | bump socket.io-parser 4.2.5→4.2.6 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 33 | **SECURITY PATCH** — socket.io-parser has ReDoS / prototype pollution history. |
| 414 | bump pyasn1 0.6.2→0.6.3 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 34 | Batch with python crypto deps. |
| 413 | bump black 26.1.0→26.3.1 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 34 | Batch with dev tooling. |
| 412 | bump tornado 6.5.4→6.5.5 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 34 | Security-relevant — tornado async server. |
| 411 | bump actions/cache 5.0.3→5.0.4 | dependabot | `DEPENDABOT_BATCH` | PASS (0) | NONE | 35 | **Only dependabot PR with clean CI.** Safe to merge once human PRs are unblocked. |
| 410 | bump @vitejs/plugin-react 5.2.0→6.0.1 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 36 | Major version bump — test. Batch with vite group. |
| 409 | bump next 16.1.6→16.2.1 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 36 | Batch with #443 (next bumps). |
| 408 | bump webpack-cli 6.0.1→7.0.2 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 36 | Batch with dev build tools. |
| 407 | bump lucide-react 0.577.0→1.0.1 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 36 | Major version bump — may have API changes. |
| 406 | bump @vercel/speed-insights 1.3.1→2.0.0 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 36 | Major version bump — Vercel API changes possible. |
| 405 | bump rate-limiter-flexible 9.1.1→10.0.1 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 36 | Major version bump — security-adjacent. |
| 404 | bump @wordpress/env 10.39.0→11.2.0 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 36 | Batch with WP dev tooling. |
| 401 | bump faiss-cpu 1.13.1→1.13.2 | dependabot | `DEPENDABOT_BATCH` | FAIL (15) | NONE | 37 | Batch with python ML deps. |

---

*DRY-RUN: No merges, closes, or pushes were performed.*
