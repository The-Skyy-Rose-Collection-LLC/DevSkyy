"""
Full-body skin weighting -- locked plan step, run AFTER the Phase-2 armpit
gusset (add_armpit_gusset.py, already applied and saved in
love-hurts-girl-rig.blend: 19402 verts across 7 vertex groups: Spine02,
{Left,Right}Shoulder, {Left,Right}Arm, {Left,Right}ForeArm).

Locked plan step being executed:
  Skin weighting for torso/pants (Spine chain + Hips), arms
  (Shoulder/Arm/ForeArm/Hand incl. the Phase-2 gusset gradient), legs
  (UpLeg/Leg/Foot/ToeBase), and face/neck. Feathered (smoothstep, not binary
  1.0/0.0 cutoff) blend zones at EVERY joint boundary -- explicitly
  including the jaw/neck-to-face seam (blend band width = 15% of neck bone
  rest length, centered on the jawline == neck.tail/Head.head).

Do-not-repeat (cerebrum, 2026-07-09): add_armpit_gusset.py overwrites the
.blend in place and is NOT idempotent -- a second run would double-subdivide
the gusset patch. This script NEVER re-runs that script; it only ADDS
weights for vertices the gusset did not already touch, identified simply as
"has zero existing vertex groups" (verified this session: 19402/47255 verts
already carry gusset weights). This same "already weighted -> skip" rule
also makes THIS script idempotent: a second run finds nothing left to do.

Method (generalizes the gusset's own axis-projection + smoothstep style,
not Blender auto/heat weights -- rejected: auto-weights would (a) clobber
the 7 existing gusset groups, (b) be unreliable on this input, which has 89
pre-existing non-manifold edges and 2 connected components (main body +
373-face accessory island) and a non-T/A rest pose with arms hanging at the
sides, both known heat-diffusion failure triggers, and (c) produce a
discontinuous seam against the hand-authored gusset taper):

1. Six anatomical CHAINS, each a position-continuous bone polyline (verified
   via assert_continuous below -- every bone's tail equals the next bone's
   head to <1mm):
     spine      = Hips -> Spine02 -> Spine01 -> Spine -> neck -> Head
     left_arm   = LeftShoulder -> LeftArm -> LeftForeArm -> LeftHand
     right_arm  = mirror
     left_leg   = LeftUpLeg -> LeftLeg -> LeftFoot -> LeftToeBase
     right_leg  = mirror
   (neck+Head fold into the spine chain because Spine.tail == neck.head ==
   a genuine position-continuous joint -- the "face/neck" region is just
   the last two links of the same backbone chain, and the required jaw
   boundary is simply one more internal joint on it.)

2. For every vertex NOT already gusset-weighted: find the globally nearest
   point across all 6 chain polylines (point-to-segment projection per
   bone, clamped to each bone's own [0,1]) -> assigns the vertex to exactly
   one chain and one arc-length position `s` along it (s=0 at the chain's
   first bone head, s=total_length at the last bone's tail).

3. Within that chain, smoothstep-blend `s` across every internal joint
   boundary (bone[i-1]<->bone[i]) using a symmetric band of half-width
   0.15 * min(len(bone[i-1]), len(bone[i])) (30% total width) -- EXCEPT the
   neck->Head joint (the jaw), which uses the LOCKED exact formula: total
   band width = 0.15 * len(neck), centered on neck.tail == Head.head. The
   left/right arm chains' Shoulder->Arm joint is explicitly SKIPPED here:
   that boundary is entirely owned by the Phase-2 gusset (its taper radius,
   0.24m, comfortably exceeds this joint's would-be 0.30-fraction band,
   ~0.022m, so no non-gusset vertex ever falls in range of it anyway).

4. For the two chains that branch off a parent bone rather than continuing
   it in a straight line (left/right_leg off Hips == the HIP boundary;
   left/right_arm off Spine == the SHOULDER boundary), layer one more
   smoothstep on top: project the vertex onto the axis from (closest point
   on the parent bone to the child's head) to (the child's head) -- the
   exact same axis-projection + smoothstep pattern add_armpit_gusset.py
   already used for its own torso<->arm blend -- and lerp the chain's
   `base_weights` toward 100% parent-bone as that projection approaches the
   branch root. This composition is weight-sum-preserving by construction
   (base_weights already sums to 1; branch_t*1 + (1-branch_t) == 1).

Every vertex ends with weights normalized to sum to 1.0 and at least one
non-zero group (asserted below) -- required so Plan-B keyframing (fresh
hand-authored poses, per cerebrum 2026-07-10) doesn't leave any vertex
frozen. An Armature modifier targeting GirlArmature is added if missing
(inferred-but-necessary: weights alone don't deform without it).

Verification (re-opens the SAVED file fresh, not the in-memory pre-save
state): for hip, shoulder, armpit-gusset, and jaw, sample the actual
vertices whose axis-projection/arc-length falls in the blend window, read
their REAL assigned weights from the reloaded file, and assert (a) weight
is monotonic in the projection parameter and (b) at least one sampled
vertex has a genuinely intermediate weight (not a binary 0/1 cutoff).

Run headless:
    blender --background --factory-startup --python skin_weight_body.py
"""

import json
import os
import shutil

import bpy
from mathutils import Vector

OUT_DIR = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/renders/3d/girl-love-hurts"
)
BLEND_PATH = os.path.join(OUT_DIR, "love-hurts-girl-rig.blend")
BACKUP_PATH = os.path.join(OUT_DIR, "love-hurts-girl-rig.pre-skinweight-backup.blend")

DEFAULT_BAND_FRAC = 0.30  # total band width, as a fraction of the shorter adjacent bone
JAW_BAND_FRAC = 0.15  # LOCKED: total band width = 0.15 * neck bone rest length

CHAIN_DEFS = {
    "spine": {
        "bones": ["Hips", "Spine02", "Spine01", "Spine", "neck", "Head"],
        "branch_parent": None,
    },
    "left_arm": {
        "bones": ["LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand"],
        "branch_parent": "Spine",
        "skip_internal_joint": ("LeftShoulder", "LeftArm"),  # owned by Phase-2 gusset
    },
    "right_arm": {
        "bones": ["RightShoulder", "RightArm", "RightForeArm", "RightHand"],
        "branch_parent": "Spine",
        "skip_internal_joint": ("RightShoulder", "RightArm"),
    },
    "left_leg": {
        "bones": ["LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase"],
        "branch_parent": "Hips",
    },
    "right_leg": {
        "bones": ["RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"],
        "branch_parent": "Hips",
    },
}

DEFORM_BONES = [
    "Hips",
    "Spine02",
    "Spine01",
    "Spine",
    "neck",
    "Head",
    "LeftShoulder",
    "LeftArm",
    "LeftForeArm",
    "LeftHand",
    "RightShoulder",
    "RightArm",
    "RightForeArm",
    "RightHand",
    "LeftUpLeg",
    "LeftLeg",
    "LeftFoot",
    "LeftToeBase",
    "RightUpLeg",
    "RightLeg",
    "RightFoot",
    "RightToeBase",
]
assert len(DEFORM_BONES) == 22


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def closest_point_on_segment(p, a, b):
    ab = b - a
    len2 = ab.length_squared
    if len2 < 1e-12:
        return a, 0.0, (p - a).length
    t = (p - a).dot(ab) / len2
    t_clamped = max(0.0, min(1.0, t))
    closest = a + ab * t_clamped
    return closest, t_clamped, (p - closest).length


def nearest_on_polyline(p, points):
    """points: list of connected Vectors (chain[0].head, chain[0].tail == chain[1].head, ...).
    Returns (dist, seg_index, t_local) for the globally closest segment."""
    best = None
    for i in range(len(points) - 1):
        _, t, dist = closest_point_on_segment(p, points[i], points[i + 1])
        if best is None or dist < best[0]:
            best = (dist, i, t)
    return best


def band_half_width(chain_name, i, bones, bone_len):
    a, b = bones[i - 1], bones[i]
    if (a, b) == ("neck", "Head"):
        return JAW_BAND_FRAC * bone_len["neck"] / 2.0
    return DEFAULT_BAND_FRAC * min(bone_len[a], bone_len[b]) / 2.0


def chain_base_weights(chain_name, chain, s, seg_idx, bone_len):
    bones = chain["bones"]
    cum = chain["cum"]
    w = {bones[seg_idx]: 1.0}
    skip = chain.get("skip_internal_joint")
    for i in range(1, len(bones)):
        a, b = bones[i - 1], bones[i]
        if skip == (a, b):
            continue
        joint_s = cum[i]
        hw = band_half_width(chain_name, i, bones, bone_len)
        if joint_s - hw <= s <= joint_s + hw:
            local_t = (s - (joint_s - hw)) / (2 * hw)
            bw = smoothstep(local_t)
            w = {a: 1.0 - bw, b: bw}
    return w


def build_chains(bone_head, bone_tail, bone_len):
    chains = {}
    for name, d in CHAIN_DEFS.items():
        bones = d["bones"]
        points = [bone_head[bones[0]]]
        for bn in bones:
            points.append(bone_tail[bn])
        cum = [0.0]
        for bn in bones:
            cum.append(cum[-1] + bone_len[bn])
        chains[name] = {
            "bones": bones,
            "branch_parent": d.get("branch_parent"),
            "skip_internal_joint": d.get("skip_internal_joint"),
            "points": points,
            "cum": cum,
        }
    return chains


def assert_continuous(bone_tail, bone_head, a, b, eps=1e-3):
    d = (bone_tail[a] - bone_head[b]).length
    assert d < eps, f"chain discontinuity {a}->{b}: gap {d}"


def get_weight(mesh_obj, vidx, group_name):
    if group_name not in mesh_obj.vertex_groups:
        return 0.0
    gi = mesh_obj.vertex_groups[group_name].index
    for g in mesh_obj.data.vertices[vidx].groups:
        if g.group == gi:
            return g.weight
    return 0.0


def do_weighting():
    if not os.path.exists(BACKUP_PATH):
        shutil.copy2(BLEND_PATH, BACKUP_PATH)
        print(f"Backup created: {BACKUP_PATH}")
    else:
        print(f"Backup already exists, not overwriting: {BACKUP_PATH}")

    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    arm_obj = bpy.data.objects["GirlArmature"]
    mesh_obj = bpy.data.objects["Mesh1.0"]

    bone_head = {b.name: Vector(b.head_local) for b in arm_obj.data.bones}
    bone_tail = {b.name: Vector(b.tail_local) for b in arm_obj.data.bones}
    bone_len = {b.name: b.length for b in arm_obj.data.bones}

    assert_continuous(bone_tail, bone_head, "Hips", "Spine02")
    assert_continuous(bone_tail, bone_head, "Spine02", "Spine01")
    assert_continuous(bone_tail, bone_head, "Spine01", "Spine")
    assert_continuous(bone_tail, bone_head, "Spine", "neck")
    assert_continuous(bone_tail, bone_head, "neck", "Head")
    for side in ("Left", "Right"):
        assert_continuous(bone_tail, bone_head, f"{side}Shoulder", f"{side}Arm")
        assert_continuous(bone_tail, bone_head, f"{side}Arm", f"{side}ForeArm")
        assert_continuous(bone_tail, bone_head, f"{side}ForeArm", f"{side}Hand")
        assert_continuous(bone_tail, bone_head, f"{side}UpLeg", f"{side}Leg")
        assert_continuous(bone_tail, bone_head, f"{side}Leg", f"{side}Foot")
        assert_continuous(bone_tail, bone_head, f"{side}Foot", f"{side}ToeBase")
    print("chain continuity verified for all 6 chains")

    for name in DEFORM_BONES:
        if name not in mesh_obj.vertex_groups:
            mesh_obj.vertex_groups.new(name=name)
    pre_existing_groups = sorted(vg.name for vg in mesh_obj.vertex_groups)
    print(f"vertex groups after ensure ({len(pre_existing_groups)}): {pre_existing_groups}")

    # Determined ONCE, from the true Phase-2-only state, then persisted as a
    # custom ID property -- NOT recomputed as "len(v.groups) > 0" on every
    # run. After this script's first run every vertex has a group, so that
    # test would silently widen to "all 47255 verts" on a second run,
    # clobbering the marker verification depends on (it distinguishes
    # gusset-preserved vertices from this pass's own assignments -- both
    # populations can carry weight on the same bone name, e.g. Hips is
    # written by both the spine-chain internal joint AND the leg-chain
    # branch blend, so "nonzero weight on bone X" alone can't disambiguate
    # them). This is what makes a second run a true no-op rather than a run
    # that leaves weights untouched but corrupts verification's bookkeeping.
    if "gusset_vertex_indices" in mesh_obj:
        gusset_verts = set(json.loads(mesh_obj["gusset_vertex_indices"]))
        print(f"gusset_vertex_indices already persisted, reusing: {len(gusset_verts)} verts")
    else:
        gusset_verts = set(v.index for v in mesh_obj.data.vertices if len(v.groups) > 0)
        mesh_obj["gusset_vertex_indices"] = json.dumps(sorted(gusset_verts))
        print(
            f"pre-existing weighted verts (Phase-2 gusset, preserved untouched): {len(gusset_verts)}"
        )

    chains = build_chains(bone_head, bone_tail, bone_len)

    # Seam fix: the leg/arm chains' branch blend (above) bleeds Hips/Spine
    # INTO the child chain as a vertex nears the joint -- but a spine-chain
    # vertex on the OTHER side of the SAME joint, one nearest-polyline tie
    # away, got zero consideration of that axis at all, landing at a pure
    # {Hips: 1.0} (or {Spine: ...}) while a mesh-adjacent, leg-chain-assigned
    # vertex a few millimeters away already carries a large UpLeg/Shoulder
    # share -- a hard seam at the chain-classification boundary itself, even
    # though each side's OWN transition is individually smooth (found via
    # advisor review + confirmed empirically: two verts 0.0074m apart showed
    # Hips 1.0 vs 0.4248 pre-fix). Fix: apply the identical axis-projection
    # formula, symmetrically, to spine-chain vertices too, shifting weight
    # from the parent bone (Hips or Spine) to the branch's child bone by the
    # same branch_t -- both sides of the seam then share one continuous
    # field instead of two independently-smooth-but-discontinuous ones.
    reverse_branches = []
    for parent_bone, child_bone in (
        ("Hips", "LeftUpLeg"),
        ("Hips", "RightUpLeg"),
        ("Spine", "LeftShoulder"),
        ("Spine", "RightShoulder"),
    ):
        child_head = bone_head[child_bone]
        anchor, _, _ = closest_point_on_segment(
            child_head, bone_head[parent_bone], bone_tail[parent_bone]
        )
        axis = child_head - anchor
        reverse_branches.append((parent_bone, child_bone, anchor, axis, axis.length_squared))

    processed = 0
    per_chain_count = dict.fromkeys(chains, 0)
    for v in mesh_obj.data.vertices:
        # Skip Phase-2 gusset verts (preserve untouched) AND any vertex this
        # SAME script already weighted on a prior run (true no-op rerun --
        # the computation is deterministic so recomputing would land on the
        # identical value anyway, but skipping makes that explicit rather
        # than relying on REPLACE-semantics coincidence).
        if v.index in gusset_verts or len(v.groups) > 0:
            continue
        p = v.co.copy()

        best_chain_name, best_dist, best_seg, best_t = None, None, None, None
        for cname, c in chains.items():
            dist, seg, t = nearest_on_polyline(p, c["points"])
            if best_dist is None or dist < best_dist:
                best_dist, best_chain_name, best_seg, best_t = dist, cname, seg, t

        chain = chains[best_chain_name]
        bones = chain["bones"]
        seg_len = bone_len[bones[best_seg]]
        s = chain["cum"][best_seg] + best_t * seg_len
        base_w = chain_base_weights(best_chain_name, chain, s, best_seg, bone_len)

        branch_parent = chain["branch_parent"]
        if branch_parent is not None:
            child_head = bone_head[bones[0]]
            anchor, _, _ = closest_point_on_segment(
                child_head, bone_head[branch_parent], bone_tail[branch_parent]
            )
            axis = child_head - anchor
            axis_len2 = axis.length_squared
            if axis_len2 > 1e-10:
                t_branch = (p - anchor).dot(axis) / axis_len2
                branch_t = smoothstep(t_branch)
            else:
                branch_t = 1.0
            final_w = {bn: wt * branch_t for bn, wt in base_w.items()}
            final_w[branch_parent] = final_w.get(branch_parent, 0.0) + (1.0 - branch_t)
        else:
            final_w = base_w

        if best_chain_name == "spine":
            # Symmetric seam fix (see comment above reverse_branches):
            # shift weight from the parent bone to the branch's child bone
            # by the SAME branch_t the child-chain side already uses, so
            # both sides of the hip/shoulder seam share one continuous
            # field. A no-op wherever the parent bone isn't present or the
            # vertex is nowhere near that branch (branch_t -> 0).
            for parent_bone, child_bone, anchor, axis, axis_len2 in reverse_branches:
                if parent_bone not in final_w or axis_len2 <= 1e-10:
                    continue
                t_branch = (p - anchor).dot(axis) / axis_len2
                branch_t = smoothstep(t_branch)
                if branch_t <= 1e-9:
                    continue
                shift = final_w[parent_bone] * branch_t
                final_w[parent_bone] -= shift
                final_w[child_bone] = final_w.get(child_bone, 0.0) + shift

        total = sum(final_w.values())
        assert total > 1e-6, f"vertex {v.index}: zero total weight ({best_chain_name})"
        for bn, wt in final_w.items():
            wt_norm = wt / total
            if wt_norm > 1e-6:
                mesh_obj.vertex_groups[bn].add([v.index], wt_norm, "REPLACE")

        processed += 1
        per_chain_count[best_chain_name] += 1

    print(f"newly weighted verts: {processed}")
    print(f"per-chain breakdown: {per_chain_count}")

    has_arm_mod = any(m.type == "ARMATURE" for m in mesh_obj.modifiers)
    if not has_arm_mod:
        mod = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
        mod.object = arm_obj
        mod.use_vertex_groups = True
        print("Added Armature modifier targeting GirlArmature (was missing)")
    else:
        print("Armature modifier already present")

    zero_weight_verts = 0
    bad_sum_verts = 0
    max_sum_err = 0.0
    for v in mesh_obj.data.vertices:
        if len(v.groups) == 0:
            zero_weight_verts += 1
            continue
        s = sum(g.weight for g in v.groups)
        err = abs(s - 1.0)
        max_sum_err = max(max_sum_err, err)
        if err > 1e-4:
            bad_sum_verts += 1
    print(f"zero-weight verts (must be 0): {zero_weight_verts}")
    print(f"bad-normalization verts (must be 0, max_err={max_sum_err:.2e}): {bad_sum_verts}")
    assert zero_weight_verts == 0, "some vertices have no deform weight"
    assert bad_sum_verts == 0, "some vertices' weights don't sum to 1.0"

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"SAVED: {BLEND_PATH}")

    return {
        "gusset_verts_preserved": len(gusset_verts),
        "newly_weighted_verts": processed,
        "per_chain_count": per_chain_count,
        "total_verts": len(mesh_obj.data.vertices),
    }


def classify_all_vertices(mesh_obj, chains, bone_len, gusset_verts):
    """Mirrors the weighting pass's own chain classification (nearest point
    across all 6 chain polylines) for every non-gusset vertex. Verification
    filters on this -- NOT on "does bone X carry nonzero weight" -- because
    several bones are written by TWO independent, unrelated pathways: Hips
    gets weight from both the spine-chain's own Hips<->Spine02 internal
    joint AND the leg-chains' hip branch blend; Spine gets weight from both
    its own spine-chain neighbors AND the arm-chains' shoulder branch blend;
    Shoulder gets weight from both the arm-chain branch blend AND the
    Phase-2 gusset. Without this filter a vertex weighted by the WRONG
    pathway, but with a coincidentally similar axis-projection value, lands
    in the sorted sample and breaks the monotonicity check (this is exactly
    what the first run of this script's verification hit -- see memory.md)."""
    assignment = {}
    for v in mesh_obj.data.vertices:
        if v.index in gusset_verts:
            continue
        p = v.co
        best_chain_name, best_dist, best_seg, best_t = None, None, None, None
        for cname, c in chains.items():
            dist, seg, t = nearest_on_polyline(p, c["points"])
            if best_dist is None or dist < best_dist:
                best_dist, best_chain_name, best_seg, best_t = dist, cname, seg, t
        bones = chains[best_chain_name]["bones"]
        s = chains[best_chain_name]["cum"][best_seg] + best_t * bone_len[bones[best_seg]]
        assignment[v.index] = (best_chain_name, best_seg, s)
    return assignment


def verify_branch_boundary(
    mesh_obj,
    bone_head,
    bone_tail,
    bone_len,
    chains,
    child_bone,
    parent_bone,
    chain_name,
    assignment,
    label,
):
    """Restricted to seg==0 (nearest bone in the chain is the branch's own
    root bone, e.g. LeftUpLeg for the hip, LeftShoulder for the shoulder)
    AND s strictly before the NEXT internal joint's own blend band (e.g.
    before the knee, for hip; before the armpit-gusset, for shoulder).
    Vertices further down the chain, or already inside the next joint's
    band, get their weight on the root bone from THAT joint's transition
    (chain_base_weights only ever splits between the two bones straddling
    whichever internal joint a vertex is near) -- including them would
    compare an unrelated joint's transition against this one's axis and
    falsely read as non-monotonic (this is exactly what an earlier version
    of this check hit on the hip boundary -- see memory.md)."""
    chain = chains[chain_name]
    bones = chain["bones"]
    skip = chain.get("skip_internal_joint")
    if skip == (bones[0], bones[1]):
        # The Shoulder->Arm joint is gusset-owned and never blended in
        # chain_base_weights (the loop `continue`s past it) -- every seg==0
        # vertex is pure {root_bone: 1.0} all the way to s==cum[1], so there
        # is nothing to guard against here and trimming would only shrink
        # the sample for no safety reason.
        safe_s_max = chain["cum"][1]
    else:
        safe_s_max = chain["cum"][1] - band_half_width(chain_name, 1, bones, bone_len)

    child_head = bone_head[child_bone]
    anchor, _, _ = closest_point_on_segment(
        child_head, bone_head[parent_bone], bone_tail[parent_bone]
    )
    axis = child_head - anchor
    axis_len2 = axis.length_squared
    samples = []
    for vidx, (cname, seg, s) in assignment.items():
        if cname != chain_name or seg != 0 or s >= safe_s_max:
            continue
        v = mesh_obj.data.vertices[vidx]
        t = (v.co - anchor).dot(axis) / axis_len2
        w_parent = get_weight(mesh_obj, vidx, parent_bone)
        w_child = get_weight(mesh_obj, vidx, child_bone)
        samples.append((t, w_parent, w_child, vidx))
    samples.sort(key=lambda x: x[0])
    return _judge(label, samples)


def verify_internal_boundary(
    mesh_obj, chains, bone_len, chain_name, bone_before, bone_after, assignment, label
):
    chain = chains[chain_name]
    bones = chain["bones"]
    i = bones.index(bone_after)
    joint_s = chain["cum"][i]
    hw = band_half_width(chain_name, i, bones, bone_len)
    window = hw * 2.5

    samples = []
    for vidx, (cname, _seg, s) in assignment.items():
        if cname != chain_name:
            continue
        if joint_s - window <= s <= joint_s + window:
            w_before = get_weight(mesh_obj, vidx, bone_before)
            w_after = get_weight(mesh_obj, vidx, bone_after)
            samples.append((s, w_before, w_after, vidx))
    samples.sort(key=lambda x: x[0])
    return _judge(label, samples, extra={"joint_s": joint_s, "band_half_width": hw})


def verify_gusset_boundary(mesh_obj, bone_head, side, gusset_verts):
    shoulder_head = bone_head[f"{side}Shoulder"]
    arm_head = bone_head[f"{side}Arm"]
    axis = arm_head - shoulder_head
    axis_len2 = axis.length_squared
    samples = []
    for vidx in gusset_verts:
        # Gate to verts THIS side's gusset pass actually touched -- Spine02
        # alone is shared by both sides, so a side-specific bone must also
        # carry weight (guards against the other side's gusset-zone verts,
        # whose t computed against THIS side's axis can coincidentally fall
        # inside the sample window).
        is_this_side = (
            get_weight(mesh_obj, vidx, f"{side}Shoulder") > 1e-6
            or get_weight(mesh_obj, vidx, f"{side}Arm") > 1e-6
            or get_weight(mesh_obj, vidx, f"{side}ForeArm") > 1e-6
        )
        if not is_this_side:
            continue
        v = mesh_obj.data.vertices[vidx]
        t = (v.co - shoulder_head).dot(axis) / axis_len2
        w_torso = get_weight(mesh_obj, vidx, "Spine02") + get_weight(
            mesh_obj, vidx, f"{side}Shoulder"
        )
        w_arm = get_weight(mesh_obj, vidx, f"{side}Arm") + get_weight(
            mesh_obj, vidx, f"{side}ForeArm"
        )
        samples.append((t, w_torso, w_arm, vidx))
    samples.sort(key=lambda x: x[0])
    return _judge(f"armpit_gusset_{side}", samples)


def _judge(label, samples, extra=None, tol=1e-6):
    result = {"label": label, "n_samples": len(samples)}
    if extra:
        result.update(extra)
    if len(samples) < 3:
        result["pass"] = False
        result["reason"] = f"too few samples in band ({len(samples)}) to judge"
        return result

    parent_w = [s[1] for s in samples]
    child_w = [s[2] for s in samples]

    non_increasing = all(parent_w[i] <= parent_w[i - 1] + tol for i in range(1, len(parent_w)))
    non_decreasing = all(child_w[i] >= child_w[i - 1] - tol for i in range(1, len(child_w)))
    has_intermediate = any(0.15 < w < 0.85 for w in child_w)
    max_step = max((abs(child_w[i] - child_w[i - 1]) for i in range(1, len(child_w))), default=0.0)
    no_hard_jump = max_step < 0.5

    ok = non_increasing and non_decreasing and has_intermediate and no_hard_jump
    result.update(
        {
            "pass": ok,
            "non_increasing_parent": non_increasing,
            "non_decreasing_child": non_decreasing,
            "has_intermediate_weight": has_intermediate,
            "max_consecutive_step": round(max_step, 4),
            "no_hard_jump": no_hard_jump,
            "child_weight_range": [round(min(child_w), 4), round(max(child_w), 4)],
        }
    )
    return result


def do_verification():
    """Re-opens the SAVED file fresh (not the in-memory pre-save state)."""
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    arm_obj = bpy.data.objects["GirlArmature"]
    mesh_obj = bpy.data.objects["Mesh1.0"]

    bone_head = {b.name: Vector(b.head_local) for b in arm_obj.data.bones}
    bone_tail = {b.name: Vector(b.tail_local) for b in arm_obj.data.bones}
    bone_len = {b.name: b.length for b in arm_obj.data.bones}
    chains = build_chains(bone_head, bone_tail, bone_len)

    gusset_verts = set(json.loads(mesh_obj["gusset_vertex_indices"]))
    assignment = classify_all_vertices(mesh_obj, chains, bone_len, gusset_verts)
    print(f"re-classified {len(assignment)} non-gusset verts for verification")

    results = {}

    hip_l = verify_branch_boundary(
        mesh_obj,
        bone_head,
        bone_tail,
        bone_len,
        chains,
        "LeftUpLeg",
        "Hips",
        "left_leg",
        assignment,
        "hip_left",
    )
    hip_r = verify_branch_boundary(
        mesh_obj,
        bone_head,
        bone_tail,
        bone_len,
        chains,
        "RightUpLeg",
        "Hips",
        "right_leg",
        assignment,
        "hip_right",
    )
    results["hip"] = {"left": hip_l, "right": hip_r, "pass": hip_l["pass"] and hip_r["pass"]}

    sh_l = verify_branch_boundary(
        mesh_obj,
        bone_head,
        bone_tail,
        bone_len,
        chains,
        "LeftShoulder",
        "Spine",
        "left_arm",
        assignment,
        "shoulder_left",
    )
    sh_r = verify_branch_boundary(
        mesh_obj,
        bone_head,
        bone_tail,
        bone_len,
        chains,
        "RightShoulder",
        "Spine",
        "right_arm",
        assignment,
        "shoulder_right",
    )
    results["shoulder"] = {"left": sh_l, "right": sh_r, "pass": sh_l["pass"] and sh_r["pass"]}

    gu_l = verify_gusset_boundary(mesh_obj, bone_head, "Left", gusset_verts)
    gu_r = verify_gusset_boundary(mesh_obj, bone_head, "Right", gusset_verts)
    results["armpit_gusset"] = {"left": gu_l, "right": gu_r, "pass": gu_l["pass"] and gu_r["pass"]}

    jaw = verify_internal_boundary(
        mesh_obj, chains, bone_len, "spine", "neck", "Head", assignment, "jaw"
    )
    results["jaw"] = {"combined": jaw, "pass": jaw["pass"]}

    zero_weight_verts = sum(1 for v in mesh_obj.data.vertices if len(v.groups) == 0)
    bad_sum_verts = sum(
        1
        for v in mesh_obj.data.vertices
        if len(v.groups) > 0 and abs(sum(g.weight for g in v.groups) - 1.0) > 1e-4
    )
    has_arm_mod = any(m.type == "ARMATURE" for m in mesh_obj.modifiers)

    results["mesh_invariants"] = {
        "zero_weight_verts": zero_weight_verts,
        "bad_normalization_verts": bad_sum_verts,
        "armature_modifier_present": has_arm_mod,
        "pass": zero_weight_verts == 0 and bad_sum_verts == 0 and has_arm_mod,
    }

    overall_pass = all(
        results[k]["pass"] for k in ("hip", "shoulder", "armpit_gusset", "jaw", "mesh_invariants")
    )
    results["overall_pass"] = overall_pass
    return results


def main():
    weighting_summary = do_weighting()
    verification = do_verification()

    print("\n" + "=" * 78)
    print("VERIFICATION (re-loaded saved file)")
    print("=" * 78)
    for key in ("hip", "shoulder", "armpit_gusset", "jaw", "mesh_invariants"):
        print(f"{key}: PASS={results_pass(verification[key])}")
    print(f"OVERALL: {'PASS' if verification['overall_pass'] else 'FAIL'}")
    print("=" * 78)

    print(
        "\nRESULT_JSON "
        + json.dumps({"weighting": weighting_summary, "verification": verification})
    )


def results_pass(d):
    return d.get("pass")


if __name__ == "__main__":
    main()
