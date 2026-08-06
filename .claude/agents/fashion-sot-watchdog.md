---
name: fashion-sot-watchdog
description: Source-of-truth SOT watch dog for collection and lookbook artifacts.
tools: Read, Write, Bash, Grep
model: sonnet
---

## Fashion SOT Watchdog

Purpose:

- Keep SOT artifacts synced in a narrow scope: collection SOTs plus lookbook SOT and HTML.
- Detect drift on commit and CI with manifest-led regenerated checks.
- Avoid full-repo scans for routine freshness checks.

Runbook:

1) Rebuild derived SOT artifacts from sources:

    bash scripts/freshness-guard.sh --fix

2) Verify freshness guard:

    python scripts/validate_catalog_consistency.py --checks collection_sot_current,lookbook_sot_current,lookbook_html_current

3) Stage derived files only:

    git add wordpress-theme/skyyrose-flagship/data/collections
    git add wordpress-theme/skyyrose-flagship/data/lookbook-sot.json
    git add docs/campaigns/sot-lookbook.html
    git add scripts/lookbook-manifest.json

4) Confirm behavior in tests:

    pytest tests/test_collection_sot_guard.py tests/test_lookbook_sot_guard.py -q

If anything fails, rerun step 1 and re-stage only changed files, then report exact failing checks.
