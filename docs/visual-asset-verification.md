# SkyyRose visual asset verification

The 3D/Tripo path is fail-closed. A model is not a product asset merely because
it is named after a SKU or looks plausible in one screenshot.

The release gate requires:

1. An exact lowercase hyphenated SKU in the model filename.
2. Five real approved references: `front`, `back`, `left`, `right`, and `detail-1`.
3. A provenance attestation containing the model SHA-256, reference SHA-256 map,
   approved SOT source kind, and a valid build-attestor Ed25519 signature.
4. A Blender render and comparison for every canonical view at the calibrated
   fidelity threshold (`0.95` by default).
5. A founder approval record signed by the configured founder Ed25519 root.

Anything missing is `reject` or `human_review`; it is never treated as a pass.
The machine may report `ready_for_founder_approval`, but it may not publish that
asset or place it in the theme package.

## CLI

```bash
python3 scripts/verify_visual_asset.py \
  --sku sg-015 \
  --model /absolute/path/sg-015-candidate.glb \
  --references /absolute/path/to/golden \
  --provenance /absolute/path/sg-015.provenance.json \
  --trust-manifest docs/theme-machine/manifest.json \
  --report-root renders/fidelity-reports
```

The command exits `0` only for `approved`. Rejected, incomplete, unsigned, or
founder-pending assets exit `2`.

## ADK workflows

`adk.visual_asset_workflows` exposes three Google ADK workflow roots:

- `visual_asset_intake`: exact-SKU and provenance intake before expensive work.
- `visual_asset_verification`: primary deterministic gate plus independent
  adversarial re-check and release disposition.
- `tripo_release_candidate`: treats Tripo output as untrusted and routes it
  through the same exact-product gate.

The ADK agents are orchestration and evidence-review roles. They cannot sign,
approve, publish, or bypass the deterministic gate. A workflow error is a block.

## Current candidate status

The existing `sg-015` web GLB is intentionally blocked until the repository has
complete canonical golden references and a controlled build-attestor provenance
record. It must remain out of the v2 hero and package until the gate returns
`approved` with founder evidence.
