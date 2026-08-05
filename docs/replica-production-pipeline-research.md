# SkyyRose replica-product 3D pipeline research

**Date:** 2026-08-04
**Scope:** 33 published catalog SKUs, branded apparel and accessories, web GLB delivery
**Decision:** no provider dispatch until a SKU has a complete reference pack and passes local preflight

## Executive conclusion

The production target is not “generate a 3D-looking garment from one product photo.”
That is a concept-generation workflow. A replica product needs multi-view evidence,
exact brand-mark references, controlled materials, and a render comparison against
the approved product source.

Tripo's current multiview contract accepts the four cardinal inputs in the order
`front, left, back, right`; its documentation says not to use fewer than two images
and recommends a front input. Meshy's own guidance recommends front, side, back,
and 3/4 views with consistent lighting, and specifically positions multi-view as
the route for high-fidelity reconstruction. [Tripo multiview generation](https://platform.tripo3d.ai/docs/generation)
and [Meshy Image to 3D guidance](https://docs.meshy.ai/en/webapp/image-to-3d)

The pipeline therefore uses AI for base reconstruction only. Logos, patches,
labels, typography, and collection marks must come from approved SOT assets or
deterministic texture/decal work. They are never trusted to a generative provider.
This follows the repository's existing Tripo hallucination guard, which blocks
branded SKUs from the single-image multiview template.

## Evidence from the production tools

### Tripo

The current Tripo API exposes `multiview_to_model` and supports a chained
multiview-image workflow. Its published input schema requires four ordered image
slots (`front`, `left`, `back`, `right`) for a complete request, accepts a direct
`original_task_id` from a multiview-image task, and supports a face limit for
controlled output density. [Tripo generation API](https://platform.tripo3d.ai/docs/generation)

Tripo bills in credits, not a universal USD price. Its current published table
lists multiview-to-3D at 20 credits without texture or 30 credits with standard
texture for the v3.1/v3.0/v2.5/v2.0 family; P1 lists 40/50 credits. Geometry,
texture quality, low-poly, parts, quad topology, and detailed geometry can add
credits. The batch controller must therefore quote credits and the account's
configured conversion, rather than pretending a stale USD constant is exact.
[Tripo pricing](https://platform.tripo3d.ai/docs/billing)

### Meshy

Meshy's API exposes an asynchronous Image to 3D task with a GLB output, task
status, model URLs, thumbnails, PBR maps, and consumed-credit reporting. The API
returns payment and rate-limit failures explicitly, so the controller must not
retry a paid request blindly. [Meshy Image to 3D API](https://docs.meshy.ai/en/api/image-to-3d)

Meshy distinguishes Standard high-detail output from Smart Topology output for
real-time delivery. Standard is the correct source candidate for fidelity review;
Smart Topology is a later derivative after the source replica passes. [Meshy
Image to 3D](https://docs.meshy.ai/en/webapp/image-to-3d)

### Garment reconstruction research

Recent garment-reconstruction work supports the same operational conclusion:
ReWeaver reconstructs seams, panels, and their 2D/3D connectivity from as few as
four sparse multiview RGB images, while Deep Fashion3D describes clothed-garment
recovery as substantially harder than unclothed-body recovery and evaluates it
with real-garment models, feature lines, body pose, and corresponding multiview
images. [ReWeaver](https://arxiv.org/abs/2601.16672), [Deep Fashion3D](https://arxiv.org/abs/2003.12753)

### Delivery format

Blender's glTF exporter supports Draco mesh compression, and Khronos documents
`KHR_draco_mesh_compression` as a ratified glTF extension. Export is still a
separate gate: a visually correct but uncompressed or texture-misconfigured GLB
is not a shippable web asset. [Blender glTF export](https://docs.blender.org/manual/en/3.3/addons/import_export/scene_gltf2.html),
[Khronos glTF extensions](https://github.com/KhronosGroup/glTF/blob/main/extensions/README.md)

## Production pipeline

### 0. Zero-cost SKU intake

Resolve the catalog row and dossier. Confirm the SKU, collection, garment type,
approved image sources, logo references, and licensing/provenance. Reject retired,
unknown, duplicate, or ambiguous SKUs before any provider call.

### 1. Reference-pack completion

Each SKU gets a locked pack:

```text
<sku>/
  front.jpg       # exact product, normalized framing
  left.jpg        # exact product, not AI-inferred
  back.jpg        # exact product
  right.jpg       # exact product, not AI-inferred
  detail-1.jpg    # logo/patch/label/seam/material close-up
  manifest.json   # hashes, camera/light notes, source rights, SKU binding
```

The four provider inputs must show the same physical sample, consistent lighting,
and a simple background. The detail frame is not sent as a substitute for a
cardinal view; it anchors brand-mark and construction checks.

### 2. Local preflight and quote

The controller checks image dimensions, file type, hashes, exact SKU binding,
duplicate-image fingerprints, and required angles. It computes the provider
credit quote, maximum retries (zero by default), and total batch ceiling. Any
missing pack member or stale hash produces a $0 plan and exits before API auth or
upload.

### 3. Provider dispatch

Use native multiview-to-3D when the pack is complete. Do not use Tripo's branded
single-image multiview template. Start with one pilot SKU per garment class and
stop the batch if the pilot misses a mark, silhouette, panel, or material gate.
The provider result is an untrusted candidate and cannot be copied into the theme.

### 4. Deterministic product detailing

Ingest the candidate into Blender. Preserve the generated base mesh only where it
matches the silhouette and construction. Replace or correct brand-critical
surfaces with approved SOT decals/material maps: roses, monograms, patches,
labels, typography, piping, seam lines, and hardware. This is the stage that
turns a plausible generated garment into an auditable product replica.

### 5. Export normalization

Produce a GLB derivative with normalized texture dimensions and MIME types,
Draco compression, stable SKU filename, and recorded source/model hashes. Run
the independent GLB export gate; a tool exit code without matching structural
evidence is not a pass.

### 6. Visual fidelity gate

Render `front`, `back`, `left`, `right`, and `detail-1` from fixed camera profiles.
Compare each against its golden reference. Any missing view, inferred view, low
composite score, geometry failure, or mark mismatch rejects the candidate. The
existing asset gate then requires a signed build attestation and founder approval
before `approved` can be emitted.

### 7. Delivery derivatives

Only after approval, create web/mobile derivatives and attach the approved GLB to
the exact WooCommerce SKU. Keep the original candidate, normalized source, render
evidence, hashes, and approvals in the audit bundle. Theme packaging consumes the
approved manifest, never a directory glob.

## Current batch audit

The current catalog has 33 published SKUs. All 33 have catalog `image`,
`front_model_image`, and `back_model_image` files present. However, the golden
reference store does not have complete five-angle packs for those 33 products,
and the existing Tripo dispatch classifier reports 0/33 eligible for its
single-image branded multiview path (29 branded, 4 explicitly not tech-flat).

The existing web hub contains 33 SKU-named GLBs, but that is asset presence, not
replica proof. They remain unapproved until the new reference-pack, export, and
visual gates pass.

## Cost-control rule

The only safe batch command before the reference packs are complete is a dry-run
that emits blocked SKUs, missing evidence, and commits zero provider spend. The
plan may still show a quoted cost for budgeting, but `dispatchable` must be false
and no provider adapter may be constructed. A provider call is allowed only after
the preflight manifest is complete, the credit quote is under the batch ceiling,
the build and policy trust roots are configured, and the founder/operator
explicitly authorizes that specific batch.

## Research limits

The provider documentation describes API capabilities and billing, not a
guarantee that generated garments are pixel-identical to a photograph. The
identity guarantee in this repository comes from the reference pack, deterministic
brand-mark handling, independent render comparison, and founder approval—not from
the provider's marketing quality label.
