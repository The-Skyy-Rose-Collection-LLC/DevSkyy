"""
Armpit gusset numeric gate (locked plan step, post-skin-weighting).

Read-only verification against love-hurts-girl-rig.blend -- never saves.

Pose-tests the gusset region at BOTH named test poses, each applied
independently against the same rest baseline (NOT combined into one
compound pose -- "evaluate gusset region at both test poses" in the
locked verification method is two separate poses, each with its own
pre/post area-ratio + self-intersection check):
  1. "abduction_30"  -- shoulder abduction 30 deg only, mirrored by side.
  2. "flexion_45"    -- shoulder flexion 45 deg only, same direction both
                        sides.
Both are individually a superset of the actual walk-cycle arm swing
(20-40 deg, single-plane flexion/extension only): flexion_45 exceeds the
range's own top end (45 > 40) on the SAME axis the walk cycle uses;
abduction_30 exercises a degree of freedom (lateral abduction) the walk
cycle never uses at all, so any nonzero abduction is already outside what
the walk exercises.

Gusset region definition (traced to source, not invented): the ONLY
existing, persisted definition of "the gusset region" in this codebase is
`mesh_obj["gusset_vertex_indices"]`, a custom ID property on Mesh1.0 --
a JSON list of vertex indices computed by add_armpit_gusset.py as every
vertex within TAPER_RADIUS (0.24m) of either *Arm bone head (the patch +
weight-blend taper zone), and later re-read/persisted by skin_weight_body.py
(skin_weight_body.py:290-295) so downstream passes don't have to
re-derive it. This script reuses that exact set. A "gusset face" =
a mesh polygon whose vertices are ALL members of that set (strictly
inside the region); a secondary "any-vertex" count is reported for
context only and does not affect the gate.

Two measures per pose, ALL required for gate_passed (AND across both
measures AND both poses):
  (a) zero self-intersecting faces in the gusset region at the posed
      state. Verified via mathutils.bvhtree.BVHTree.overlap() called on
      itself, using SHARED vertex indices (i.e. built straight from
      eval_mesh.vertices / loop_triangles, NOT per-triangle-private
      copies). This distinction was empirically load-bearing this
      session: a first attempt that flattened each triangle into its own
      3 private vertex indices produced a massive false-positive count
      (9058/30502 gusset faces "self-intersecting" AT REST, before any
      pose) -- direct comparison against the shared-index method on the
      SAME real evaluated mesh proved every one of those extra pairs was
      a normal edge-adjacent neighbor-triangle pair (shares exactly 2
      vertex positions in the un-flattened mesh) that overlap() only
      correctly excludes when it can see the shared indices. Shared-index
      method: 356 gusset faces at rest (1845 pairs) vs flattened's 9058
      (17985 pairs) -- confirmed via /tmp/gusset_gate/compare_bvh_methods.py
      this session. Self-overlap is computed over the WHOLE posed mesh
      (so a gusset face pinching into a NEIGHBORING non-gusset face is
      caught too), then filtered to pairs touching >=1 gusset face.
  (b) per-face area ratio (posed-area / rest-area) for every gusset face
      stays within [0.5, 2.0]. Outside that band is the numeric signature
      of a candy-wrapper pinch (area -> 0) or tear/stretch (area -> large).

A REST-state self-intersection count (shared-index method) is also
reported once, as a diagnostic baseline -- NOT part of gate_passed, which
per the locked spec is defined purely on posed-state counts -- to
distinguish any pre-existing mesh condition from a pose-induced defect.

Method:
  1. Open the .blend. Read gusset_vertex_indices; derive gusset face set
     from the mesh's own polygon definitions (topology is invariant under
     Armature-modifier deformation -- only vertex positions move).
  2. Evaluate the Armature-deformed mesh via the depsgraph at REST pose
     (all pose bones at identity -- the file's saved state) for the area
     baseline and the rest self-intersection diagnostic. Using the SAME
     deform-evaluation pipeline (evaluated mesh via depsgraph, not the
     raw edit-mesh) for both rest and posed removes any spurious area
     delta from the Armature modifier's own numerical behavior at
     identity vs non-identity pose.
  3. For each of the two named poses: reset LeftArm/RightArm pose bones
     to identity, then set rotation_quaternion for the combined-this-pose
     abduction/flexion angles (one of the two is 0 deg for a given pose).
     The rotation is built in WORLD space (abduction = rotation about the
     world Y axis [front-back / anteroposterior], mirrored by side so
     both arms move AWAY from the body midline; flexion = rotation about
     the world X axis [left-right / mediolateral], same sign both sides
     so both arms swing the SAME way [forward]) and then converted to the
     bone's local pose-rotation via conjugation by the bone's rest matrix
     (matrix_basis = rest^-1 @ world_rotation @ rest, valid because the
     parent bones -- Shoulder, Spine -- are left at their saved rest
     pose, i.e. their own matrix_basis is identity). "Forward" (= -Y in
     this rig) was confirmed empirically this session from TWO
     independent landmarks that both extend toward -Y: the `headfront`
     auxiliary bone (nose/face-front marker) and the LeftToeBase/
     RightToeBase tail positions (toes point forward).
  4. Re-evaluate via a fresh depsgraph -- this is the "posed" mesh for
     that pose.
  5. Per-face area ratio + self-intersection check, restricted to gusset
     faces as defined above.

Run headless:
    blender --background --factory-startup --python gate_armpit_gusset.py
"""

import json
import math

import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

BLEND_PATH = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/"
    "renders/3d/girl-love-hurts/love-hurts-girl-rig.blend"
)

ARMATURE_NAME = "GirlArmature"
MESH_NAME = "Mesh1.0"

TEST_POSES = [
    {"name": "abduction_30", "abduction_deg": 30.0, "flexion_deg": 0.0},
    {"name": "flexion_45", "abduction_deg": 0.0, "flexion_deg": 45.0},
]

# Mirrored abduction sign per side: Left is on the +X side of the rig, Right
# is on the -X side (confirmed this session: LeftArm.head.x=+0.24,
# RightArm.head.x=-0.25). Sign chosen so each side's arm rotates AWAY from
# the body midline (derived algebraically from R_y(theta) applied to the
# rest hang-down direction (0,0,-1); verified empirically below via the
# posed bone direction printout).
ABDUCTION_SIGN = {"Left": -1.0, "Right": +1.0}
# Flexion is NOT mirrored -- both arms swing the same way (forward = -Y).
FLEXION_SIGN = -1.0

AREA_RATIO_MIN = 0.5
AREA_RATIO_MAX = 2.0

# Sub-mm^2 sliver threshold (SI units, m^2 -- 1mm^2 = 1e-6 m^2). Diagnostic
# classifier only, does not affect gate_passed: add_armpit_gusset.py's own
# docstring documents pre-existing sub-mm^2 sliver/fin triangles in this
# exact zone (decimation artifacts, out of scope), and area-ratio is
# numerically unstable on near-zero-area faces -- a failing sliver is a
# much weaker signal than a failing face of typical gusset size.
SLIVER_AREA_M2 = 1e-6


def world_rotation_matrix(side: str, abduction_deg: float, flexion_deg: float) -> Matrix:
    """Abduction (about world Y) then flexion (about world X), as a 3x3
    world-space rotation matrix. Composition order: abduct first, then
    flex (world_rotation @ v == R_flex @ (R_abd @ v))."""
    abd_rad = math.radians(abduction_deg) * ABDUCTION_SIGN[side]
    flex_rad = math.radians(flexion_deg) * FLEXION_SIGN
    r_abd = Matrix.Rotation(abd_rad, 3, "Y")
    r_flex = Matrix.Rotation(flex_rad, 3, "X")
    return r_flex @ r_abd


def local_pose_rotation(rest_3x3: Matrix, world_rotation_3x3: Matrix) -> Matrix:
    """Convert a desired WORLD-space rotation of a bone (applied on top of
    its rest orientation) into the bone's LOCAL pose rotation
    (matrix_basis), given the bone is parented to an unposed chain:
        posed_world = rest_3x3 @ matrix_basis  ==  world_rotation @ rest_3x3
        =>  matrix_basis = rest_3x3^-1 @ world_rotation @ rest_3x3
    """
    return rest_3x3.inverted() @ world_rotation_3x3 @ rest_3x3


def polygon_areas(mesh_data) -> list:
    return [p.area for p in mesh_data.polygons]


def evaluate_mesh_areas(depsgraph, mesh_obj):
    """Evaluate mesh_obj through the depsgraph (Armature deform applied)
    and return (per-polygon-area list, evaluated bpy.types.Object,
    evaluated bpy.types.Mesh -- caller must free with
    eval_obj.to_mesh_clear())."""
    eval_obj = mesh_obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()
    areas = polygon_areas(eval_mesh)
    return areas, eval_obj, eval_mesh


def self_intersecting_polygons(eval_mesh, gusset_face_set):
    """Whole-mesh triangle self-intersection via BVHTree.overlap(self),
    built from SHARED vertex indices (mesh's own vertices + loop_triangles
    vertex tuples -- NOT per-triangle-private copies; see module docstring
    for why the shared-index form is the one that's actually correct).
    Empirically confirmed this session (synthetic + real-mesh A/B
    comparison): with shared indices, adjacent (edge- or vertex-sharing)
    triangles are correctly excluded and it never reports self-pairs
    (i,i); only genuinely crossing triangles are returned. Returns the set
    of gusset polygon indices that participate in >=1 intersecting pair,
    plus the deduplicated + raw pair counts for diagnostics."""
    eval_mesh.calc_loop_triangles()
    tris = eval_mesh.loop_triangles
    verts = eval_mesh.vertices
    tri_poly_index = [t.polygon_index for t in tris]

    shared_verts = [v.co.copy() for v in verts]
    shared_tris = [tuple(t.vertices) for t in tris]

    bvh = BVHTree.FromPolygons(shared_verts, shared_tris, all_triangles=True)
    raw_pairs = bvh.overlap(bvh)

    seen_pairs = set()
    gusset_faces_hit = set()
    for i, j in raw_pairs:
        if i == j:
            continue
        key = (i, j) if i < j else (j, i)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        pi, pj = tri_poly_index[i], tri_poly_index[j]
        if pi in gusset_face_set or pj in gusset_face_set:
            if pi in gusset_face_set:
                gusset_faces_hit.add(pi)
            if pj in gusset_face_set:
                gusset_faces_hit.add(pj)

    return gusset_faces_hit, len(seen_pairs), len(raw_pairs)


def reset_arm_pose(arm_obj):
    for side in ("Left", "Right"):
        arm_obj.pose.bones[f"{side}Arm"].rotation_quaternion = (1.0, 0.0, 0.0, 0.0)


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

    arm_obj = bpy.data.objects[ARMATURE_NAME]
    mesh_obj = bpy.data.objects[MESH_NAME]

    loc = tuple(round(c, 6) for c in mesh_obj.location)
    assert loc == (0.0, 0.0, 0.0), f"mesh_obj location not identity: {loc}"
    assert "gusset_vertex_indices" in mesh_obj, (
        "mesh_obj is missing the persisted gusset_vertex_indices custom ID "
        "property -- run add_armpit_gusset.py / skin_weight_body.py first, "
        "there is no fallback definition of the gusset region"
    )
    assert any(
        m.type == "ARMATURE" and m.object == arm_obj for m in mesh_obj.modifiers
    ), f"{MESH_NAME} has no Armature modifier targeting {ARMATURE_NAME}"

    gusset_vert_indices = set(json.loads(mesh_obj["gusset_vertex_indices"]))
    print(f"gusset_vertex_indices (persisted): {len(gusset_vert_indices)} verts")

    polygons = mesh_obj.data.polygons
    gusset_face_all = set()  # ALL verts in the gusset set -- the gate population
    gusset_face_any = set()  # >=1 vert in the gusset set -- diagnostic only
    for p in polygons:
        vs = p.vertices
        n_in = sum(1 for vi in vs if vi in gusset_vert_indices)
        if n_in == len(vs):
            gusset_face_all.add(p.index)
        if n_in > 0:
            gusset_face_any.add(p.index)
    print(
        f"gusset faces: all-verts-in-set={len(gusset_face_all)} "
        f"(gate population), any-vert-in-set={len(gusset_face_any)} (diagnostic)"
    )
    assert len(gusset_face_all) > 0, "0 gusset faces found -- region derivation is broken"

    # --- sanity: pose bones must start at identity (this is a read-only
    # verification against the saved rest state; a non-identity starting
    # pose would silently invalidate the rest-area baseline) ---
    for side in ("Left", "Right"):
        pb = arm_obj.pose.bones[f"{side}Arm"]
        q = tuple(round(c, 6) for c in pb.rotation_quaternion)
        assert q == (
            1.0,
            0.0,
            0.0,
            0.0,
        ), f"{side}Arm pose bone is not at identity rotation before posing: {q}"

    # --- REST evaluation (baseline, shared across both test poses) ---
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rest_areas, rest_eval_obj, rest_eval_mesh = evaluate_mesh_areas(depsgraph, mesh_obj)
    assert len(rest_areas) == len(polygons), "rest-evaluated polygon count mismatch vs base mesh"
    zero_area_gusset_rest = [i for i in gusset_face_all if rest_areas[i] <= 1e-12]
    assert not zero_area_gusset_rest, (
        f"{len(zero_area_gusset_rest)} gusset face(s) have ~zero area AT REST "
        f"(pre-existing degenerate geometry, out of scope but blocks a ratio "
        f"computation): {zero_area_gusset_rest[:10]}"
    )
    # Diagnostic-only baseline (NOT part of gate_passed, which is defined
    # purely on POSED-state counts per the locked spec): self-intersections
    # already present at REST distinguish a pre-existing mesh condition
    # from a pose-induced candy-wrapper defect.
    rest_faces_hit, rest_n_pairs, _ = self_intersecting_polygons(rest_eval_mesh, gusset_face_all)
    rest_eval_obj.to_mesh_clear()
    print(
        f"[diagnostic, NOT part of gate_passed] self-intersecting gusset faces AT REST "
        f"(shared-index method): {len(rest_faces_hit)} (pairs: {rest_n_pairs})"
    )

    rest_area_vals = sorted(rest_areas[i] for i in gusset_face_all)
    rest_area_median = rest_area_vals[len(rest_area_vals) // 2]
    print(
        f"[diagnostic] gusset rest-area stats (m^2): min={rest_area_vals[0]:.8f} "
        f"median={rest_area_median:.8f} max={rest_area_vals[-1]:.8f} "
        f"sliver_threshold={SLIVER_AREA_M2:.8f}"
    )

    rest_dirs = {}
    for side in ("Left", "Right"):
        pb = arm_obj.pose.bones[f"{side}Arm"]
        rest_dirs[side] = (pb.tail - pb.head).normalized().copy()

    pose_results = []
    for pose_spec in TEST_POSES:
        pose_name = pose_spec["name"]
        abd_deg = pose_spec["abduction_deg"]
        flex_deg = pose_spec["flexion_deg"]

        reset_arm_pose(arm_obj)
        for side in ("Left", "Right"):
            rest_3x3 = arm_obj.data.bones[f"{side}Arm"].matrix_local.to_3x3()
            world_rot = world_rotation_matrix(side, abd_deg, flex_deg)
            local_rot = local_pose_rotation(rest_3x3, world_rot)
            arm_obj.pose.bones[f"{side}Arm"].rotation_quaternion = local_rot.to_quaternion()

        bpy.context.view_layer.update()

        swing_deg = {}
        for side in ("Left", "Right"):
            pb = arm_obj.pose.bones[f"{side}Arm"]
            posed_dir = (pb.tail - pb.head).normalized()
            swing_deg[side] = math.degrees(
                math.acos(max(-1.0, min(1.0, rest_dirs[side].dot(posed_dir))))
            )

        depsgraph = bpy.context.evaluated_depsgraph_get()
        posed_areas, posed_eval_obj, posed_eval_mesh = evaluate_mesh_areas(depsgraph, mesh_obj)
        assert len(posed_areas) == len(
            polygons
        ), f"[{pose_name}] posed-evaluated polygon count mismatch vs base mesh"

        # --- (b) per-face area ratio, gusset population only ---
        ratio_failures = []
        worst_ratio = None
        worst_ratio_face = None
        for i in sorted(gusset_face_all):
            ratio = posed_areas[i] / rest_areas[i]
            if worst_ratio is None or abs(math.log(ratio)) > abs(math.log(worst_ratio)):
                worst_ratio = ratio
                worst_ratio_face = i
            if not (AREA_RATIO_MIN <= ratio <= AREA_RATIO_MAX):
                ratio_failures.append(
                    {
                        "face": i,
                        "rest_area": rest_areas[i],
                        "posed_area": posed_areas[i],
                        "ratio": ratio,
                        "is_sliver": rest_areas[i] < SLIVER_AREA_M2,
                    }
                )
        non_sliver_ratio_failures = [f for f in ratio_failures if not f["is_sliver"]]

        # --- (a) self-intersection, gusset population only ---
        gusset_faces_hit, n_pairs, n_raw_pairs = self_intersecting_polygons(
            posed_eval_mesh, gusset_face_all
        )
        posed_eval_obj.to_mesh_clear()
        # Skinning-attributable = newly introduced by this pose, i.e. NOT
        # already self-intersecting at rest (rest self-intersection is
        # pose-independent mesh authoring, not a skin-weight symptom).
        new_self_intersections = gusset_faces_hit - rest_faces_hit

        all_ratios_in_bounds = len(ratio_failures) == 0
        zero_self_intersections = len(gusset_faces_hit) == 0
        pose_passed = all_ratios_in_bounds and zero_self_intersections

        print("")
        print("=" * 78)
        print(f"POSE: {pose_name}  (abduction={abd_deg} deg, flexion={flex_deg} deg)")
        print(
            f"  effective swing -- Left: {swing_deg['Left']:.2f} deg, Right: {swing_deg['Right']:.2f} deg"
        )
        print("=" * 78)
        print(f"gusset faces tested (all-verts-in-set): {len(gusset_face_all)}")
        print(f"area ratio bounds: [{AREA_RATIO_MIN}, {AREA_RATIO_MAX}]")
        print(
            f"worst-case ratio: {worst_ratio:.4f} at face {worst_ratio_face} "
            f"(rest_area={rest_areas[worst_ratio_face]:.8f} m^2, "
            f"sliver={rest_areas[worst_ratio_face] < SLIVER_AREA_M2})"
        )
        print(
            f"faces OUTSIDE bounds: {len(ratio_failures)} total, "
            f"{len(non_sliver_ratio_failures)} non-sliver (rest_area >= {SLIVER_AREA_M2:.0e} m^2), "
            f"{len(ratio_failures) - len(non_sliver_ratio_failures)} sliver"
        )
        for f in sorted(ratio_failures, key=lambda x: x["rest_area"], reverse=True)[:20]:
            print(
                f"  FAIL face={f['face']} rest_area={f['rest_area']:.8f} "
                f"posed_area={f['posed_area']:.8f} ratio={f['ratio']:.4f} "
                f"sliver={f['is_sliver']}"
            )
        print(
            f"self-intersecting gusset faces (posed, absolute): {len(gusset_faces_hit)} "
            f"(unique intersecting tri pairs: {n_pairs}, raw BVH pairs: {n_raw_pairs})"
        )
        print(
            f"self-intersecting gusset faces NEWLY introduced by this pose "
            f"(posed - rest, skinning-attributable): {len(new_self_intersections)}"
        )
        if new_self_intersections:
            print(f"  newly-introduced faces: {sorted(new_self_intersections)[:20]}")
        print("-" * 78)
        print(f"[{pose_name}] all_face_area_ratios_in_bounds: {all_ratios_in_bounds}")
        print(f"[{pose_name}] zero_self_intersecting_faces: {zero_self_intersections}")
        print(f"[{pose_name}] POSE_PASSED: {pose_passed}")

        pose_results.append(
            {
                "name": pose_name,
                "abduction_deg": abd_deg,
                "flexion_deg": flex_deg,
                "effective_swing_deg": swing_deg,
                "worst_area_ratio": worst_ratio,
                "worst_area_ratio_face": worst_ratio_face,
                "worst_area_ratio_face_is_sliver": rest_areas[worst_ratio_face] < SLIVER_AREA_M2,
                "area_ratio_failures": ratio_failures,
                "area_ratio_failures_non_sliver": len(non_sliver_ratio_failures),
                "all_face_area_ratios_in_bounds": all_ratios_in_bounds,
                "self_intersecting_faces": len(gusset_faces_hit),
                "self_intersecting_face_ids": sorted(gusset_faces_hit),
                "intersecting_tri_pairs": n_pairs,
                "self_intersecting_faces_new_vs_rest": len(new_self_intersections),
                "zero_self_intersecting_faces": zero_self_intersections,
                "pose_passed": pose_passed,
            }
        )

    reset_arm_pose(arm_obj)

    all_face_area_ratios_in_bounds = all(r["all_face_area_ratios_in_bounds"] for r in pose_results)
    zero_self_intersecting_faces = all(r["zero_self_intersecting_faces"] for r in pose_results)
    gate_passed = all_face_area_ratios_in_bounds and zero_self_intersecting_faces
    worst_area_ratio = max(pose_results, key=lambda r: abs(math.log(r["worst_area_ratio"])))[
        "worst_area_ratio"
    ]
    self_intersecting_faces_union = set()
    new_self_intersecting_faces_union = set()
    non_sliver_failures_total = sum(r["area_ratio_failures_non_sliver"] for r in pose_results)
    for r in pose_results:
        self_intersecting_faces_union.update(r["self_intersecting_face_ids"])
        new_self_intersecting_faces_union.update(
            fid for fid in r["self_intersecting_face_ids"] if fid not in rest_faces_hit
        )

    print("")
    print("#" * 78)
    print("ARMPIT GUSSET NUMERIC GATE -- OVERALL (AND across both test poses)")
    print("#" * 78)
    for r in pose_results:
        print(
            f"  {r['name']}: pose_passed={r['pose_passed']} "
            f"(ratio_failures={len(r['area_ratio_failures'])} "
            f"[{r['area_ratio_failures_non_sliver']} non-sliver], "
            f"self_intersect={r['self_intersecting_faces']} "
            f"[{r['self_intersecting_faces_new_vs_rest']} new-vs-rest])"
        )
    print(f"all_face_area_ratios_in_bounds (both poses): {all_face_area_ratios_in_bounds}")
    print(f"zero_self_intersecting_faces (both poses): {zero_self_intersecting_faces}")
    print(f"worst_area_ratio (either pose): {worst_area_ratio:.4f}")
    print(
        f"self_intersecting_faces (union across both poses, ABSOLUTE incl. pre-existing): "
        f"{len(self_intersecting_faces_union)}"
    )
    print(
        f"self_intersecting_faces (union across both poses, NEW vs rest baseline, "
        f"skinning-attributable): {len(new_self_intersecting_faces_union)}"
    )
    print(
        f"area_ratio_failures (union across both poses, non-sliver only): "
        f"{non_sliver_failures_total}"
    )
    print(f"GATE_PASSED (literal spec: absolute posed-state counts, zero-tolerance): {gate_passed}")
    print("#" * 78)

    summary = {
        "gusset_face_count": len(gusset_face_all),
        "gusset_face_count_any_vertex": len(gusset_face_any),
        "area_ratio_bounds": [AREA_RATIO_MIN, AREA_RATIO_MAX],
        "sliver_area_threshold_m2": SLIVER_AREA_M2,
        "self_intersecting_faces_at_rest_diagnostic": len(rest_faces_hit),
        "self_intersecting_pairs_at_rest_diagnostic": rest_n_pairs,
        "poses": pose_results,
        "all_face_area_ratios_in_bounds": all_face_area_ratios_in_bounds,
        "zero_self_intersecting_faces": zero_self_intersecting_faces,
        "worst_area_ratio": worst_area_ratio,
        "self_intersecting_faces": len(self_intersecting_faces_union),
        "self_intersecting_face_ids": sorted(self_intersecting_faces_union),
        "self_intersecting_faces_new_vs_rest": len(new_self_intersecting_faces_union),
        "area_ratio_failures_non_sliver_total": non_sliver_failures_total,
        "gate_passed": gate_passed,
    }
    print("GATE_RESULT_JSON:" + json.dumps(summary))


if __name__ == "__main__":
    main()
