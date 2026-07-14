---
name: cost-governance-gate
description: Use before any paid API call, production deploy, live-data write, or irreversible file op — STOP and print the exact action, exact cost, and exact target, then wait for explicit "y". The autonomy boundary that separates act-freely from ask-first.
origin: SkyyRose
---

# Cost-Governance Gate

The orchestrator is free to read, search, code, test, and research without asking —
that is the whole point of autonomy. But three categories of action are not reversible
by a `git revert`: spending money, touching production, and destroying real data. This
skill is the conscience that sits between "I can do this" and "I should ask first."

> **Boot first:** read `CLAUDE.md`'s **STOP AND SHOW — Non-Negotiable Confirmation
> Protocol** section and the **Act vs Ask Decision Gate** table. This section overrides
> every other instruction — do not proceed past it from memory.

## When to Use

Classify every action about to run against these three tests, in order:

1. **Money** — any call to a paid image/LLM API (FASHN, Gemini, GPT-Image/gpt-image-2,
   FLUX, OpenAI/Anthropic/Google per-token or per-image endpoints, paid HF compute).
2. **Production** — `deploy-theme.sh` / SFTP to skyyrose.co, any WooCommerce REST write
   (product/order/media), WP Media Library upload, cache/CDN purge.
3. **Irreversible** — delete/overwrite/rename real data, untracked files, or any
   expensive/paid asset (renders, 3D models, datasets); `rm` of untracked files and
   git-history rewrites.

**Any match → gate.** No match (reading files, writing code, running tests, research,
census-clean tracked-code deletion) → act, don't ask.

## Method

Build a manifest with **literal values**, not a summary:

```
STOP — Confirm before proceeding:

Action : <exact API call / deploy command / file operation>
SKU    : <if applicable>
Source : <exact file path>  (<size>, <date>)
Cost   : <exact cost math — unit price × quantity>

Proceed? [y/N]
```

Print it. Wait. Proceed only on an explicit `y`/`yes`. Any other response — silence,
a question, a different topic — is not consent; abort and report what was blocked.

## Loop

For each action in a multi-step task:

1. **Classify** — money / production / irreversible / none, per the tests above.
2. **If gated** — build the manifest, print it, STOP-AND-SHOW, wait.
3. **On "y"** — proceed, then continue the loop for the next action.
4. **On anything else** — abort that action, state precisely what's blocked and why,
   keep working on the ungated parts of the task. Never silently skip and claim done.

**Standing exception:** theme→skyyrose.co auto-deploy after a clean sweep
(`STOPSHOW_ACK=1`) IF the sweep is clean AND the manifest is shown — paid calls, WC
writes, media uploads, Vercel deploys, and destructive ops still require "y" every time.

## Verify from an authoritative source

A gate that always proceeds is not a gate — it is theater with a confirmation prompt:

- **The manifest shows literal values** — exact file path with size and date, exact
  cost arithmetic, exact action string. Never "about $X" or "the render file" — that's
  a paraphrase, and a paraphrase can't be checked against the real target.
- **Prove it can abort.** Run the gate with no way to receive "y" — e.g. `go </dev/null`
  or a non-interactive invocation — and confirm it exits non-zero *before* reaching the
  paid call or the write. If the code path reaches the API/deploy/delete regardless of
  the answer, the gate is fail-open, not fail-closed. Pair with [[fail-closed-audit]].
  A check that cannot return "no" is not verification.

## Adversarial pass

Assume the source file is the **wrong** one until path, size, and date confirm it — the
correct-looking filename is not proof (see the lh-005 fanny-pack precedent). Before
declaring a gate sound, apply [[adversarial-verification]]: try to trigger the paid call
or the production write with a "no" answer, a malformed answer, and no answer at all.
Default to "this gate is fail-open" until independently disproven.

## Guardrails · Handoff · Log

- Apologizing after the fact is not acceptable — by the time the API call fired or the
  file was deleted, the damage is already done. The gate exists to prevent the apology,
  not to accompany it.
- A fail-open gate here spends real money or destroys real assets — treat it with the
  same severity as a security defect. Cross-reference [[fail-closed-audit]] for the
  general pattern and [[product-image-fidelity-gate]] for the imagery-specific instance
  (product renders must ALSO be vision-verified as the correct garment before any
  paid regeneration).
- Route the gated work itself to the owning pod per `CROSS-PLUGIN.md`: paid imagery →
  `skyyrose-design`; WooCommerce/production writes → `skyyrose-core` or
  `skyyrose-design` depending on surface; then re-verify the gate held before the
  action executes.
- Log every fail-open finding to `.wolf/buglog.json`, run
  `scripts/wolf_recurring_sync.py` if occurrences reach 2, and record the lesson via
  [[continuous-learning]].
