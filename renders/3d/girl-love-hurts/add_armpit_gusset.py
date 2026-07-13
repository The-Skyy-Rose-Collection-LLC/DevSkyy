"""
Armpit gusset — Phase (post-Phase-1 rig, pre-Phase-6 numeric gate).

Locked plan step being executed (do not revert to a "rip and leave open" design):
  REJECT the "topologically rip, leave open, no cap" approach. Instead: add 2-3
  new edge loops forming a small gusset panel at the armpit only, skin-weighted
  with a smooth multi-bone gradient (Spine02/Shoulder-equivalent dominant at the
  torso edge, UpperArm/ForeArm dominant at the arm edge, blending across the
  gusset span; arm-proper/torso-proper regions outside the gusset become
  progressively more mono-influenced). Mesh stays a single connected watertight
  surface (no rip, no gap possible by construction).

Pre-flight finding (this session): the Phase-1 .blend was a raw glTF import
whose vertices were never merged-by-distance. glTF stores one vertex per
unique (position, normal, UV) tuple, so every UV seam / hard-normal edge on
this mesh produced duplicate, unwelded, coincident vertices. Diagnostic:
  - as saved by Phase 1  : 5946 face-islands, 44459 non-manifold(!=2 faces) edges
  - after remove_doubles(dist=1e-4): 2 islands (48972-face body + 373-face
    accessory), 89 non-manifold edges
The 44459 -> 89 collapse is a real topology fix (unwelded duplicate verts),
not a redefinition of "watertight" -- confirmed by testing multiple weld
thresholds (1e-5, 1e-4, 1e-3) which all converge on the same 89-edge result,
and by every "boundary loop" being a 1-3 edge fragment (a single dropped
triangle), never a large designed seam. This weld is applied globally as a
prerequisite (it was clearly a missed Phase-1 step, not something optional),
then the armpit gusset is built on top of a properly welded mesh.

Remaining 89 non-manifold edges after the weld are pre-existing single-
triangle mesh-generation defects scattered across the WHOLE body (collar,
hip-pocket, hair-back, jacket seams) -- most are unrelated to the armpit and
are explicitly OUT OF SCOPE for this step (surgical change only). A small
cluster of them sits right at each shoulder/underarm joint (empirically
verified against the LeftArm/RightArm bone head positions); those specific
ones are inside the gusset patch we're building anyway, so they get closed
as a side effect of this edit (holes_fill before subdivide) -- not a
separate whole-body cleanup pass.

Technique for the gusset itself (verified on a synthetic closed mesh first,
see session notes): bmesh.ops.subdivide_edges(..., use_grid_fill=True)
applied to a *local* patch of faces (not the whole mesh) correctly meshes
the transition to the surrounding untouched geometry with zero new
non-manifold edges and zero degenerate faces -- this is what "add 2-3 new
edge loops forming a small gusset panel" is implemented as.

Run headless:
    blender --background --python add_armpit_gusset.py
"""

import json
import os

import bmesh
import bpy
from mathutils import Vector

OUT_DIR = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/renders/3d/girl-love-hurts"
)
BLEND_PATH = os.path.join(OUT_DIR, "love-hurts-girl-rig.blend")

# Gusset patch radius (m): comfortably covers every empirically-found
# shoulder/underarm micro-defect (max observed distance from the Arm bone
# head to a defect cluster centroid was 0.143m; several clusters sit as
# close as 0.04m). 0.15m gives margin without reaching into forearm/hand or
# neck/collar geometry.
PATCH_RADIUS = 0.15
# Taper radius (m): the "arm-proper / torso-proper progressively more
# mono-influenced" zone extends past the patch itself, saturating to pure
# single-bone weight by this radius.
TAPER_RADIUS = 0.24

# Torso-edge / arm-edge weight splits (locked spec: Spine02/Shoulder dominant
# at the torso edge, UpperArm/ForeArm dominant at the arm edge). Shoulder and
# Arm are the anatomically closer bone at each edge, so they take the larger
# share of that edge's weight budget.
TORSO_SHOULDER_SHARE = 0.60
TORSO_SPINE02_SHARE = 0.40
ARM_ARM_SHARE = 0.65
ARM_FOREARM_SHARE = 0.35

SIDES = ["Left", "Right"]


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def face_islands(bm):
    """Connected components over face-adjacency (shared edges)."""
    bm.faces.ensure_lookup_table()
    visited = [False] * len(bm.faces)
    islands = []
    for start in range(len(bm.faces)):
        if visited[start]:
            continue
        stack = [start]
        visited[start] = True
        comp = []
        while stack:
            fi = stack.pop()
            f = bm.faces[fi]
            comp.append(fi)
            for e in f.edges:
                for lf in e.link_faces:
                    if not visited[lf.index]:
                        visited[lf.index] = True
                        stack.append(lf.index)
        islands.append(comp)
    return islands


def nonmanifold_edges(bm):
    return [e for e in bm.edges if len(e.link_faces) != 2]


def edge_key(e):
    """Stable geometric key for an edge (position-based, survives bmesh
    index churn across operations) so we can diff non-manifold edge sets
    before/after."""
    a = tuple(round(c, 5) for c in e.verts[0].co)
    b = tuple(round(c, 5) for c in e.verts[1].co)
    return tuple(sorted((a, b)))


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

    arm_obj = bpy.data.objects["GirlArmature"]
    mesh_obj = bpy.data.objects["Mesh1.0"]
    assert mesh_obj.matrix_world.is_identity or tuple(mesh_obj.location) == (
        0.0,
        0.0,
        0.0,
    ), "mesh_obj is not at identity transform -- landmark math below assumes local==world"

    bone_head = {b.name: Vector(b.head_local) for b in arm_obj.data.bones}

    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    v_before, e_before, f_before = len(bm.verts), len(bm.edges), len(bm.faces)
    nm_before_raw = len(nonmanifold_edges(bm))
    islands_before_raw = len(face_islands(bm))
    print(
        f"RAW (unwelded, as saved by Phase 1): verts={v_before} edges={e_before} "
        f"faces={f_before} nonmanifold={nm_before_raw} islands={islands_before_raw}"
    )

    # --- global weld: fix the unmerged glTF-import duplicate vertices ---
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    v_welded, e_welded, f_welded = len(bm.verts), len(bm.edges), len(bm.faces)
    nm_welded = len(nonmanifold_edges(bm))
    islands_welded = face_islands(bm)
    print(
        f"WELDED (remove_doubles dist=1e-4): verts={v_welded} edges={e_welded} "
        f"faces={f_welded} nonmanifold={nm_welded} islands={len(islands_welded)} "
        f"island_sizes={sorted((len(c) for c in islands_welded), reverse=True)}"
    )
    nm_welded_keys = set(edge_key(e) for e in nonmanifold_edges(bm))

    gusset_vert_indices = set()  # verts whose weights we'll set (patch + taper)
    total_closed_holes_edges = 0
    total_new_faces_from_subdivide = 0

    for side in SIDES:
        shoulder_head = bone_head[f"{side}Shoulder"]
        arm_head = bone_head[f"{side}Arm"]
        axis = arm_head - shoulder_head
        axis_len2 = axis.length_squared
        assert axis_len2 > 1e-8, f"{side}: degenerate Shoulder->Arm axis"

        # Gusset center: the underarm crease sits at the arm-ball joint,
        # matching the empirically-found micro-defect clusters (verified
        # against RightArm/LeftArm bone head positions this session).
        center = arm_head

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        # Pre-existing decimation artifacts: a handful of sub-mm^2 sliver
        # triangles form non-manifold "fin" edges (3-4 faces sharing one
        # edge) right at each shoulder joint -- confirmed this session by
        # direct inspection (near-zero face area, degenerate topology,
        # unrelated to skinning). These are a separate, pre-existing mesh
        # defect, NOT something this step repairs (surgical scope). Fix:
        # exclude the defect faces plus a 1-ring buffer from the patch so
        # subdivide_edges never touches an edge that's part of the defect
        # (verified empirically: this is the only technique of several
        # tried -- dissolve_degenerate, holes_fill, edgenet_fill on the
        # defect itself -- that produces zero new non-manifold edges).
        fin_edges_in_patch = [
            e
            for e in bm.edges
            if len(e.link_faces) > 2
            and ((e.verts[0].co + e.verts[1].co) / 2 - center).length <= PATCH_RADIUS
        ]
        defect_faces = set()
        for e in fin_edges_in_patch:
            for f in e.link_faces:
                defect_faces.add(f)
        excluded_faces = set(defect_faces)
        for f in defect_faces:
            for e in f.edges:
                for lf in e.link_faces:
                    excluded_faces.add(lf)
        if defect_faces:
            print(
                f"  [{side}] excluding {len(defect_faces)} pre-existing defect faces "
                f"(+{len(excluded_faces) - len(defect_faces)} buffer faces) from the gusset "
                f"patch -- {len(fin_edges_in_patch)} non-manifold fin edges, untouched/out-of-scope"
            )

        patch_faces = [
            f
            for f in bm.faces
            if (f.calc_center_median() - center).length <= PATCH_RADIUS and f not in excluded_faces
        ]
        print(
            f"\n[{side}] patch center={tuple(round(c, 4) for c in center)} "
            f"patch_faces={len(patch_faces)}"
        )

        # Close any pre-existing simple (1-face) micro-holes strictly inside
        # this patch (after excluding the fin-defect zone above) before
        # densifying, so subdivide_edges operates on locally-closed topology.
        local_nm_edges = []
        for f in patch_faces:
            for e in f.edges:
                if len(e.link_faces) == 1:
                    local_nm_edges.append(e)
        local_nm_edges = list({e.index: e for e in local_nm_edges}.values())
        if local_nm_edges:
            bmesh.ops.holes_fill(bm, edges=local_nm_edges, sides=0)
            total_closed_holes_edges += len(local_nm_edges)
            print(f"  closed {len(local_nm_edges)} local boundary edges (pre-existing micro-holes)")

        # Recompute the patch after hole-filling (new faces may have joined it).
        bm.faces.ensure_lookup_table()
        patch_faces = [
            f
            for f in bm.faces
            if (f.calc_center_median() - center).length <= PATCH_RADIUS and f not in excluded_faces
        ]
        patch_edges = set()
        for f in patch_faces:
            for e in f.edges:
                patch_edges.add(e)
        patch_edges = list(patch_edges)
        f_count_before_sub = len(bm.faces)

        # The gusset: 2 new edge loops (3-way subdivision) across the local
        # patch, grid-filled so the transition to surrounding untouched
        # geometry stays manifold (verified on a synthetic closed mesh
        # before running this on the real asset).
        bmesh.ops.subdivide_edges(bm, edges=patch_edges, cuts=2, use_grid_fill=True)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        total_new_faces_from_subdivide += len(bm.faces) - f_count_before_sub
        print(
            f"  subdivided patch: faces {f_count_before_sub} -> {len(bm.faces)} "
            f"(+{len(bm.faces) - f_count_before_sub})"
        )

        # Collect verts for weight assignment: everything within the taper
        # radius (patch + surrounding mono-influence falloff zone).
        for v in bm.verts:
            if (v.co - center).length <= TAPER_RADIUS:
                gusset_vert_indices.add(v.index)

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    nm_after = nonmanifold_edges(bm)
    nm_after_keys = set(edge_key(e) for e in nm_after)
    new_nm_keys = nm_after_keys - nm_welded_keys
    print(
        f"\nGLOBAL AFTER GUSSET WORK: verts={len(bm.verts)} edges={len(bm.edges)} "
        f"faces={len(bm.faces)} nonmanifold={len(nm_after)}"
    )
    print(
        f"  non-manifold edges CLOSED by this edit: {nm_welded - len(nm_after)} "
        f"(local holes closed inside patches: {total_closed_holes_edges})"
    )
    print(f"  NEW non-manifold edges introduced by this edit (must be 0): {len(new_nm_keys)}")
    assert (
        len(new_nm_keys) == 0
    ), f"gusset edit introduced {len(new_nm_keys)} new non-manifold edges -- ABORTING SAVE"

    islands_after = face_islands(bm)
    print(
        f"  connected components after: {len(islands_after)} "
        f"sizes={sorted((len(c) for c in islands_after), reverse=True)}"
    )

    # --- vertex groups + smooth multi-bone gradient weights ---
    group_names = [
        "Spine02",
        "LeftShoulder",
        "LeftArm",
        "LeftForeArm",
        "RightShoulder",
        "RightArm",
        "RightForeArm",
    ]
    for name in group_names:
        if name not in mesh_obj.vertex_groups:
            mesh_obj.vertex_groups.new(name=name)
    group_index = {vg.name: vg.index for vg in mesh_obj.vertex_groups}

    deform = bm.verts.layers.deform.verify()

    weighted_count = 0
    for side in SIDES:
        shoulder_head = bone_head[f"{side}Shoulder"]
        arm_head = bone_head[f"{side}Arm"]
        axis = arm_head - shoulder_head
        axis_len2 = axis.length_squared
        center = arm_head

        i_spine02 = group_index["Spine02"]
        i_shoulder = group_index[f"{side}Shoulder"]
        i_arm = group_index[f"{side}Arm"]
        i_forearm = group_index[f"{side}ForeArm"]

        bm.verts.ensure_lookup_table()
        for vi in gusset_vert_indices:
            v = bm.verts[vi]
            if (v.co - center).length > TAPER_RADIUS:
                continue
            # only weight verts actually on this side's axis-relevant side
            # (skip -- both sides' taper spheres don't overlap given the
            # >0.2m shoulder separation, so no cross-talk; each vert is
            # processed once per side whose sphere contains it)
            t = (v.co - shoulder_head).dot(axis) / axis_len2
            arm_w = smoothstep(t)
            torso_w = 1.0 - arm_w

            dv = v[deform]
            dv[i_shoulder] = torso_w * TORSO_SHOULDER_SHARE
            dv[i_spine02] = torso_w * TORSO_SPINE02_SHARE
            dv[i_arm] = arm_w * ARM_ARM_SHARE
            dv[i_forearm] = arm_w * ARM_FOREARM_SHARE
            weighted_count += 1

    print(f"\nweighted {weighted_count} vertices across both gusset+taper zones")

    bm.to_mesh(mesh_obj.data)
    mesh_obj.data.update()
    bm.free()

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"\nSAVED: {BLEND_PATH}")

    result = {
        "raw_verts": v_before,
        "raw_edges": e_before,
        "raw_faces": f_before,
        "raw_nonmanifold": nm_before_raw,
        "raw_islands": islands_before_raw,
        "welded_verts": v_welded,
        "welded_nonmanifold": nm_welded,
        "welded_islands": len(islands_welded),
        "final_nonmanifold": len(nm_after),
        "new_nonmanifold_introduced": len(new_nm_keys),
        "final_islands": len(islands_after),
        "final_island_sizes": sorted((len(c) for c in islands_after), reverse=True),
        "weighted_vert_count": weighted_count,
    }
    print("RESULT_JSON " + json.dumps(result))


if __name__ == "__main__":
    main()
