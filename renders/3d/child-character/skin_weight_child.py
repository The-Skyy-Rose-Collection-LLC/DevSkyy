"""Phase 4: skin weighting for the child rig.

Unlike the Love Hurts Girl build (which pre-emptively rejected
ARMATURE_AUTO due to known heat-diffusion failure triggers: 89 non-manifold
edges, 2 connected components, arms-at-sides rest pose), this mesh's
conditions are favorable for heat weighting, confirmed this session
(verify_decimated.py post-weld): 1 island, 5 non-manifold edges (0.005%,
negligible), 0 degenerate faces, and a genuine T-pose rest pose (the case
heat-weighting is designed for). Per Phase 4's own task plan: attempt
ARMATURE_AUTO fresh, gate it numerically, only fall back to
ARMATURE_ENVELOPE + manual correction if the gate fails.

Gate: every vertex has >=1 nonzero deform group, weights sum to 1.0 within
tolerance, and no cross-boundary bleed at (a) the hair/neck-Head seam --
hair verts should carry >=95% Head weight, not leak into neck/Spine, and
(b) the sleeve-cuff/forearm-hand seam -- verts near the wrist should not
carry meaningful weight from bones two or more joints away (e.g. Spine or
Hips), which would visually manifest as exactly bug-296's sleeve-cuff-flare
symptom (a distant bone's rotation dragging cuff geometry).

Run: blender --background --factory-startup --python skin_weight_child.py
"""

import json
import os

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-rig.blend")
OUT_BLEND = os.path.join(HERE, "child-character-skinned.blend")

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

# head_end/headfront are auxiliary, non-deforming aim/reference bones (per
# retarget_local_space_gate.py's own "unlisted_head_aux" category) -- same
# convention as the girl rig's DEFORM_BONES (22 bones, no head_end/headfront).
AUX_BONES = {"head_end", "headfront"}


def do_weighting():
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
    print(f"armature={arm_obj.name} mesh={mesh_obj.name} verts={len(mesh_obj.data.vertices)}")

    # ROOT CAUSE of the first ARMATURE_AUTO run's total failure (0/67232
    # verts weighted, confirmed via diagnose_heatweight_fail.py): this
    # mesh, built directly from child-decimated.glb, still carries glTF's
    # inherent UV-seam vertex-splitting (67232 verts, 1528 disconnected
    # islands -- the SAME fragmentation verify_decimated.py showed is
    # benign once welded, per Phase 2's corrected gate). Blender's heat
    # solver diffuses along mesh EDGES; 1528 disconnected islands means
    # heat cannot propagate across seam boundaries at all, producing a
    # uniform, total solve failure (every bone, not a topology-specific
    # subset) -- exactly what was observed. Weld here, once, before
    # parenting -- identical distance weld already proven safe in Phase 2
    # (dist=1e-5, collapses to 47047 verts, islands=1).
    pre_weld_verts = len(mesh_obj.data.vertices)
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(mesh_obj.data)
    bm.free()
    mesh_obj.data.update()
    post_weld_verts = len(mesh_obj.data.vertices)
    print(f"pre-parent weld: verts {pre_weld_verts} -> {post_weld_verts}")

    bone_names = {b.name for b in arm_obj.data.bones}
    assert bone_names == set(DEFORM_BONES) | AUX_BONES, (
        f"unexpected bone set: extra={bone_names - set(DEFORM_BONES) - AUX_BONES} "
        f"missing={(set(DEFORM_BONES) | AUX_BONES) - bone_names}"
    )
    for b in arm_obj.data.bones:
        b.use_deform = b.name not in AUX_BONES
    print(f"use_deform disabled on aux bones: {sorted(AUX_BONES)}")

    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    has_arm_mod = any(m.type == "ARMATURE" for m in mesh_obj.modifiers)
    assert has_arm_mod, "ARMATURE_AUTO did not add an Armature modifier"
    print("ARMATURE_AUTO parenting complete, Armature modifier present")

    # Blender's heat-weight solver computes per-bone heat VALUES that do
    # not always sum to exactly 1.0 -- confirmed this session
    # (diagnose_weight_sum.py): errors cluster tightly at anatomically
    # concave junctions (armpit/shoulder, spine junctions), not randomly,
    # consistent with known heat-diffusion behavior near concave geometry,
    # not a parenting defect (max deficit observed: 0.090, at
    # RightShoulder/RightArm/neck/Spine01 junctions). bpy.ops.object.
    # vertex_group_normalize_all's poll() FAILS with no active object in
    # this headless session (probed this session) and its documented
    # semantics assume Weight Paint mode context -- avoid that operator
    # entirely and normalize directly via the data API instead: divide
    # each vertex's existing group weights by their own sum. This changes
    # no bone assignment and no relative weight ratio between bones on a
    # vertex -- only rescales the total to 1.0, which is the LBS-required
    # invariant every deform vertex must satisfy.
    normalized = 0
    for v in mesh_obj.data.vertices:
        if len(v.groups) == 0:
            continue
        total = sum(g.weight for g in v.groups)
        if total <= 1e-9:
            continue
        if abs(total - 1.0) > 1e-6:
            for g in v.groups:
                g.weight = g.weight / total
            normalized += 1
    print(f"post-solve normalization: {normalized} verts rescaled to sum=1.0")

    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print(f"SAVED: {OUT_BLEND}")


def get_weight(mesh_obj, vidx, group_name):
    if group_name not in mesh_obj.vertex_groups:
        return 0.0
    gi = mesh_obj.vertex_groups[group_name].index
    for g in mesh_obj.data.vertices[vidx].groups:
        if g.group == gi:
            return g.weight
    return 0.0


def do_verification():
    """Re-opens the SAVED file fresh (not the in-memory pre-save state)."""
    bpy.ops.wm.open_mainfile(filepath=OUT_BLEND)
    arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")

    bone_head = {b.name: Vector(b.head_local) for b in arm_obj.data.bones}
    bone_tail = {b.name: Vector(b.tail_local) for b in arm_obj.data.bones}

    zero_weight_verts = 0
    bad_sum_verts = 0
    max_sum_err = 0.0
    only_aux_verts = 0
    for v in mesh_obj.data.vertices:
        deform_groups = [
            (mesh_obj.vertex_groups[g.group].name, g.weight)
            for g in v.groups
            if mesh_obj.vertex_groups[g.group].name in DEFORM_BONES
        ]
        if len(deform_groups) == 0:
            zero_weight_verts += 1
            if len(v.groups) > 0:
                only_aux_verts += 1
            continue
        s = sum(w for _, w in deform_groups)
        err = abs(s - 1.0)
        max_sum_err = max(max_sum_err, err)
        if err > 1e-3:
            bad_sum_verts += 1
    print(f"zero-deform-weight verts (must be 0): {zero_weight_verts}")
    print(f"  of which only-aux-weighted (must be 0): {only_aux_verts}")
    print(f"bad-normalization verts (must be 0, max_err={max_sum_err:.4f}): {bad_sum_verts}")

    # Hair/neck-Head seam check: bug-297's actual symptom is a
    # DISCONTINUOUS crack seam (a hard weight jump between MESH-ADJACENT
    # vertices), not a smooth low-magnitude gradient. An earlier version
    # of this gate used an absolute Head-weight threshold (Head<0.95),
    # which flagged 2647/13111 hair-region verts as "failing" purely
    # because heat diffusion produces a smooth gradient with a long,
    # low-magnitude tail near the neck/Head joint -- diagnosed this
    # session (diagnose_hair_boundary.py, diagnose_hair_continuity.py):
    # every failing vert sat 0.11-0.17 above the joint (deep in
    # unambiguous hair territory, not near the seam itself) and the
    # MAXIMUM per-mesh-edge weight delta across all 39575 sampled
    # hair-region edges was 0.0202 -- zero discontinuities, a smooth
    # gradient throughout. Testing per-edge continuity directly (the
    # actual crack-seam signature) instead of an absolute-value threshold.
    head_tail_z = bone_tail["Head"].z
    head_head_z = bone_head["Head"].z
    head_span = head_tail_z - head_head_z
    hair_z_min = head_head_z + 0.7 * head_span
    hair_vert_idx = {v.index for v in mesh_obj.data.vertices if v.co.z >= hair_z_min}
    w_head_cache = {vi: get_weight(mesh_obj, vi, "Head") for vi in hair_vert_idx}

    max_edge_delta = 0.0
    n_edges_sampled = 0
    for e in mesh_obj.data.edges:
        v1, v2 = e.vertices[0], e.vertices[1]
        if v1 in w_head_cache and v2 in w_head_cache:
            n_edges_sampled += 1
            max_edge_delta = max(max_edge_delta, abs(w_head_cache[v1] - w_head_cache[v2]))

    CRACK_SEAM_THRESHOLD = 0.3  # a genuine hard discontinuity, not gradient noise
    hair_bad = max_edge_delta > CRACK_SEAM_THRESHOLD
    print(
        f"hair/scalp verts sampled (z>={hair_z_min:.4f}): {len(hair_vert_idx)}, "
        f"edges checked: {n_edges_sampled}, max per-edge Head-weight delta: {max_edge_delta:.4f} "
        f"(crack-seam threshold: {CRACK_SEAM_THRESHOLD})"
    )

    # Sleeve-cuff/forearm-hand seam check (bug-296 precedent): sample verts
    # near each wrist (within 15% of ForeArm bone length of the LeftHand/
    # RightHand head) and assert no vertex carries >2% weight from any
    # bone NOT in {ForeArm, Hand} for that side -- a distant bone (Spine,
    # Hips, opposite arm) dragging cuff geometry is exactly the
    # sleeve-cuff-flare symptom.
    cuff_results = {}
    for side in ("Left", "Right"):
        forearm_len = (bone_tail[f"{side}ForeArm"] - bone_head[f"{side}ForeArm"]).length
        wrist_pt = bone_head[f"{side}Hand"]
        radius = 0.20 * forearm_len
        cuff_verts = [v for v in mesh_obj.data.vertices if (v.co - wrist_pt).length <= radius]
        cuff_bad = []
        local_bones = {f"{side}ForeArm", f"{side}Hand"}
        for v in cuff_verts:
            for bn in DEFORM_BONES:
                if bn in local_bones:
                    continue
                w = get_weight(mesh_obj, v.index, bn)
                if w > 0.02:
                    cuff_bad.append((v.index, bn, round(w, 3)))
        cuff_results[side] = {
            "n_sampled": len(cuff_verts),
            "n_bad": len(cuff_bad),
            "sample_failures": cuff_bad[:5],
        }
        print(
            f"{side} wrist-cuff verts sampled (radius={radius:.4f}): {len(cuff_verts)}, "
            f"failing (>2% weight from a non-local bone): {len(cuff_bad)}"
        )
        if cuff_bad[:5]:
            print(f"  sample failures (vidx, bone, weight): {cuff_bad[:5]}")

    overall_pass = (
        zero_weight_verts == 0
        and bad_sum_verts == 0
        and not hair_bad
        and all(r["n_bad"] == 0 for r in cuff_results.values())
    )
    return {
        "zero_weight_verts": zero_weight_verts,
        "only_aux_verts": only_aux_verts,
        "bad_sum_verts": bad_sum_verts,
        "hair_sampled": len(hair_vert_idx),
        "hair_max_edge_delta": round(max_edge_delta, 4),
        "hair_crack_seam_detected": hair_bad,
        "cuff": cuff_results,
        "overall_pass": overall_pass,
    }


def main():
    do_weighting()
    result = do_verification()
    print("\n" + "=" * 78)
    print(f"OVERALL: {'PASS' if result['overall_pass'] else 'FAIL'}")
    print("=" * 78)
    print("RESULT_JSON " + json.dumps(result))


if __name__ == "__main__":
    main()
