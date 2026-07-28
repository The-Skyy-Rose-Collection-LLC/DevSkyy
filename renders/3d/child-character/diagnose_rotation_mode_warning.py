"""Root-cause check for build_idle_and_export.py's export warning
"Multiple rotation mode detected for Spine01/Spine/neck/Head": inspect
what rotation_mode is actually set on these bones' pose channels, and
whether each action's F-curves target rotation_euler vs
rotation_quaternion consistently.
Run: blender --background --factory-startup --python diagnose_rotation_mode_warning.py
"""

import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")

FLAGGED = ["Spine01", "Spine", "neck", "Head"]
for bone_name in FLAGGED:
    pb = arm_obj.pose.bones[bone_name]
    print(f"{bone_name}: current rotation_mode={pb.rotation_mode}")


def iter_fcurves(action):
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    yield fc


for action_name in ("idle", "walk"):
    action = bpy.data.actions.get(action_name)
    if action is None:
        print(f"\naction {action_name!r} not found")
        continue
    print(f"\naction '{action_name}':")
    dp_types = {}
    for fc in iter_fcurves(action):
        dp = fc.data_path
        if not dp.startswith('pose.bones["'):
            continue
        bone_name = dp.split('"')[1]
        if bone_name not in FLAGGED:
            continue
        kind = (
            "euler"
            if "rotation_euler" in dp
            else ("quat" if "rotation_quaternion" in dp else "other")
        )
        dp_types.setdefault(bone_name, set()).add(kind)
    for bone_name, kinds in dp_types.items():
        print(f"  {bone_name}: fcurve rotation types = {kinds}")
