"""Empirical axis-mapping probe for the child rig's arm/leg bones.

The rest pose is a genuine T-pose scan (arms horizontal, pointing sideways)
-- unlike the Love Hurts Girl rig, whose rest pose already had arms roughly
hanging at the sides. bake_walk_retarget.py's sign-probe assumed a
hanging-arm rest pose (local-X rotation = forward/backward swing, world Y
motion). Confirmed this session (build_walk_cycle.py's first run):
LeftArm's local-X 5deg probe produced delta=(-0.0005, 0.0, 0.0117) -- world Y
motion is ~0, world Z motion is the actual response. This means local-X on
THIS rig's T-pose arm performs a RAISE/LOWER (abduction) motion, not a
forward/backward swing -- a real physical consequence of the different
rest orientation, not a bug.

This script probes ALL THREE local axes (X, Y, Z) on each arm/leg bone,
individually, and reports the resulting world-space tail delta for each --
producing an evidence-based map of "which axis does what" instead of
assuming the girl rig's axis semantics carry over.

Run: blender --background --factory-startup --python probe_arm_axes.py
"""

import math
import os

import bpy
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-skinned.blend")

TEST_ANGLE_DEG = 5.0
BONES_TO_PROBE = [
    "LeftShoulder",
    "LeftArm",
    "LeftForeArm",
    "RightShoulder",
    "RightArm",
    "RightForeArm",
    "LeftUpLeg",
    "LeftLeg",
    "RightUpLeg",
    "RightLeg",
    "LeftFoot",
    "RightFoot",
]

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode="POSE")

for bone_name in BONES_TO_PROBE:
    pb = arm_obj.pose.bones[bone_name]
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()
    rest_tail = pb.tail.copy()
    rest_head = pb.head.copy()
    bone_dir = (rest_tail - rest_head).normalized()

    print(
        f"\n{bone_name}: rest_head={tuple(round(c,4) for c in rest_head)} rest_tail={tuple(round(c,4) for c in rest_tail)} dir={tuple(round(c,3) for c in bone_dir)}"
    )

    for axis_idx, axis_name in enumerate(("X", "Y", "Z")):
        angles = [0.0, 0.0, 0.0]
        angles[axis_idx] = math.radians(TEST_ANGLE_DEG)
        pb.rotation_euler = Euler(tuple(angles), "XYZ")
        bpy.context.view_layer.update()
        test_tail = pb.tail.copy()
        pb.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
        bpy.context.view_layer.update()
        delta = test_tail - rest_tail
        print(
            f"  local-{axis_name} +{TEST_ANGLE_DEG}deg -> world tail delta=({delta.x:+.5f}, {delta.y:+.5f}, {delta.z:+.5f})"
        )

bpy.ops.object.mode_set(mode="OBJECT")
