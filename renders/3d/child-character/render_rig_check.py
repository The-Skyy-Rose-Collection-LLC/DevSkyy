"""Visual gate for build_rig.py's landmark placement: bright-red joint markers
+ xray shading (per the Do-Not-Repeat lesson -- default gray markers against
gray Workbench MATCAP are fully occluded and prove nothing).
Run: blender --background --factory-startup --python render_rig_check.py
"""

import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-rig.blend")
MESH_GLB = os.path.join(HERE, "child-decimated.glb")
OUT_FRONT = os.path.join(HERE, "rig_check_front.png")
OUT_SIDE = os.path.join(HERE, "rig_check_side.png")

bpy.ops.wm.open_mainfile(filepath=BLEND)
bpy.ops.import_scene.gltf(filepath=MESH_GLB)
mesh_obj = max(
    (o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices)
)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")

red_mat = bpy.data.materials.new("JointMarker")
red_mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)

for b in arm_obj.data.bones:
    for point, suffix in ((b.head_local, "head"), (b.tail_local, "tail")):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.01, location=arm_obj.matrix_world @ point)
        marker = bpy.context.active_object
        marker.name = f"marker_{b.name}_{suffix}"
        marker.data.materials.append(red_mat)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "FLAT"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_xray = True
scene.display.shading.xray_alpha = 0.35
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.image_settings.file_format = "PNG"

for m in bpy.data.materials:
    if m is not red_mat:
        m.diffuse_color = (0.6, 0.6, 0.65, 1.0)

dims = mesh_obj.dimensions
center_z = dims.z / 2.0

light_data = bpy.data.lights.new("sun", type="SUN")
light_obj = bpy.data.objects.new("sun", light_data)
scene.collection.objects.link(light_obj)
light_data.energy = 3.0

cam_data = bpy.data.cameras.new("cam")
cam_obj = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam_obj)
cam_data.lens = 50
scene.camera = cam_obj

cam_obj.location = (0, -2.2, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, 0)
scene.render.filepath = OUT_FRONT
bpy.ops.render.render(write_still=True)
print(f"Rendered {OUT_FRONT}")

cam_obj.location = (2.2, 0, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))
scene.render.filepath = OUT_SIDE
bpy.ops.render.render(write_still=True)
print(f"Rendered {OUT_SIDE}")
