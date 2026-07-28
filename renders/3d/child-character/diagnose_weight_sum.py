"""Root-cause check for skin_weight_child.py's near-universal weight-sum
failure (45967/47047 verts, max_err=0.09) after a successful ARMATURE_AUTO
heat-weight solve. Print raw per-group weights for a handful of failing
verts to see whether the deficit is a genuine under-normalization or an
artifact of the verification's own DEFORM_BONES-only filter (e.g. weight
assigned to a bone name not in that list).
Run: blender --background --factory-startup --python diagnose_weight_sum.py
"""

import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")

bone_names = {b.name for b in arm_obj.data.bones}
print(f"armature bone names ({len(bone_names)}): {sorted(bone_names)}")
print(
    f"mesh vertex_groups ({len(mesh_obj.vertex_groups)}): {[g.name for g in mesh_obj.vertex_groups]}"
)

all_sums = []
for v in mesh_obj.data.vertices:
    groups = [(mesh_obj.vertex_groups[g.group].name, round(g.weight, 4)) for g in v.groups]
    s = sum(w for _, w in groups)
    all_sums.append((abs(s - 1.0), v.index, s, groups))

all_sums.sort(reverse=True)
print("\nWorst 15 by |sum-1.0|:")
for err, vidx, s, groups in all_sums[:15]:
    print(f"  vidx={vidx} sum={s:.4f} err={err:.4f} groups={groups}")

import statistics

errs = [e for e, _, _, _ in all_sums]
print(
    f"\nerr stats: min={min(errs):.5f} max={max(errs):.5f} mean={statistics.mean(errs):.5f} median={statistics.median(errs):.5f}"
)
print(f"count with err>0.01: {sum(1 for e in errs if e > 0.01)}")
print(f"count with err>0.05: {sum(1 for e in errs if e > 0.05)}")

print(f"\nTotal groups defined on mesh: {len(mesh_obj.vertex_groups)}")
for g in mesh_obj.vertex_groups:
    print(f"  group '{g.name}' -- in armature bones: {g.name in bone_names}")
