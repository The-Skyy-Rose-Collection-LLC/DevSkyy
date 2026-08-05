---
name: adversarial-planning-free
description: Generate a zero-network, zero-paid-call release closeout plan from repository evidence. Use for marketplace readiness, release-candidate audits, packaging gates, or project-manager closeout lists when paid multi-model debate is not authorized or would add no value.
---

# Adversarial Planning Free

Produce a deterministic challenge to release claims. This is not a substitute for two-model debate; it tests claims against files, Git state, build outputs, trust roots, and static checks.

## Run

From the repository root:

```bash
python3 skyyrose-suite/plugins/skyyrose-core/skills/adversarial-planning-free/scripts/marketplace_closeout.py \
  --repo . \
  --theme wordpress-theme/skyyrose-flagship-2
```

The script is read-only and uses only the Python standard library plus installed `git`, `php`, and `node` commands. It makes no network, model, upload, install, deploy, or paid calls.

## Interpret

- `BLOCK`: resolve before commit/package/submission.
- `VERIFY`: obtain runtime, legal, or human evidence before claiming marketplace readiness.
- `DONE`: reproduced by the current run.

Treat the highest-severity unresolved item as the release status. Do not convert `VERIFY` to `DONE` from prose or memory.

## Closeout order

1. Fix supply-chain and security blockers.
2. Fix route/update compatibility blockers.
3. Commit the scoped source and generated assets.
4. Build twice from clean `HEAD`; require identical ZIP digests and safe extraction.
5. Sign policy/build/founder evidence with configured trust roots.
6. Install the exact ZIP on staging and run the full WooCommerce, browser, accessibility, responsive, Lighthouse, and visual/SOT matrix.
7. Complete the asset-rights ledger, documentation, screenshots, and marketplace submission package.

## Rules

- Never run provider generation to fill an empty model manifest.
- Never package an uncommitted worktree when the package script archives `HEAD`.
- Never call a static pass a browser, WooCommerce, legal, or founder approval pass.
- Never weaken a blocker to make the report green.
