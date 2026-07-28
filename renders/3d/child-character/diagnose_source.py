"""Phase 0/1 numeric gate: real topology + rig stats for source.glb and skyy.glb.
Run: blender --background --python diagnose_source.py
"""

import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source.glb")
SKYY = os.path.join(
    HERE, "..", "..", "..", "wordpress-theme", "skyyrose-flagship", "assets", "models", "skyy.glb"
)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_list in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions):
        for block in list(block_list):
            block_list.remove(block)


def mesh_stats(mesh_obj, label):
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)

    # connected islands via BFS over vert-edge graph
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

    n_verts = len(bm.verts)
    n_faces = len(bm.faces)

    uv_span = None
    uv_layer = bm.loops.layers.uv.active
    if uv_layer:
        spanning = 0
        for f in bm.faces:
            us = [loop[uv_layer].uv.x for loop in f.loops]
            vs = [loop[uv_layer].uv.y for loop in f.loops]
            if (max(us) - min(us)) > 0.5 or (max(vs) - min(vs)) > 0.5:
                spanning += 1
        uv_span = (spanning, n_faces, 100.0 * spanning / n_faces if n_faces else 0.0)

    bm.free()
    print(f"--- {label} ---")
    print(f"  verts={n_verts} faces={n_faces} non_manifold_edges={non_manifold} islands={islands}")
    if uv_span:
        print(f"  uv_atlas_spanning_faces={uv_span[0]}/{uv_span[1]} ({uv_span[2]:.2f}%)")
    else:
        print("  no active UV layer")
    dims = mesh_obj.dimensions
    print(f"  bbox_dims=({dims.x:.5f}, {dims.y:.5f}, {dims.z:.5f})")


def report_file(path, label):
    if not os.path.exists(path):
        print(f"### {label}: FILE NOT FOUND at {path}")
        return
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=path)
    mesh_objs = [o for o in bpy.data.objects if o.type == "MESH"]
    arm_objs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if not mesh_objs:
        print(f"### {label}: no mesh objects found")
        return
    main_mesh = max(mesh_objs, key=lambda o: len(o.data.vertices))
    print(f"=== {label} ({os.path.basename(path)}) ===")
    print(f"  mesh_objects={len(mesh_objs)} armature_objects={len(arm_objs)}")
    mesh_stats(main_mesh, main_mesh.name)
    for arm in arm_objs:
        bone_names = [b.name for b in arm.data.bones]
        print(f"  armature '{arm.name}': {len(bone_names)} bones: {bone_names}")


report_file(SOURCE, "SOURCE (child character 3d model8k)")
report_file(SKYY, "REFERENCE (skyy.glb mascot)")
