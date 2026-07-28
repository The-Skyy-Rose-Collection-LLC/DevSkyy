"""Numeric gate for the walk cycle's actual pose content: sample the baked
action's rotation values (in degrees) at each of the 7 pose-instant frames
for the swing/flex bones, and print them directly -- confirms the
alternating gait pattern is really keyed (not silently flat or collapsed),
independent of eyeballing render silhouettes.
Run: blender --background --factory-startup --python verify_walk_fcurve_values.py
"""

import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
action = bpy.data.actions["ChildWalk_Baked"]


def iter_fcurves(action):
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    yield fc


fcurve_by_bone_axis = {}
for fc in iter_fcurves(action):
    dp = fc.data_path
    if not dp.startswith('pose.bones["') or ".rotation_euler" not in dp:
        continue
    bone_name = dp.split('"')[1]
    fcurve_by_bone_axis.setdefault(bone_name, {})[fc.array_index] = fc

BONES = [
    "LeftUpLeg",
    "RightUpLeg",
    "LeftLeg",
    "RightLeg",
    "LeftFoot",
    "RightFoot",
    "LeftArm",
    "RightArm",
    "LeftShoulder",
    "RightShoulder",
]
FRAMES = [1, 5, 9, 13, 17, 21, 25]

for bone_name in BONES:
    axes = fcurve_by_bone_axis.get(bone_name, {})
    print(f"\n{bone_name}:")
    for frame in FRAMES:
        vals_deg = [
            round(math.degrees(axes[i].evaluate(frame)), 2) if i in axes else 0.0 for i in range(3)
        ]
        print(
            f"  frame {frame:3d}: X={vals_deg[0]:+7.2f} Y={vals_deg[1]:+7.2f} Z={vals_deg[2]:+7.2f}"
        )
