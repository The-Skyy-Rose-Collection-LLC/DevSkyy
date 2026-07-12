# Worked Example: Love Hurts Girl Build — and the No-Stale-Premises Rule

Applies `doctrine.md`'s numeric-gate and independent-verification rules throughout.

## Correcting the record — there is no "9-phase plan" document

An earlier planning pass for this build referenced a "9-phase locked plan." No document by
that name, or any numbered-phase plan for this build, exists anywhere in this repository — the
authoritative source is the 4 real scripts on disk plus `.wolf/cerebrum.md`'s Decision Log and
`.wolf/buglog.json` bug-195/bug-196, all read directly this session. If a future reference to
"the 9-phase plan" shows up in this skill or elsewhere, it's a fabrication and should be removed.

## The actual on-disk build (`renders/3d/girl-love-hurts/`)

Four pipeline scripts, confirmed present this session, plus their output artifacts
(`love-hurts-girl-rig.blend`/`.glb`, `love-hurts-girl-rig.pre-gusset-backup.blend`,
`verify_front.png`/`verify_side.png`/`verify_montage.png`):

1. **`build_girl_rig.py`** — builds a FRESH 24-bone skeleton, hierarchy-matched to `skyy.glb`
   (same 24 bone names and parent-child order, no finger chain — `Hand` is the end effector),
   but positioned at the girl mesh's OWN geometry landmarks derived from her actual vertex
   data. Its own docstring states explicitly this is NOT copying the mascot's bind-pose
   numbers — it does not use `retargeting.md`'s Copy Rotation method at all; it constructs
   bones directly from landmark geometry.
2. **`gate_bone_direction.py`** — tests whether a SEPARATE walk-clip retarget onto this new rig
   is viable. It FAILED (bug-195: 15/24 bones over threshold, see `retargeting.md`) → Plan B
   chosen: a hand-keyframed walk cycle authored directly on the girl's own rig (8–16 pose
   keys), no retargeting for that clip.
3. **`add_armpit_gusset.py`** — mesh modification separating the arm from the pants at the
   armpit via 2–3 new edge loops (a smooth-weighted gusset panel, not a rip-and-leave-open
   approach). Non-idempotent (see `doctrine.md`'s precedent (a)) — externally md5-verified
   against `love-hurts-girl-rig.pre-gusset-backup.blend`, never re-run blind.
4. **`skin_weight_body.py`** — full-body skin weighting (torso/pants, arms including the
   gusset gradient, legs, face/neck), feathered smoothstep blend zones at every joint boundary
   including the jaw/neck-to-face seam. Its own verification pass had a real bug (bug-196,
   below), now fixed.

## Reuse-vs-re-derive table

Per the no-stale-premises rule below: state plainly which prior artifact stays valid to reuse
as-is vs. which must be freshly re-measured before the next script runs.

| Artifact | Reuse as-is? | Re-derive when |
|---|---|---|
| `love-hurts-girl-rig.blend`'s skeleton (from `build_girl_rig.py`) | Yes, until either rig file changes | Either the girl mesh or `skyy.glb` changes at all |
| `gate_bone_direction.py`'s 15/24-fail result | No — never assumed still-failing (or still-passing) from a prior session's number | Every time before committing to retargeting for any rig pair, run fresh |
| The armpit gusset (`add_armpit_gusset.py`'s edit) | Yes, once verified via the external `.blend1` md5 check | If you suspect it ran twice, or before any re-run — check the md5 first, always |
| Skin weights (`skin_weight_body.py`) | Yes, once its own (fixed) verification passes | If the gusset or skeleton changes after weighting, re-weight and re-verify |

## The no-stale-premises rule

Every stage re-measures its own claims against the CURRENT state of the actual `.blend`/`.glb`
file. It never inherits a claim from a previous stage's writeup without re-running that
measurement.

**Primary grounded precedent (bug-195, same pipeline as above, not an analogy):** the build
assumed hierarchy-matched armatures were retarget-compatible. Before committing to Local-Space
Copy Rotation constraint setup, `gate_bone_direction.py` was run fresh against the CURRENT rig
files and disproved the assumption. The build correctly stopped and pivoted to Plan B rather
than proceeding on the untested premise.

**Secondary, non-identical precedent, flagged as an analogy, not the same case:** bug-194's
scope error (see `shape-keys.md`) — a task assumed all 5 gesture clips needed a fix; fresh
renders showed only 1 did. This demonstrates re-verifying an inherited assumption against fresh
evidence within one investigation — it is not a cross-session premise-staleness case.

**A citation to avoid:** an earlier planning brief referenced a "bug-215" for a cross-session
premise-staleness failure. That ID has zero references anywhere in this repository after a
full grep of `.wolf/buglog.json`, `.wolf/cerebrum.md`, `.wolf/memory.md`, and all tracked
`.md`/`.json`/`.py`/`.js` files. Don't present bug-194 or bug-195 as a match for it — bug-195 is
cited above as the strongest available grounded instance of this section's general discipline,
not as a stand-in for an unlocated citation.

## A related, real bug in the verification layer itself (bug-196)

`skin_weight_body.py`'s own first self-check reported false FAILs on monotonic weight
transitions at hip/shoulder/gusset boundaries — not because the weighting math was wrong
(smoothstep is monotonic by construction), but because the verification sampled ALL vertices
with nonzero weight on a bone, mixing two independently-monotonic populations (a bone can
legitimately receive weight from two unrelated joints, e.g. `Hips` from both the spine chain
AND the leg chains' hip branch). Fixed by filtering samples to the SAME chain/segment
classification the weighting pass used. A related idempotency bug — recomputing "which
vertices are pre-existing" as `len(v.groups) > 0` on every run, which silently widens after the
first run — was fixed by persisting that marker as a custom ID property, read back rather than
recomputed. This is itself an instance of `doctrine.md`'s self-grading trap: the verification
was checking its own sampling assumption, not the actual weighting formula.

## Re-derivation note

This worked example is a snapshot of the 4 scripts as they existed when read this session. If
they're edited or new ones are added, re-read them against the then-current files before
relying on this description — don't treat this file as a permanent record of an unchanging build.
