# Obsolete Documentation Report

**Generated**: 2026-03-03
**Previous Scan**: 2026-02-24
**Total docs scanned**: 215 files in docs/
**Threshold**: Status reports (30 days), deployment reports (60 days), general docs (90 days)

---

## Summary (2026-03-03 Scan)

| Category | Count | Status |
|----------|-------|--------|
| **Docs older than 90 days** | 0 | None found |
| **Previously archived** | 19 | Already in `docs/archive/` |
| **Core docs (active)** | 7 | CONTRIB, RUNBOOK, ENV_VARS, SCRIPTS_REFERENCE + 4 codemaps |
| **Total docs scanned** | 215 | All within 90-day window |

No new obsolete files found. All docs were bulk-committed Feb 23 or later.

---

## Potentially Stale Content (Review Recommended)

These docs have current timestamps but may contain outdated content:

| File | Concern |
|------|---------|
| `3D_GENERATION_PIPELINE.md` | Pipeline evolved — Gemini now primary, not Hunyuan |
| `3D_GENERATION_FILES.md` | File paths changed with render-front/back/branding migration |
| `AR_SHOPPING_MISSION.md` | AR features not yet implemented |
| `AR_STACK_CONFIGURATION.md` | AR features not yet implemented |
| `WORDPRESS_SHOPTIMIZER_BUILD_GUIDE.md` | Using skyyrose-flagship, not Shoptimizer |
| `COLAB_TRAINING_GUIDE.md` | Training approach changed (local + Replicate, not Colab) |
| `VERCEL_ROUTING_FIX.md` | One-time fix, may be obsolete |

## New This Session

| File | Purpose |
|------|---------|
| `codemaps/architecture.md` | System overview, dependency flow, package map |
| `codemaps/backend.md` | Python backend (12 packages) |
| `codemaps/frontend.md` | Next.js frontend (23 routes, 60+ components) |
| `codemaps/data.md` | Data models (SQLAlchemy, GraphQL, gRPC, PHP catalog) |

## Recently Updated

| File | Date | Change |
|------|------|--------|
| `CONTRIB.md` | 2026-03-03 | Version bump to 3.4.0, added codemaps + AI CLI references |
| `RUNBOOK.md` | 2026-03-03 | Version bump to 3.4.0 |
| `SCRIPTS_REFERENCE.md` | 2026-03-03 | Date refresh |
| `OBSOLETE_DOCS_REPORT.md` | 2026-03-03 | This scan |

## Recommendation

1. No urgent action needed — core docs are current
2. Low priority: Review 7 "Potentially Stale" docs above during next maintenance window
3. Consider archiving AR docs (not implemented) and Shoptimizer guide (wrong theme)
