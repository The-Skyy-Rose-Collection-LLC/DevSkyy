---
name: saas-gate-avif-blocked-vs-code
tags: [saas-gate, avif, asset-blocked, g2-check, g13-check]
locked: 2026-05-25
---

# SaaS Gate G2 AVIF Failure: Asset-Blocked vs Code-Blocked

## The Distinction

**Code-blocked AVIF failure**: `<picture>` elements missing `type="image/avif"` source tags.
Fix: add `<source ... type="image/avif">` before the WebP source. Always fixable in this session.

**Asset-blocked AVIF failure**: The AVIF file itself doesn't exist on disk.
G13 (asset path resolution) catches fabricated paths — it resolves relative paths from the target dir
and checks `[[ -f "$resolved" ]]`. If the file isn't there, G13 fails too.

**Rule**: NEVER add an AVIF `<source>` pointing to a path that doesn't exist on disk.
Both G2 and G13 will catch it; the gate gets worse, not better.

## v2.html Session Result (2026-05-25)

- Pre-session: ~8 AVIF sources / 13 pictures (FAIL)
- Phase 3 adds 4 patch AVIF sources (disk-verified): `br-patch-{nfl,nba,mlb,hockey}.avif` → 12/13
- Remaining FAIL: `forbidden-midnight-{480,768,1280,1680}w.webp` exist, but no `.avif` counterparts
- Asset-blocked: fix requires `avifenc` run on existing WebP/JPG masters (Tier 4 deferred)
- Cannot reach 13/13 without the avifenc run — **do not fabricate the paths**

## Deferred Fix (STOP-AND-SHOW)

```bash
# STOP — confirm before running (Tier 4: compute-heavy)
for w in 480 768 1280 1680; do
  avifenc \
    wordpress-theme/skyyrose-flagship/assets/branding/hero/forbidden-midnight-${w}w.webp \
    wordpress-theme/skyyrose-flagship/assets/branding/hero/forbidden-midnight-${w}w.avif
done
```

Then add 4 `<source type="image/avif">` tags to the 3 `<picture>` elements in the BR cover/hero
(v2.html lines ~780-820 area). This closes the G2 FAIL and allows full PASS on saas-gate.
