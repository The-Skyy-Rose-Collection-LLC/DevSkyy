"""Independent visual gate for skin_weight_child.py: pose the rig into a
moderate arm-raise + elbow-bend + hip-twist test pose and render before/
after -- confirms weights DEFORM correctly (not just that the numeric sums
are right) and specifically checks for bug-296's sleeve-cuff-flare (cuff
geometry ballooning outward on rotation) and bug-297's crack-seam (a visible
gap/tear at the neck-head boundary) under actual deformation, which a
rest-pose-only weight-sum check cannot catch.
Run: blender --background --factory-startup --python render_skin_pose_check.py
"""

import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-skinned.blend")
OUT_REST = os.path.join(HERE, "pose_check_rest.png")
OUT_POSED = os.path.join(HERE, "pose_check_posed.png")

bpy.ops.wm.open_mainfile(filepath=BLEND)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.image_settings.file_format = "PNG"

dims = mesh_obj.dimensions
center_z = dims.z / 2.0

cam_data = bpy.data.cameras.new("cam")
cam_obj = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam_obj)
cam_data.lens = 50
scene.camera = cam_obj
cam_obj.location = (0, -2.2, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, 0)

light_data = bpy.data.lights.new("sun", type="SUN")
light_obj = bpy.data.objects.new("sun", light_data)
scene.collection.objects.link(light_obj)
light_data.energy = 3.0

scene.render.filepath = OUT_REST
bpy.ops.render.render(write_still=True)
print(f"Rendered {OUT_REST}")

bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode="POSE")
pb = arm_obj.pose.bones

pb["LeftArm"].rotation_mode = "XYZ"
pb["LeftArm"].rotation_euler = (0, 0, math.radians(-45))
pb["LeftForeArm"].rotation_mode = "XYZ"
pb["LeftForeArm"].rotation_euler = (math.radians(60), 0, 0)
pb["RightArm"].rotation_mode = "XYZ"
pb["RightArm"].rotation_euler = (0, 0, math.radians(45))
pb["RightForeArm"].rotation_mode = "XYZ"
pb["RightForeArm"].rotation_euler = (math.radians(60), 0, 0)
pb["Spine"].rotation_mode = "XYZ"
pb["Spine"].rotation_euler = (0, 0, math.radians(15))
pb["Head"].rotation_mode = "XYZ"
pb["Head"].rotation_euler = (0, 0, math.radians(-20))

bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode="OBJECT")

scene.render.filepath = OUT_POSED
bpy.ops.render.render(write_still=True)
print(f"Rendered {OUT_POSED}")
