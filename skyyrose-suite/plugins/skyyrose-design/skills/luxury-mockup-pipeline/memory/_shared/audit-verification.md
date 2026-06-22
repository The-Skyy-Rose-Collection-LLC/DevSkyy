---
name: audit-verification
description: Multi-agent audit P0 false-positive rate ~25% — always verify live state before drafting fixes
tags: [audit-discipline, verification]
applies_to: [ux-architect, ui-designer, brand-guardian, frontend-developer, senior-developer]
last_verified: 2026-05-24
---

# Audit Verification

Multi-agent audits have a ~25% P0 false-positive rate (observed 2026-05-23 SkyyRose audit: 12 reported P0s collapsed to 9 actionable).

**Why:** agents pattern-match on doc claims without checking live state. WebFetch strips `<script>` tags. WP.com Batcache serves stale HTML for minutes after deploy. Memory entries can be stale.

**How to apply:** before drafting any audit fix:
1. Curl live URL with cache-bust: `curl -s "https://skyyrose.co/?cb=$(date +%s)"`
2. Grep for the actual claim — JSON-LD / OG tags / inline JS / canonical markup
3. Confirm the violation EXISTS in live render before recommending a fix
4. Memory facts that name file paths / functions → verify file exists first

**Source:** `/Users/theceo/.claude/projects/-Users-theceo-DevSkyy/memory/feedback_verify_before_audit_claims.md`
