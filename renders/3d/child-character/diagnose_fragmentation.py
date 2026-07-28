"""Root-cause check for verify_decimated.py's post-round-trip 1528-island /
36791-non-manifold-edge result: is this genuine decimation-introduced mesh
fragmentation, or glTF's normal vertex-splitting at UV-seam/hard-normal
boundaries (position-coincident but index-separate verts, which any
edge-walk island count will over-count even on a topologically continuous
surface -- exactly the same pattern decimate.py's own PRE-WELD check
reported on the raw, never-decimated source.glb: 1560 islands there too)?

Test: re-import child-decimated.glb fresh, then apply the IDENTICAL
distance-weld (remove_doubles dist=1e-5) used in Phase 2 -- with NO
decimation this time. If islands collapses back to 1, the fragmentation is
purely coincident-position UV-seam splitting (benign, glTF-inherent). If it
does not, some islands are genuinely disconnected geometry (real defect).

Run: blender --background --factory-startup --python diagnose_fragmentation.py
"""

import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "child-decimated.glb")


def island_count(bm):
    bm.verts.ensure_lookup_table()
    visited = set()
    islands = 0
    sizes = []
    for seed in bm.verts:
        if seed.index in visited:
            continue
        islands += 1
        size = 0
        stack = [seed]
        visited.add(seed.index)
        while stack:
            v = stack.pop()
            size += 1
            for e in v.link_edges:
                other = e.other_vert(v)
                if other.index not in visited:
                    visited.add(other.index)
                    stack.append(other)
        sizes.append(size)
    return islands, sizes


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=GLB)
mesh_obj = max(
    (o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices)
)

bm = bmesh.new()
bm.from_mesh(mesh_obj.data)
pre_islands, pre_sizes = island_count(bm)
pre_sizes.sort(reverse=True)
print(f"PRE-REWELD: islands={pre_islands} verts={len(bm.verts)}")
print(f"  largest 5 island sizes: {pre_sizes[:5]}")
print(f"  smallest 5 island sizes: {pre_sizes[-5:]}")
print(f"  islands with size==1 (stray verts): {sum(1 for s in pre_sizes if s == 1)}")
print(f"  islands with size<=3: {sum(1 for s in pre_sizes if s <= 3)}")

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
post_islands, post_sizes = island_count(bm)
post_sizes.sort(reverse=True)
print(f"POST-REWELD (dist=1e-5, NO decimation): islands={post_islands} verts={len(bm.verts)}")
print(f"  largest 5 island sizes: {post_sizes[:5]}")

# Also try a slightly looser weld distance in case decimate's COLLAPSE
# introduced new seam verts whose positions drifted just past 1e-5 during
# the collapse math (floating point, not a topology change).
bm2 = bmesh.new()
bm2.from_mesh(mesh_obj.data)
bmesh.ops.remove_doubles(bm2, verts=bm2.verts, dist=1e-4)
loose_islands, loose_sizes = island_count(bm2)
loose_sizes.sort(reverse=True)
print(f"POST-REWELD (dist=1e-4): islands={loose_islands} verts={len(bm2.verts)}")

bm.free()
bm2.free()
