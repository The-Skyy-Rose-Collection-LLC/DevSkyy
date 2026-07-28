"""Root-cause + severity check for the exporter's warning "There are more
than 4 joint vertex influences. The 4 with highest weight will be used
(and normalized)." glTF's runtime skinning standard caps joint influences
at 4 per vertex (JOINTS_0/WEIGHTS_0, a single vec4 attribute set) --
Blender's own vertex groups have no such cap, so ANY vertex with 5+
nonzero-weight vertex groups triggers this on every skinned export; it is
not necessarily a defect. The real question is severity: how much total
weight is being dropped, and is any dropped-weight vertex significant
enough to visibly affect deformation once truncated-and-renormalized to
the top 4.
Run: blender --background --factory-startup --python diagnose_joint_influences.py
"""

import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND)
mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")

over_4 = []
max_groups = 0
for v in mesh_obj.data.vertices:
    n = len(v.groups)
    max_groups = max(max_groups, n)
    if n > 4:
        weights = sorted((g.weight for g in v.groups), reverse=True)
        top4_sum = sum(weights[:4])
        dropped_sum = sum(weights[4:])
        over_4.append((v.index, n, round(top4_sum, 4), round(dropped_sum, 4)))

print(f"total verts: {len(mesh_obj.data.vertices)}")
print(f"max vertex-group count on any vertex: {max_groups}")
print(f"verts with >4 nonzero groups: {len(over_4)}")
if over_4:
    dropped_sums = [d for _, _, _, d in over_4]
    print(
        f"dropped-weight stats: min={min(dropped_sums):.4f} max={max(dropped_sums):.4f} mean={sum(dropped_sums)/len(dropped_sums):.4f}"
    )
    print(
        f"count with dropped_sum > 0.05 (5%, would visibly affect deformation): {sum(1 for d in dropped_sums if d > 0.05)}"
    )
    print(f"count with dropped_sum > 0.10: {sum(1 for d in dropped_sums if d > 0.10)}")
    print(f"worst 10 by dropped_sum: {sorted(over_4, key=lambda x: -x[3])[:10]}")
