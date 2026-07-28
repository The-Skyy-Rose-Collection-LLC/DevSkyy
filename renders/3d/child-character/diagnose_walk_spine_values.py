"""Confirm the walk action's baked-but-unauthored quaternion fcurves on
Spine01/Spine/neck/Head are truly IDENTITY (harmless residue of nla.bake
selecting the whole armature) and not some accidental non-identity
rotation that would visibly clash with idle's genuine XYZ Euler animation
of the same bones.
Run: blender --background --factory-startup --python diagnose_walk_spine_values.py
"""

import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
action = bpy.data.actions["walk"]
arm_obj.animation_data.action = action


def iter_fcurves(action):
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    yield fc


FLAGGED = ["Spine01", "Spine", "neck", "Head"]
fcurve_by_bone = {}
for fc in iter_fcurves(action):
    dp = fc.data_path
    if not dp.startswith('pose.bones["') or "rotation_quaternion" not in dp:
        continue
    bone_name = dp.split('"')[1]
    if bone_name not in FLAGGED:
        continue
    fcurve_by_bone.setdefault(bone_name, {})[fc.array_index] = fc

for bone_name, axes in fcurve_by_bone.items():
    print(f"{bone_name}:")
    for frame in (1, 13, 25):
        quat = [
            round(axes[i].evaluate(frame), 6) if i in axes else (1.0 if i == 0 else 0.0)
            for i in range(4)
        ]
        is_identity = quat == [1.0, 0.0, 0.0, 0.0]
        print(f"  frame {frame}: quat={quat} identity={is_identity}")
