---
name: no-webfetch-for-scripts
description: WebFetch strips script tags during HTML→Markdown conversion. Use curl+grep for JSON-LD / OG / inline JS
tags: [tool-discipline, audit, false-positives]
applies_to: [ux-architect, ui-designer, brand-guardian, frontend-developer, senior-developer]
last_verified: 2026-05-24
---

# No WebFetch for Script Tags

WebFetch tool strips all `<script>` blocks (including JSON-LD) during HTML → Markdown conversion. Using it to audit structured data / OG meta / inline JS produces FALSE POSITIVES every time.

**Why:** 2026-05-23 SkyyRose SEO audit reported "zero JSON-LD on all 4 pages, OG tags absent" as P0 finding. Live `curl + grep` showed 2 JSON-LD blocks per page (Product, BreadcrumbList, ItemList, Organization) + full OG markup. Cost ~1500 tokens of bad analysis + near-miss on shipping a "fix" for a non-bug.

**How to apply:**
```bash
# WRONG (strips scripts)
WebFetch url:https://skyyrose.co/...

# RIGHT (preserves structure)
curl -s "https://skyyrose.co/page/?cb=$(date +%s)" | grep -oE '<script type="application/ld\+json">[^<]+'
curl -s URL | grep -oE '<meta property="og:[^"]+" content="[^"]+"'
```

**Apply to:** any structured-data audit, OG tag verification, inline JS inspection, JSON-LD validation, schema.org checks.

**Source:** `/Users/theceo/.claude/projects/-Users-theceo-DevSkyy/memory/feedback_verify_before_audit_claims.md`
