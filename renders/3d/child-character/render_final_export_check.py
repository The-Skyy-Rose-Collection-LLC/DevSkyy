"""Independent visual gate for the FINAL EXPORTED GLB (child-character-final.glb),
not the pre-export .blend -- confirms the exporter's own 4-joint-influence
truncation (diagnose_joint_influences.py: 1592 verts affected, 80% at the
shoulder blend zone, max 13.3% weight redistributed) doesn't introduce a
visible shoulder-seam artifact once actually posed, and that both 'idle'
and 'walk' clips import and evaluate correctly from the shipped file.
Run: blender --background --factory-startup --python render_final_export_check.py
"""

import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "child-character-final.glb")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=GLB)

arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh_obj = max(
    (o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices)
)

actions = sorted(a.name for a in bpy.data.actions)
print(f"actions in exported GLB: {actions}")
if actions != ["idle", "walk"]:
    raise RuntimeError(f"expected exactly ['idle','walk'], got {actions}")

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
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

light_data = bpy.data.lights.new("sun", type="SUN")
light_obj = bpy.data.objects.new("sun", light_data)
scene.collection.objects.link(light_obj)
light_data.energy = 3.0

arm_obj.animation_data.action = bpy.data.actions["walk"]
cam_obj.location = (0.9, -1.9, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(20))
for frame in (1, 9, 13, 21):
    scene.frame_set(frame)
    out = os.path.join(HERE, f"final_export_walk_{frame:02d}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {out}")

arm_obj.animation_data.action = bpy.data.actions["idle"]
for frame in (1, 19, 37, 55):
    scene.frame_set(frame)
    out = os.path.join(HERE, f"final_export_idle_{frame:02d}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {out}")
