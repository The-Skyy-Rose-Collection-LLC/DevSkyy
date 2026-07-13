# Corrective Shape Keys for Extreme Flexion (Candy-Wrapper Collapse)

Applies `doctrine.md`'s numeric-gate and independent-verification rules throughout.

## The ordering rule

Corrective/pose-driven shape key computation is the FIRST-CHOICE remediation for Linear Blend
Skinning "candy-wrapper collapse" at extreme joint flexion. Weight-paint retries and
helper/twist-bone additions are not authorized as first-choice remediation.

**Cite the real precedent precisely (`.wolf/buglog.json` bug-194) — do not overstate it.** The
actual sequence on the mascot's wave-clip crotch fold was: 3 same-night non-shape-key attempts
(weight smoothing, flexion clamp, manual-blend) plus 3 shape-key iterations, before a correct
closed-form fix succeeded. Only one or two of those attempts were literally "weight painting" —
never restate this in shipped work as "weight painting proven insufficient three times," which
overstates what bug-194 actually documents. Of the 3 shape-key iterations, the third's apparent
"shattered geometry" was itself a scale-unit misdiagnosis at the time (see below), not a
separate defect — bug-194 does not detail what specifically went wrong in the first two
shape-key attempts, so don't assert more forensic detail than the source states.

Also re-verify scope from fresh evidence before building anything: bug-194's own task assumed
all 5 gesture clips (wave/walk/talk/point/joy) needed a fix. Fresh pristine renders at measured
peak-flexion frames showed only wave has a genuine defect — the other 4 were already clean and
would have regressed if "corrected." Trust your own fresh renders over an inherited scope claim.

## The closed-form LBS inverse method

```
corrected_rest = A_blend.inverted() @ desired_world
```

Gated by two numeric checks, both required, both printed from a real script run:

- **Gate 1** — the forward formula (applying `A_blend` to `corrected_rest`) matches Blender's
  own depsgraph-evaluated posed position. Target: ~1e-7 (machine precision for this operation).
- **Gate 2** — reapplying the blend matrix to the corrected rest pose reproduces the desired
  posed target. Target: ~1e-16.

Both gates must be checked in the SAME unit space (see the unit-scale trap below) — a gate
that "passes" after silently mixing world-space and local-space units isn't verified, it's
coincidence.

## The unit-scale trap (this is why v3's "shattered" result was a misdiagnosis, not a bug)

At a Mixamo-style armature world scale of 0.01 (cm→m), a local-space shape-key delta is ~100x
larger in raw magnitude than a world-space reference by construction — this is NOT evidence of
a broken shape key. Before concluding "near-singular blend matrix, shape key is broken":

1. Convert both sides of the comparison to the SAME unit space.
2. Check the blend matrix's condition number/determinant — a well-conditioned matrix (roughly
   1.0–2.5 condition number on this project's rigs) with a delta that merely "looks huge" is
   fine; a genuinely singular/near-singular matrix is the real defect to chase instead.

## Identifying the actual folding vertex subset

Use a posed-vs-rest Laplacian delta to find the top-N most-displaced vertices, then add halo
neighbors at a falloff weight (e.g. 0.4) rather than correcting the entire visually-affected
region. A corrective shape key that touches far more geometry than the actual fold is over-
scoped and risks visible artifacts outside the defect.

## Shape-Key Bake & Rest-Weight-Leak Assertion

The defect this section prevents: a shape key's Key-datablock rest/default weight (block-level
`value`, distinct from any per-clip evaluated weight sampled during a specific animation)
silently leaking a non-zero value into the exported base mesh — shipping a subtly-wrong GLB
that a self-graded harness would still call "passing." (See `doctrine.md` for why the specific
"bug-214" anecdote is flagged unlocated while this general rule is fully grounded and settled.)

**Mandatory assertion, every export:** parse the exported GLB's JSON chunk directly — via a
script sharing NO code with the Blender export path — and confirm the REST value is 0.0 for
any shape key not intentionally held active across a full clip (this project's one deliberate
exception: the wave clip's corrective key is kept at a flat 1.0 for its entire duration, because
the defect pose is held for the whole clip, not a narrow peak — measured per-clip, never
assumed). Run `scripts/assert_shape_key_rest_weight.py` as its own process, then independently
cross-check with `npx @gltf-transform/cli inspect <file>` — two independently-implemented
parsers agreeing is the gate, never the exporter's own self-report.

**Efficient-production constraint:** run the rest-weight assertion once per actual export, not
speculatively re-run against an unchanged GLB.
