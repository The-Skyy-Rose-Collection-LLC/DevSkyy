"""Phase 7 final QA: close-up renders of the actual shipped compressed GLB,
zoomed on the wrist/cuff and neck/head zones across multiple walk-cycle
frames, textured -- the specific defect classes bug-296 (sleeve-cuff
flare) and bug-297 (crack-seam) originally targeted. Independent of every
prior render in this session (fresh camera framing, fresh frame
selection).
Run: blender --background --factory-startup --python render_closeup_defect_check.py
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
arm_obj.animation_data.action = bpy.data.actions["walk"]

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x = 700
scene.render.resolution_y = 700
scene.render.image_settings.file_format = "PNG"

light_data = bpy.data.lights.new("sun", type="SUN")
light_obj = bpy.data.objects.new("sun", light_data)
scene.collection.objects.link(light_obj)
light_data.energy = 3.0

cam_data = bpy.data.cameras.new("cam")
cam_obj = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam_obj)
cam_data.lens = 85
scene.camera = cam_obj

# Close-up on the head/neck junction (crack-seam risk) -- fixed framing,
# varying only the pose frame. Target the JOINT itself (Head.head, the
# actual neck-Head boundary), not centered on the face -- pulled back
# slightly (0.5m) and aimed down 15deg to keep the collar/jaw seam in
# frame instead of just the upper face.
for frame in (1, 5, 9, 13, 17, 21):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    target = arm_obj.pose.bones["Head"].head
    cam_obj.location = (target.x, target.y - 0.5, target.z + 0.03)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    out = os.path.join(HERE, f"closeup_neck_{frame:02d}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {out}")

# Close-up on each wrist across the walk cycle (cuff-flare risk).
for frame in (1, 5, 9, 13, 17, 21):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    lh = arm_obj.pose.bones["LeftHand"].head
    cam_obj.location = (lh.x + 0.35, lh.y - 0.25, lh.z + 0.05)
    cam_obj.rotation_euler = (math.radians(90), 0, math.radians(55))
    out = os.path.join(HERE, f"closeup_leftwrist_{frame:02d}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {out}")
