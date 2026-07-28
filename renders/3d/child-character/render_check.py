"""Render a textured bind-pose front view of a GLB for a fresh vision check.
Run: blender --background --factory-startup --python render_check.py -- <glb_path> <out_png>
"""

import math
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
GLB, OUT_PNG = argv[0], argv[1]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=GLB)

mesh_objs = [o for o in bpy.data.objects if o.type == "MESH"]
mesh_obj = max(mesh_objs, key=lambda o: len(o.data.vertices))

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "MATCAP"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.image_settings.file_format = "PNG"

dims = mesh_obj.dimensions
height = dims.z if dims.z > 0 else 1.0
center_z = height / 2.0

cam_data = bpy.data.cameras.new("cam")
cam_obj = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = (0, -2.2, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, 0)
cam_data.lens = 50
scene.camera = cam_obj

light_data = bpy.data.lights.new("sun", type="SUN")
light_obj = bpy.data.objects.new("sun", light_data)
scene.collection.objects.link(light_obj)
light_data.energy = 3.0

scene.render.filepath = OUT_PNG
bpy.ops.render.render(write_still=True)
print(f"Rendered {OUT_PNG}")
