import sys

import bpy
import mathutils


def setup_luxury_render_settings():
    """Configure Blender for professional e-commerce output."""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.film_transparent = True

    # White background for scaffold
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (1, 1, 1, 1)
    bg.inputs[1].default_value = 1.0


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_product(filepath):
    # Support GLB/glTF
    bpy.ops.import_scene.gltf(filepath=filepath)
    return [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]


def setup_3point_lighting():
    # Key Light
    bpy.ops.object.light_add(type="AREA", location=(5, -5, 10))
    key = bpy.context.active_object
    key.data.energy = 1000
    key.data.size = 5

    # Fill Light
    bpy.ops.object.light_add(type="AREA", location=(-5, -5, 5))
    fill = bpy.context.active_object
    fill.data.energy = 400
    fill.data.size = 5

    # Rim Light
    bpy.ops.object.light_add(type="AREA", location=(0, 5, 5))
    rim = bpy.context.active_object
    rim.data.energy = 600
    rim.data.size = 5


def setup_pro_camera(targets, view="front"):
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam

    # Calculate bounding box
    all_coords = []
    for obj in targets:
        for v in obj.bound_box:
            all_coords.append(obj.matrix_world @ mathutils.Vector(v))

    if not all_coords:
        return

    center = sum(all_coords, mathutils.Vector((0, 0, 0))) / len(all_coords)
    max_dist = max([(v - center).length for v in all_coords])

    # Camera Positioning for 'Luxury Front'
    if view == "front":
        cam.location = center + mathutils.Vector((0, -max_dist * 4, max_dist * 0.5))
    elif view == "back":
        cam.location = center + mathutils.Vector((0, max_dist * 4, max_dist * 0.5))

    # Point at product
    direction = center - cam.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    cam.rotation_euler = rot_quat.to_euler()


def main():
    # Args: blender -b -P script.py -- <input_glb> <output_png> <view>
    argv = sys.argv
    if "--" not in argv:
        return
    args = argv[argv.index("--") + 1 :]

    input_path = args[0]
    output_path = args[1]
    view = args[2] if len(args) > 2 else "front"

    clear_scene()
    setup_luxury_render_settings()
    meshes = import_product(input_path)
    setup_3point_lighting()
    setup_pro_camera(meshes, view)

    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"VERIFIED_RENDER_SUCCESS: {output_path}")


if __name__ == "__main__":
    main()
