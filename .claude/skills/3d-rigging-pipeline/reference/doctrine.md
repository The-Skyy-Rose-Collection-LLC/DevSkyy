# Non-Negotiable Doctrine — Numeric Gates & the Self-Grading Trap

Every other reference file in this skill inherits this rule. Stated once, referenced
everywhere: no phase advances on an assumed or eyeballed number, and no verification counts if
it was produced by the same code path (or a harness that pre-mutated state) that built the
artifact being checked.

## The numeric-gate rule

Every bone angle, vertex delta, shape-key weight, texture dimension, and file size that a
phase depends on must be a printed number from an actual script run in the CURRENT authoring
session — never eyeballed, never assumed, never carried forward unchecked from a prior
session's writeup. If you haven't run the measurement this session, you don't have the number.

## The self-grading trap — two precedents, two different grounding strengths

Stated honestly as such, not flattened into one confident narrative:

**(a) Fully grounded, files confirmed on disk.** `renders/3d/girl-love-hurts/add_armpit_gusset.py`
is non-idempotent — its internal assert diffs against its OWN run's baseline, so a second run
on an already-gusseted file would still pass while silently saving a wrong, double-gusseted
mesh (`.wolf/cerebrum.md`, 2026-07-09 entry). The actual verification used was an EXTERNAL
`.blend1` auto-backup md5 compared against `love-hurts-girl-rig.pre-gusset-backup.blend` — a
file outside the script's own control, proving the script ran exactly once.

**(b) Doctrine-level only, specific anecdote unlocated.** An earlier version of this project's
own planning brief described a harness that allegedly zeroed a shape key's rest weight BEFORE
its own test run, calling it "bug-214." That specific incident has no matching entry in this
worktree's `.wolf/buglog.json` and no in-repo text corroborates that exact mechanism — treat it
as illustrative, not a located incident. What IS grounded and load-bearing: a shape key's
rest/default weight must be verified as exactly 0.0 by parsing the exported GLB JSON directly,
never inferred from runtime playback (this project's `skyyrose-wp-platform` theme skill,
`threejs-immersive.md`, states this independently). Ship the general rule as settled; don't
resurrect the specific harness anecdote as fact.

## The rule itself

The verification source must be structurally independent of the code path that produced the
artifact — a different script, a different tool, or a raw-format parse of the final output
file. Never the same function or harness grading its own output.

**Acceptable independent authorities:**
- A direct GLB JSON/binary-chunk parse via a script that never imports the exporter's code.
- A fresh bpy depsgraph evaluation (not the transform math re-derived by hand).
- `npx @gltf-transform/cli inspect` output (a bare `gltf-transform` binary does not resolve in
  this environment — confirmed this session; always invoke via the scoped npx package).
- A freshly rendered image read via vision — never a reused, stale render from an earlier
  attempt.
- A Context7 doc lookup for spec/API conformance (bpy `Key`/shape-key semantics, glTF morph
  target spec, Copy Rotation constraint `target_space`/`owner_space` enum values).

## Efficient-production constraint

Batch multiple numeric gates for one phase into one script invocation / one headless Blender
session. Redundant Blender process spin-up is this pipeline's single biggest token and wall-
clock cost — a phase that needs three numbers should print three numbers from one `blender
--background --python` run, not three separate launches.
