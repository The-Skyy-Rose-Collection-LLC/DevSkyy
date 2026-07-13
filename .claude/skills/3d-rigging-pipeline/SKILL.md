---
name: 3d-rigging-pipeline
description: Headless Blender/bpy authoring pipeline for character rigging, corrective shape keys, cross-armature retargeting, and glTF export compression -- the AUTHORING half of SkyyRose's 3D character pipeline (distinct from threejs-animation's RUNTIME morph-wiring during playback, and from render-QA skills' post-export fidelity grading). Use when doing headless Blender/bpy rigging, fixing skin-weight or shape-key defects, retargeting -- or evaluating whether to retarget -- a skeleton onto a new character, or exporting/compressing a rigged GLB for the mascot, Love Hurts Girl, or any future SkyyRose character.
---

# 3D Rigging Pipeline (Blender/bpy Authoring)

## Scope boundary -- read this before anything else

- **This skill = AUTHORING.** Headless Blender/bpy: computing, baking, and exporting a
  correction or a rig.
- **`threejs-animation` = RUNTIME.** Wiring morph-target influence during three.js playback
  in the browser. It already names this skill by this exact name for the Blender-side half
  of the same problem (`threejs-immersive.md` in `skyyrose-wp-platform` cross-references it).
- **Render-QA / mockup-pipeline skills = POST-EXPORT.** Output-fidelity grading after a GLB
  already exists.
- Hand off at the GLB file boundary. Never duplicate another skill's half of the problem.

## Non-negotiable gates

Every phase of a rig build obeys `reference/doctrine.md` in full: numeric gates only (a
printed number from a real script run this session, never eyeballed or assumed), and
verification must come from a source structurally independent of whatever built the artifact
being checked -- never a harness grading its own output.

## Quick start -- locating a mesh's shape keys in bpy

```python
import bpy
mesh_obj = bpy.data.objects["YourMesh"]
if mesh_obj.data.shape_keys:
    for kb in mesh_obj.data.shape_keys.key_blocks:
        print(kb.name, kb.value)  # kb.value == REST/default weight -- must be 0.0 unless
                                   # this key is deliberately held active for a full clip
```

This is illustrative only -- the full corrective-shape-key computation is in
`reference/shape-keys.md`, not here.

## Reference files

| Read this | For |
|---|---|
| `reference/doctrine.md` | The numeric-gate + independent-verification rule every other file inherits |
| `reference/shape-keys.md` | Corrective/pose-driven shape keys for LBS candy-wrapper collapse, plus the rest-weight-leak export assertion |
| `reference/retargeting.md` | Local-Space Copy Rotation retargeting AND the mandatory rest-direction precondition gate that a real run already needed |
| `reference/export-pipeline.md` | The confirmed gltf-transform compression sequence and its `--formats` gotcha |
| `reference/love-hurts-worked-example.md` | The actual, currently-on-disk Love Hurts Girl build -- real scripts, not a fabricated phase count |

`scripts/` holds the runnable checks each reference file calls out by name.

## What this skill will not do

It will not assert a bug ID, a script's behavior, or a "confirmed" numeric result that wasn't
re-derived from a real file or a real script run in the authoring session that touched this
skill. Every reference file below says explicitly which of its claims are grounded on-disk
and which are flagged as unverified -- carry that distinction forward, don't flatten it.
