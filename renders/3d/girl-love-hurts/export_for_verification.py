"""
Independent-verifier export step. Opens the SAVED .blend read-only (never
writes back to it) and exports a fresh GLB via the installed Blender 5.1.2
glTF exporter, using settings introspected directly from this exact
installed operator's RNA (bpy.ops.export_scene.gltf.get_rna_type()) rather
than assumed from memory/docs of a possibly-different exporter version.

This script's ONLY job is to produce the artifact under test. All numeric
gates live in verify_export.py and run against the file this script writes,
never against the .blend.

Run headless:
    blender --background --factory-startup --python export_for_verification.py
"""

import bpy

BLEND_PATH = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/"
    "renders/3d/girl-love-hurts/love-hurts-girl-rig.blend"
)
GLB_OUT = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/"
    "renders/3d/girl-love-hurts/love-hurts-girl-v1.glb"
)


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

    arm = bpy.data.objects.get("GirlArmature")
    mesh = bpy.data.objects.get("Mesh1.0")
    if arm is None or mesh is None:
        raise RuntimeError("expected GirlArmature + Mesh1.0 objects not found in source .blend")

    # Read-only sanity on the source before export -- this is the "claimed
    # pre-export state" the exported file will be checked against.
    print(
        f"source armature action: {arm.animation_data.action.name if arm.animation_data else None}"
    )
    print(f"source mesh verts={len(mesh.data.vertices)} polys={len(mesh.data.polygons)}")

    bpy.ops.object.select_all(action="DESELECT")
    for o in (arm, mesh):
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm

    bpy.ops.export_scene.gltf(
        filepath=GLB_OUT,
        export_format="GLB",
        use_selection=True,
        use_visible=False,
        export_yup=True,
        export_apply=False,  # keep skin dynamic -- do NOT bake Armature modifier into mesh
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_bake_animation=False,
        export_skins=True,
        export_morph_animation=True,
        export_frame_range=False,
        export_optimize_animation_size=True,
        export_optimize_animation_keep_anim_armature=True,
        export_extras=True,  # carry custom properties (gusset_vertex_indices) as glTF extras, for cross-check only
        export_image_format="AUTO",
    )

    import os

    size = os.path.getsize(GLB_OUT)
    print(f"EXPORTED: {GLB_OUT} ({size} bytes)")
    with open(GLB_OUT, "rb") as f:
        magic = f.read(4)
    if magic != b"glTF":
        raise RuntimeError(f"exported file does not start with glTF magic bytes: {magic!r}")
    print("EXPORT_OK")


if __name__ == "__main__":
    main()
