---
name: elite-builder-runtime
description: Lazily operate the optional hardened Elite Web Builder runtime bundled with Fashion Theme Team. Use only when the user requests the runtime, multi-provider story execution, its verification/self-heal loop, or its specialized Python tools. Do not use for ordinary team routing or theme edits.
---

# Elite Builder Runtime

This capability is opt-in. Read `../../runtime/elite_web_builder/INTEGRATION.md`
before using any runtime file. Do not preload runtime modules or provider tool
definitions during normal Fashion Theme Team work.

## Safe planning

```bash
python3 runtime/elite_web_builder/run.py --prd <approved-prd.md>
```

Planning is local: it does not import provider SDKs, scan `.env` files, or make
external calls.

## Live execution boundary

Live execution requires the founder to approve the exact PRD, provider routing,
estimated budget, and target. Only then run:

```bash
python3 runtime/elite_web_builder/run.py \
  --prd <approved-prd.md> \
  --routing <approved-routing.json> \
  --execute \
  --approved-paid-providers
```

Provider credentials must already exist in process environment variables. The
runtime never reads repository `.env` files. Never use its generic legacy
knowledge as SkyyRose canon.

## Verification semantics

- `PASSED` requires executed evidence.
- `SKIPPED`, missing, timeout, and error remain unresolved.
- Self-healing may repair code but never edit thresholds, disable gates, or
  reinterpret skipped evidence.
- Every output remains candidate-bound and requires the Fashion Theme Team's
  independent visual, accessibility, commerce, performance, and release gates.
