# Cross-Armature Retargeting — Local-Space Copy Rotation, Gated

Applies `doctrine.md`'s numeric-gate and independent-verification rules throughout. Uses the
Love Hurts Girl case as its worked precedent — a gate correctly REJECTING an incompatible
retarget, not a success story. Read `love-hurts-worked-example.md` for the full build; this
file is the method + gate in isolation.

## The method — necessary, not sufficient

Local-Space Copy Rotation constraints, matched bone-by-bone by hierarchy position (not
world-space bone matching), are invariant to PROPORTION/scale differences between two rigs
sharing the same parent-child bone hierarchy. This is the correct method for same-hierarchy FK
retargeting — but hierarchy match alone is not sufficient to guarantee a good result.

## The mandatory precondition gate — a real run already needed this

Local-space rotation is invariant to proportion differences but NOT to rest-orientation
divergence — two hierarchy-identical armatures can still have wildly different bone rest
directions. Run a per-bone rest-pose direction-angle gate BEFORE any constraint setup, ever:
compute the world-space head-to-tail unit-vector angle between each corresponding bone pair
(both armatures root-scale-normalized to 1.0, both at rest pose, root world transform =
identity) and check it against a category threshold.

**This already happened, for real, on this project** (`gate_bone_direction.py`, confirmed on
disk at `renders/3d/girl-love-hurts/`, real captured output, `.wolf/buglog.json` bug-195):
comparing the mascot's `skyy.glb` rig against the Love Hurts Girl rig, **15 of 24 bones failed**
a 10°-critical / 20°-lenient threshold, including `Hips` at 97.4°, `LeftForeArm` at 126.2°, and
`RightForeArm` at 130.5° — the last two near-inverted. The category thresholds:

| Category | Bones | Threshold |
|---|---|---|
| Critical (fails the whole gate) | spine chain, neck/Head, upper-arm, forearm, up-leg, leg | 10° |
| Lenient (reported, non-critical) | shoulder, foot, toe-base, hand | 20° |
| Inferred (not in the locked spec, defaulted to lenient) | head auxiliary bones (`head_end`, `headfront`) — flagged as inferred in the report, never counted toward a critical failure | 20° |

## The hard-stop rule this precedent establishes

A failed rest-direction gate is a hard stop that redirects to a DIFFERENT authoring method for
that specific rig pair/clip — not something to patch with looser thresholds or extra
correction bones. On the Love Hurts Girl build, this meant abandoning Local-Space Copy Rotation
retargeting for the mascot→girl walk clip and pivoting to a fresh, hand-keyframed walk cycle
authored directly on the girl's own rig instead (8–16 hand-placed pose keys).

**This falsifies retargeting for the SPECIFIC rig pair that failed — it does not invalidate the
method in general.** A future character whose rig is both hierarchy-identical AND rest-
direction-compatible with an existing animated rig remains a valid retargeting candidate.
Don't let this precedent get paraphrased into "retargeting doesn't work here" as a blanket rule.

## Running the gate

`scripts/retarget_local_space_gate.py` generalizes the real, already-executed
`gate_bone_direction.py` into a path-parameterized, reusable tool — adapted from a working
implementation, not invented from scratch. Run it headless (`blender --background --python`)
for any new rig pair before writing a single line of constraint-setup code. Confirm Copy
Rotation's `target_space`/`owner_space` = `'LOCAL'` enum semantics via Context7 before writing
the constraint code itself — don't rely on memory for the exact enum string.
