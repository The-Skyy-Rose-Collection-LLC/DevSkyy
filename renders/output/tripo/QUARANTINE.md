# renders/output/tripo/ — QUARANTINED OUTPUTS

**Status:** All branded outputs in this directory are HALLUCINATED. Do not publish to skyyrose.co.
**Generated:** May 8, 2026 (commit `d86ee6e45`, batch run 00:13–04:48 PDT)
**Quarantined:** May 11, 2026
**RCA:** `BUG-tripo-hallu-001` (see `.wolf/buglog.json`)

---

## What's broken

The 30 SKU subdirectories in this folder contain 120 image-to-3D-multiview
renders produced by **Tripo's `generate_multiview_image` template** running
**FLUX.1 Kontext** under the hood. The template accepts only a source image
— no prompt, no logo overlay, no dossier branding spec, no palette token,
no garment-type lock. With no canon to anchor against, FLUX freelances on
every non-trivial branded surface.

Confirmed hallucinations (1:38 PDT May 11 sample of 3 SKUs):

| SKU | Real product | Rendered as |
|-----|--------------|-------------|
| **br-001** | Black Rose Crewneck (canonical black-rose-logo embroidery, white-trim ribbing) | Gray sage/blue rose-on-cloud motif (FLUX trained-on stock fashion graphic), garbled neckline label |
| **br-011** | "The Rose" Hockey Jersey (NHL Authentic Collection cut, no hood, mesh side panels) | Cyan/teal hoodie with invented chest crest, fake hem patch with garbled text |
| **sg-007** | The Signature Beanie (front-center SR monogram or red-roses cluster) | Black beanie with off-canon rose-on-cloud sewn-on patch on right cuff |

The same "rose-on-cloud" motif appears across multiple unrelated SKUs — it
is a FLUX prior the template defaulted to in the absence of a canon anchor.

## Why this happened

5-layer failure chain:

| Layer | Failure |
|-------|---------|
| **L1 — Wrong tool** | Tripo `generate_multiview_image` is for UNBRANDED CLEAN TECH-FLATS — it generates camera angles, not branded renders |
| **L2 — No anchor** | `tripo_agent.py:106-108` calls `generate_multiview_image(image=...)` naked. No prompt, no ref overlay, no palette |
| **L3 — Wrong source feed** | Some SKUs (br-001) had empty `image` column, so the dispatch script fell back to `front_model_image` — a model-on shot. FLUX rebuilt the garment from scratch |
| **L4 — No QA gate** | 30 SKUs × 4 views = 120 images written direct to disk with zero quality classifier or human approval |
| **L5 — STOP-AND-SHOW showed cost, not preview** | The gate confirmed dollar amounts; nothing surfaced a sample output |

## Fix (committed 2026-05-11)

`scripts/tripo_dispatch.py` now blocks at the dispatch boundary:

1. **Branded SKU guard.** If the dossier frontmatter has `logo_reference:`
   populated, the SKU is blocked. Override with `--force-branded` (prints a
   WARNING and still requires explicit `y` to dispatch).
2. **Tech-flat source guard.** If the catalog `image` column is empty or
   the file is missing, the SKU is blocked. No model-on shots accepted —
   the template breaks on them.
3. **Per-SKU block reason** printed in the manifest before the `y/N`
   prompt, so the human can see exactly what got refused.

Tests live in `tests/test_tripo_dispatch_guards.py` (12 unit tests covering
both guards plus the `--force-branded` escape hatch).

## What to do with the contents

- **Do not publish** any image in this folder to skyyrose.co.
- **Do not feed** any image here into downstream 3D mesh generation (Tripo
  image-to-3D, Meshy, TRELLIS) — the input would be hallucinated, the mesh
  would inherit the hallucination.
- **Keep for now** as evidence. The forensic record helps tune future QA
  thresholds.
- **Re-render branded SKUs** via the ADK `render_pipeline` (see
  `agents/render_pipeline/agent.py`) — that path applies logo overlays,
  3-judge QA tournament, and refine loop. Selectable from
  `EliteStudioState.engine="adk-render"` (P7, commit `97ded5587`).

## See also

- RCA in `.wolf/buglog.json` under `BUG-tripo-hallu-001`
- Cerebrum `Do-Not-Repeat` entry "Tripo multiview for branded SKUs"
- Phase E manifest at `tasks/phase-e-manifest.md` (real cost ceilings,
  correct dispatch path)
