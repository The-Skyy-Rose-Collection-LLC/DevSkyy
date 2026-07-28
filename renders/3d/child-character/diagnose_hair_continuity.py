"""bug-297's actual symptom is a DISCONTINUOUS crack seam -- a hard jump in
weight (or worse, in effective deformation) between mesh-ADJACENT
vertices, not a smooth low-magnitude gradient. Test mesh-edge-adjacency
continuity directly: for every edge connecting a "hair-gate-failing" vertex
to any neighbor, compute |w_head(a) - w_head(b)| across that edge. A
genuine crack seam shows large jumps (e.g. >0.3) between adjacent verts. A
smooth gradient shows small per-edge deltas even if the ABSOLUTE value
drifts across many edges.
Run: blender --background --factory-startup --python diagnose_hair_continuity.py
"""

import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")

head_gi = mesh_obj.vertex_groups["Head"].index


def get_weight(v, gi):
    for g in v.groups:
        if g.group == gi:
            return g.weight
    return 0.0


head_bone = arm_obj.data.bones["Head"]
head_span = head_bone.tail_local.z - head_bone.head_local.z
hair_z_min = head_bone.head_local.z + 0.7 * head_span

bm = bmesh.new()
bm.from_mesh(mesh_obj.data)
bm.verts.ensure_lookup_table()

w_head = {}
for v in mesh_obj.data.vertices:
    if v.co.z >= hair_z_min:
        w_head[v.index] = get_weight(v, head_gi)

deltas = []
for e in bm.edges:
    v1, v2 = e.verts[0].index, e.verts[1].index
    if v1 in w_head and v2 in w_head:
        deltas.append(abs(w_head[v1] - w_head[v2]))

deltas.sort(reverse=True)
print(f"edges sampled (both endpoints in hair region): {len(deltas)}")
print(f"max per-edge weight delta: {deltas[0]:.4f}")
print(f"top 10 per-edge deltas: {[round(d,4) for d in deltas[:10]]}")
print(f"count with delta>0.1: {sum(1 for d in deltas if d > 0.1)}")
print(f"count with delta>0.3: {sum(1 for d in deltas if d > 0.3)}")
print(f"count with delta>0.5: {sum(1 for d in deltas if d > 0.5)}")

bm.free()
