---
name: product-image-fidelity-gate
description: MANDATORY before rendering, creating content, or editing skyyrose.co — eyes-on verify every product image is the CORRECT garment for its SKU by reading the actual pixels (vision), never the filename or manifest. Prevents wrong-garment imagery, the #1 recurring defect.
origin: SkyyRose
---

# Product-Image Fidelity Gate

Filenames lie. Manifests lie. Only the pixels are truth. Wrong-garment imagery is the
**#1 recurring defect** in this project: `lh-005` was shipped as a fanny pack it never
was, and **bug-096** (recurred ×30) shows Tripo's `generate_multiview_image` hallucinating
brand canon on 30 SKUs — 120 renders that invented motifs and rendered `br-011`'s hockey
jersey as a cyan/teal hoodie with an invented crest. Never-made renders have leaked onto
live product cards. This gate exists because a green manifest and a wrong garment can
coexist.

> **Boot first:** `SOT.md` → catalog CSV + per-SKU dossier → `data/sot-images.json`
> (`skyyrose.core.sot_images`) → `.wolf/buglog.json` (grep `bug-096` — the pattern is
> already logged) → `CLAUDE.md`. Do not resolve identity from memory or a filename.

## When to Use

- Before rendering anything, creating content, or editing skyyrose.co that touches
  **any product image about to reach the site** — PDP hero, collection card, email,
  social asset, dashboard preview.
- Before approving output from any imagery pipeline (Elite Studio, Tripo, OAI render,
  FASHN try-on) that produces a SKU-attributed image.
- Before trusting a render-review manifest, QC report, or "verdict: verified" flag that
  you have not personally read the pixels for.

## The one rule

**Every product image touching the site is eyes-on verified as the correct garment for
its SKU before it ships.** Product renders come from **OAI gpt-image-2 only** — any other
engine producing a branded SKU render is itself a defect signal. A manifest that cannot
be visually falsified is not verification — it is a guess with a citation.

## Method

1. **Resolve identity via SOT** — pull the SKU's canonical record: catalog CSV row +
   per-SKU dossier (garment type, color, branding spec) + `sot-images.json` entry
   (front-first). This is the *only* legitimate identity source — never a filename,
   never a directory listing, never a prior session's memory.
2. **Read the actual pixels** — `Read` the image file directly (vision). Look at the
   garment silhouette, color, fabric, and any logo/branding placement.
3. **Compare against the dossier** — does the pixel-level garment match the catalog
   entry (type, color, silhouette) and the dossier's branding spec (logo present/absent,
   placement, motif)? A cyan hoodie is not a jersey. An invented rose-on-cloud motif is
   not in any dossier.
4. **Match → proceed. Mismatch or uncertain → BLOCK.** No partial credit — "looks close
   enough" is how bug-096 shipped 120 defective renders past a cost-only STOP-AND-SHOW
   that never previewed output.

## Loop until every image is confirmed

Bounded per batch, one image at a time — never batch-approve on a sample:

```
1. Take the next unverified image.  2. Resolve its SKU via SOT (CSV + dossier + sot-images.json).
3. Read the pixels (vision).  4. Garment/color/branding match the dossier?
5. Yes → mark confirmed, next image.  No/uncertain → BLOCK, flag with file path + reason.
6. Repeat until the batch is exhausted.  Never proceed on an unconfirmed image "for now."
```

## Verify from an authoritative source

The only authoritative check here is **your own eyes on the pixels** — nothing else
substitutes:

- **Read the image with vision** and describe what garment it actually shows, then
  compare that description to the dossier — not the other way around.
- **`identify` for metadata only** (dimensions, format) — it cannot tell you what
  garment is depicted. Never treat a passing `identify` as a fidelity check.
- **Batch all image reads once per conversation** — there is a per-conversation image
  read quota; once exceeded, ALL further reads fail silently-wrong. Plan the full batch
  before reading the first image. Never retry a failed read hoping it clears.
- **If vision is unavailable** (quota exhausted, tool error) **the gate FAILS CLOSED** —
  do not render, publish, or deploy on an unconfirmed image. Report the block; do not
  guess from the filename to "keep moving."

## Adversarial pass

[[adversarial-verification]] — assume every render is the **wrong garment** until the
pixels prove otherwise. Do not extend good faith to a pipeline that has hallucinated
before (bug-096) or to a manifest whose author is the same process that generated the
image (self-grading — mirrors the fail-open pattern in [[fail-closed-audit]]).

## Guardrails · Handoff · Log

- Any paid render call (OAI gpt-image-2, FASHN, Tripo) is **STOP-AND-SHOW** — manifest +
  cost, explicit "y", before dispatch. See [[cost-governance-gate]].
- Uncertain is a BLOCK, not a pass — same discipline as [[fail-closed-audit]]: a check
  that cannot return "no" is not verification.
- Log every wrong-garment finding to `.wolf/buglog.json` under the `bug-096` lineage
  (bump `occurrences`, never duplicate) and record the lesson via [[continuous-learning]].
- Handoff per `CROSS-PLUGIN.md`: imagery-engine defects → the render pipeline owner;
  theme/PDP wiring that surfaced the bad image → `skyyrose-design` frontend work; then
  **re-verify here** before the corrected image ships.
