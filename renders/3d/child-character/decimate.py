"""Phase 2: weld UV/normal-seam-split vertices (NOT voxel_remesh, per bug-297),
then decimate to skyy.glb's ~94,723-tri budget via DecimateModifier COLLAPSE
(NOT quadriflow_remesh, per bug-289). Export child-decimated.glb.

Run: blender --background --factory-startup --python decimate.py
"""

import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source.glb")
OUT = os.path.join(HERE, "child-decimated.glb")
TARGET_TRIS = 94723


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_list in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions):
        for block in list(block_list):
            block_list.remove(block)


def island_count(mesh_obj):
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    bm.verts.ensure_lookup_table()
    visited = set()
    islands = 0
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
    n = len(bm.verts)
    bm.free()
    return islands, n


def uv_span_pct(mesh_obj):
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.active
    spanning, total = 0, len(bm.faces)
    if uv_layer:
        for f in bm.faces:
            us = [loop[uv_layer].uv.x for loop in f.loops]
            vs = [loop[uv_layer].uv.y for loop in f.loops]
            if (max(us) - min(us)) > 0.5 or (max(vs) - min(vs)) > 0.5:
                spanning += 1
    bm.free()
    return spanning, total, (100.0 * spanning / total if total else 0.0)


clear_scene()
bpy.ops.import_scene.gltf(filepath=SOURCE)
mesh_obj = max(
    (o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices)
)
bpy.context.view_layer.objects.active = mesh_obj

pre_islands, pre_verts = island_count(mesh_obj)
pre_span = uv_span_pct(mesh_obj)
print(
    f"PRE-WELD: islands={pre_islands} verts={pre_verts} uv_span={pre_span[0]}/{pre_span[1]} ({pre_span[2]:.2f}%)"
)

# Weld coincident boundary vertices between native UV/normal-seam-split islands.
# remove_doubles(dist=1e-5) is a distance weld, NOT voxel_remesh's nearest-surface
# UV resample -- it cannot destroy the UV atlas the way voxel_remesh does (bug-297).
bm = bmesh.new()
bm.from_mesh(mesh_obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(mesh_obj.data)
bm.free()
mesh_obj.data.update()

post_islands, post_verts = island_count(mesh_obj)
post_span = uv_span_pct(mesh_obj)
print(
    f"POST-WELD: islands={post_islands} verts={post_verts} uv_span={post_span[0]}/{post_span[1]} ({post_span[2]:.2f}%)"
)

n_tris_pre_decimate = len(mesh_obj.data.polygons)
ratio = TARGET_TRIS / n_tris_pre_decimate
print(f"pre-decimate tris={n_tris_pre_decimate} target={TARGET_TRIS} ratio={ratio:.6f}")

mod = mesh_obj.modifiers.new(name="Decimate", type="DECIMATE")
mod.decimate_type = "COLLAPSE"
mod.ratio = ratio
bpy.ops.object.modifier_apply(modifier=mod.name)

final_tris = len(mesh_obj.data.polygons)
final_islands, final_verts = island_count(mesh_obj)
final_span = uv_span_pct(mesh_obj)
print(
    f"FINAL: tris={final_tris} (target {TARGET_TRIS}, "
    f"{100.0 * abs(final_tris - TARGET_TRIS) / TARGET_TRIS:.2f}% off) "
    f"islands={final_islands} verts={final_verts} "
    f"uv_span={final_span[0]}/{final_span[1]} ({final_span[2]:.2f}%)"
)

bpy.ops.object.select_all(action="DESELECT")
mesh_obj.select_set(True)
bpy.context.view_layer.objects.active = mesh_obj
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format="GLB")
print(f"Exported {OUT}")
