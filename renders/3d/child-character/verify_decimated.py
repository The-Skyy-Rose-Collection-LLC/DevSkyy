"""Independent re-verification of child-decimated.glb after export+reimport round trip
(bug-292 lesson: topology claims from decimate.py's own pre-export check do not survive
a glTF round trip -- must be re-verified on the actual shipped file).

Island/non-manifold-edge counts are computed AFTER a distance weld
(remove_doubles dist=1e-5), not on the raw re-import. Confirmed this
session (diagnose_fragmentation.py): a raw glTF re-import always re-splits
vertices at UV-seam/hard-normal boundaries into position-coincident,
index-separate verts -- decimate.py's own PRE-WELD check reports this same
fragmentation (1560 islands) on the RAW, never-decimated source.glb too, so
it is glTF's inherent representation, not a defect. Counting islands on the
raw re-import conflates this benign splitting with genuine topology
defects; re-welding first isolates the real signal (welded islands==1,
verts drop to the pre-export weld count exactly, confirmed 47047==47047
this session).
Run: blender --background --factory-startup --python verify_decimated.py
"""

import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "child-decimated.glb")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=GLB)

mesh_obj = max(
    (o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices)
)
mesh = mesh_obj.data

is_clean = not mesh.validate(verbose=True)
print(f"mesh.validate() clean = {is_clean}")

raw_bm = bmesh.new()
raw_bm.from_mesh(mesh)
raw_verts = len(raw_bm.verts)
raw_bm.free()

bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
welded_verts = len(bm.verts)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
print(
    f"raw re-import verts={raw_verts} -> post-weld verts={welded_verts} (weld isolates glTF UV-seam splitting from real topology)"
)

non_manifold = sum(1 for e in bm.edges if not e.is_manifold)

visited, islands = set(), 0
for seed in bm.verts:
    if seed.index in visited:
        continue
    islands += 1
    stack = [seed]
    visited.add(seed.index)
    while stack:
        v = stack.pop()
        for e in v.link_edges:
            other = e.other_vert(v)
            if other.index not in visited:
                visited.add(other.index)
                stack.append(other)

degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-10)

uv_layer = bm.loops.layers.uv.active
spanning = 0
if uv_layer:
    for f in bm.faces:
        us = [loop[uv_layer].uv.x for loop in f.loops]
        vs = [loop[uv_layer].uv.y for loop in f.loops]
        if (max(us) - min(us)) > 0.5 or (max(vs) - min(vs)) > 0.5:
            spanning += 1

n_faces = len(bm.faces)
print(
    f"tris={n_faces} non_manifold_edges={non_manifold} islands={islands} degenerate_faces={degenerate}"
)
print(f"uv_atlas_spanning_faces={spanning}/{n_faces} ({100.0*spanning/n_faces:.2f}%)")
bm.free()
