"""Independent visual gate for build_walk_cycle.py: render several frames
across the baked walk cycle to confirm the arm-down offset + swing looks
anatomically natural (not still T-pose, not clipping through the body) and
that legs/feet move plausibly -- a fresh render, independent of the
fcurve-math verification already run in build_walk_cycle.py itself.
Run: blender --background --factory-startup --python render_walk_frames.py
"""

import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")

action = bpy.data.actions.get("ChildWalk_Baked")
if action is None:
    raise RuntimeError("ChildWalk_Baked action not found")
if arm_obj.animation_data is None:
    arm_obj.animation_data_create()
arm_obj.animation_data.action = action

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x = 700
scene.render.resolution_y = 950
scene.render.image_settings.file_format = "PNG"

dims = mesh_obj.dimensions
center_z = dims.z / 2.0

cam_data = bpy.data.cameras.new("cam")
cam_obj = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam_obj)
cam_data.lens = 50
scene.camera = cam_obj
light_data = bpy.data.lights.new("sun", type="SUN")
light_obj = bpy.data.objects.new("sun", light_data)
scene.collection.objects.link(light_obj)
light_data.energy = 3.0

cam_obj.location = (0, -2.0, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, 0)
for frame in (1, 5, 9, 13, 17, 21):
    scene.frame_set(frame)
    out = os.path.join(HERE, f"walk_frame_{frame:02d}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {out}")

# Side view -- forward/backward leg+arm swing is along this camera's
# depth axis in the front view, effectively invisible there. A side
# camera is required to actually see gait swing.
cam_obj.location = (2.0, 0, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))
for frame in (1, 5, 9, 13, 17, 21):
    scene.frame_set(frame)
    out = os.path.join(HERE, f"walk_frame_side_{frame:02d}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {out}")
