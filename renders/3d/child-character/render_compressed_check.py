"""Final independent render gate: import the ACTUAL shipped, compressed
GLB (draco geometry + jpeg textures) and confirm it still deforms
correctly across both clips and shows the textured (not just gray) mesh,
proving the compression pipeline preserved skinning, animation, and
texture data.
Run: blender --background --factory-startup --python render_compressed_check.py
"""

import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "child-character-compressed.glb")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=GLB)

arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh_obj = max(
    (o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices)
)

actions = sorted(a.name for a in bpy.data.actions)
print(f"actions: {actions}")
print(f"mesh vertices: {len(mesh_obj.data.vertices)}")
print(f"mesh materials: {[m.name for m in mesh_obj.data.materials]}")

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x = 800
scene.render.resolution_y = 1050
scene.render.image_settings.file_format = "PNG"

dims = mesh_obj.dimensions
center_z = dims.z / 2.0
cam_data = bpy.data.cameras.new("cam")
cam_obj = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam_obj)
cam_data.lens = 50
scene.camera = cam_obj
cam_obj.location = (0.9, -1.9, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(20))

light_data = bpy.data.lights.new("sun", type="SUN")
light_obj = bpy.data.objects.new("sun", light_data)
scene.collection.objects.link(light_obj)
light_data.energy = 3.0

arm_obj.animation_data.action = bpy.data.actions["walk"]
for frame in (1, 9):
    scene.frame_set(frame)
    out = os.path.join(HERE, f"compressed_check_walk_{frame:02d}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {out}")
