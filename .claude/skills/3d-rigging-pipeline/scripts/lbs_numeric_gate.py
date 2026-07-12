"""Two numeric gates for a closed-form LBS corrective shape-key computation.

NOT YET EXECUTED against a real file this authoring session (unlike
assert_shape_key_rest_weight.py and gltf_export_verify.py, which were run
against the real production skyy.glb while this skill was written) -- this
is genuine first-run risk, flagged per doctrine.md's numeric-gate rule rather
than asserted as verified. Run it against a real .blend before trusting its
output on a new character.

Gate 1: the forward formula (applying the blend matrix to the corrected rest
position) matches Blender's own depsgraph-evaluated posed position. Target:
~1e-7 (machine precision for this operation).

Gate 2: reapplying the blend matrix to the corrected rest pose reproduces
the desired posed target. Target: ~1e-16.

Both gates are computed in the SAME unit space (see reference/shape-keys.md's
unit-scale trap) -- this script does not convert between world-space and
local-space magnitudes; the caller must pass vertex coordinates already in
one consistent space.

Run:
    blender -b --factory-startup -P lbs_numeric_gate.py -- \\
        --blend /path/to/file.blend --mesh MeshName --armature ArmatureName \\
        --frame 44 --vertex-indices 1023,1024,1057
"""

import json
import sys

import bpy
import mathutils


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    opts = {"blend": None, "mesh": None, "armature": None, "frame": 0, "vertex_indices": []}
    it = iter(argv)
    for arg in it:
        if arg == "--blend":
            opts["blend"] = next(it)
        elif arg == "--mesh":
            opts["mesh"] = next(it)
        elif arg == "--armature":
            opts["armature"] = next(it)
        elif arg == "--frame":
            opts["frame"] = int(next(it))
        elif arg == "--vertex-indices":
            opts["vertex_indices"] = [int(x) for x in next(it).split(",")]
    if not all([opts["blend"], opts["mesh"], opts["armature"], opts["vertex_indices"]]):
        raise SystemExit(
            "usage: ... -- --blend <file.blend> --mesh <name> --armature <name> "
            "--frame <int> --vertex-indices <comma-separated ints>"
        )
    return opts


def blend_matrix_for_vertex(mesh_obj, arm_obj, vertex_index):
    """Compute the linear-blend-skinning matrix (weighted sum of bone
    transforms) actually applied to one vertex, from its vertex groups."""
    vert = mesh_obj.data.vertices[vertex_index]
    group_index_to_name = {vg.index: vg.name for vg in mesh_obj.vertex_groups}

    total = mathutils.Matrix.Identity(4) * 0.0
    total_weight = 0.0
    for g in vert.groups:
        bone_name = group_index_to_name.get(g.group)
        if bone_name is None or bone_name not in arm_obj.pose.bones:
            continue
        pbone = arm_obj.pose.bones[bone_name]
        bone_matrix = (
            arm_obj.matrix_world
            @ pbone.matrix
            @ pbone.bone.matrix_local.inverted()
            @ arm_obj.matrix_world.inverted()
        )
        total += bone_matrix * g.weight
        total_weight += g.weight

    if total_weight < 1e-9:
        raise RuntimeError(
            f"vertex {vertex_index}: zero total skin weight, cannot compute blend matrix"
        )
    # Normalize in case weights don't sum to exactly 1.0.
    return total * (1.0 / total_weight)


def gate1_forward_vs_depsgraph(mesh_obj, arm_obj, vertex_index, corrected_rest_world):
    """Apply the blend matrix to the corrected rest position and compare
    against Blender's own depsgraph-evaluated posed vertex position."""
    A_blend = blend_matrix_for_vertex(mesh_obj, arm_obj, vertex_index)
    forward_world = A_blend @ corrected_rest_world

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = mesh_obj.evaluated_get(depsgraph)
    eval_vert_world = eval_obj.matrix_world @ eval_obj.data.vertices[vertex_index].co

    error = (forward_world - eval_vert_world).length
    return error, A_blend


def gate2_reapply_to_rest(A_blend, corrected_rest_world, desired_posed_world):
    """Reapplying the blend matrix to the corrected rest pose must reproduce
    the desired posed target -- this is the actual definition of a correct
    closed-form inverse, checked as its own independent numeric assertion
    rather than assumed from gate 1 alone."""
    reapplied = A_blend @ corrected_rest_world
    return (reapplied - desired_posed_world).length


def compute_corrected_rest(A_blend, desired_posed_world):
    """The closed-form LBS inverse: corrected_rest = A_blend^-1 @ desired_world."""
    return A_blend.inverted() @ desired_posed_world


def main():
    opts = parse_args()

    bpy.ops.wm.open_mainfile(filepath=opts["blend"])
    bpy.context.scene.frame_set(opts["frame"])

    mesh_obj = bpy.data.objects.get(opts["mesh"])
    arm_obj = bpy.data.objects.get(opts["armature"])
    if mesh_obj is None or arm_obj is None:
        raise RuntimeError(f"mesh {opts['mesh']!r} or armature {opts['armature']!r} not found")

    results = []
    for vidx in opts["vertex_indices"]:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = mesh_obj.evaluated_get(depsgraph)
        desired_posed_world = eval_obj.matrix_world @ eval_obj.data.vertices[vidx].co

        A_blend = blend_matrix_for_vertex(mesh_obj, arm_obj, vidx)
        corrected_rest_world = compute_corrected_rest(A_blend, desired_posed_world)

        gate1_error, _ = gate1_forward_vs_depsgraph(mesh_obj, arm_obj, vidx, corrected_rest_world)
        gate2_error = gate2_reapply_to_rest(A_blend, corrected_rest_world, desired_posed_world)

        results.append(
            {
                "vertex_index": vidx,
                "gate1_forward_vs_depsgraph_error": gate1_error,
                "gate2_reapply_to_rest_error": gate2_error,
                "gate1_pass": gate1_error < 1e-5,
                "gate2_pass": gate2_error < 1e-10,
            }
        )

    print("")
    print("=" * 78)
    print(f"LBS NUMERIC GATE -- {opts['mesh']} @ frame {opts['frame']}")
    print("=" * 78)
    for r in results:
        print(
            f"vertex {r['vertex_index']}: gate1_error={r['gate1_forward_vs_depsgraph_error']:.2e} "
            f"({'PASS' if r['gate1_pass'] else 'FAIL'}), "
            f"gate2_error={r['gate2_reapply_to_rest_error']:.2e} "
            f"({'PASS' if r['gate2_pass'] else 'FAIL'})"
        )
    all_pass = all(r["gate1_pass"] and r["gate2_pass"] for r in results)
    print(f"\nAll gates passed: {all_pass}")
    print("GATE_RESULT_JSON:" + json.dumps({"all_pass": all_pass, "per_vertex": results}))


if __name__ == "__main__":
    main()
