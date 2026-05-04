---
name: Phase 0.5 Blocking Prerequisites Check Output
specified_by: [v2: §5 Phase 0.5]
phase: 0.5
test_command: node scripts/measurement/check-prerequisites.js  # PHASE 0.5 DELIVERABLE — script does not exist yet; running it will exit 1 with a 'Phase 0.5 not started' message until the runner is built. See scripts/measurement/README.md.
pass_threshold: All 8 prerequisites PASS or marked N/A with documented reason
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0 placeholder)
---

# Blocking Prerequisites — Phase 0.5

> **PLACEHOLDER STATUS:** This file is empty in Phase 0. Phase 0.5.a populates it with the actual check results. If all checks PASS, this file remains a one-line "All prerequisites passed on YYYY-MM-DD" record. If any check FAILS, the failure detail is written here and the build halts pending resolution.

## Prerequisites (per V2 §5 Phase 0.5)

| Check | Method | Pass condition | Status |
|-------|--------|----------------|--------|
| Stripe account | `mcp__stripe__authenticate` | Returns valid account | PENDING (Phase 0.5.a) |
| FASHN API key | Env var `FASHN_API_KEY` set in Vercel | Present, format-valid | PENDING |
| Pinecone account | `pinecone:quickstart` provisioning | Index `skyyrose-products` exists or creatable | PENDING |
| Anthropic API key | Env var `ANTHROPIC_API_KEY` set | Present | PENDING |
| Avatar GLB rig | `node scripts/check-glb-rig.js assets/models/skyy.glb` | If used in 5.6/5.8: bones > 0, animations > 0 | PENDING (likely FAIL — `MEMORY.md` notes 0 bones, 0 animations on all 6 GLB variants) |
| WP REST API auth | `curl -u $WP_USER:$WP_APP_PASS https://skyyrose.co/wp-json/wp/v2/pages?per_page=1` | HTTP 200 | PENDING |
| Vercel CLI auth | `vercel whoami` | Returns user | PENDING (likely PASS — `.vercel/project.json` linked per CLAUDE.md) |
| Pusher account | Env var `PUSHER_APP_ID` set | Present | PENDING |

## Failure handling

Any FAIL → write the specific failure here with:

- Which check failed
- Why (error message, missing env var, etc.)
- What the user (Corey) needs to do to resolve, OR what Claude Code can do to resolve autonomously
- Whether the failure blocks the entire build or only specific phases

If avatar GLB rig fails AND Phase 5.6 or 5.8 depend on it, the failure escalates to G3 with a Blender/Mixamo rig instruction artifact at `eval/avatar-rig-required.md`.

## N/A handling

If a prerequisite is genuinely not applicable (e.g., Pusher account isn't needed because drop queue uses a different transport), mark as N/A with a one-line reason. Don't leave PENDING — that signals the check hasn't run yet.

## Phase 0.5 entry expectation

Phase 0.5.a runs all 8 checks. This file is the output. The phase advances only when this file shows all rows PASS or N/A.
