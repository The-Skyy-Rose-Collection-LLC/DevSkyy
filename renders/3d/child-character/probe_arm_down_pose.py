"""Two-stage empirical probe for building a natural arm-down base pose on
this T-pose-rest rig, before authoring the walk cycle.

Stage A: find the local-axis+sign on Shoulder that lowers the arm (raw
T-pose probe already shows local-X on Shoulder produces world-Z motion;
this stage picks the SIGN that decreases Z, i.e. brings the hand down) and
measure the resulting hand position at candidate angles to pick a natural
resting magnitude (hand should end up below shoulder height, near hip
level -- not still near shoulder height nor overshooting past the hip).

Stage B: with that static offset applied to Shoulder, RE-PROBE Arm's own
local-X vs local-Z response in world Y (front-back swing) -- pose-bone
local rotations are always defined relative to the bone's OWN rest frame,
but the WORLD effect of a child bone's local rotation is carried by
whatever the parent is currently doing, so the axis that produced swing in
the raw T-pose context is not safe to assume unchanged once the parent
(Shoulder) has a large static offset applied. Re-probing in the ACTUAL
context the walk keyframes will use is the only reliable way to answer
this, per doctrine.md.

Run: blender --background --factory-startup --python probe_arm_down_pose.py
"""

import math
import os

import bpy
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-skinned.blend")

TEST_ANGLE_DEG = 5.0

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode="POSE")

for side in ("Left", "Right"):
    arm_obj.pose.bones[f"{side}Shoulder"].rotation_mode = "XYZ"
    arm_obj.pose.bones[f"{side}Arm"].rotation_mode = "XYZ"
    arm_obj.pose.bones[f"{side}ForeArm"].rotation_mode = "XYZ"

hips_z = arm_obj.pose.bones["Hips"].head.z
print(f"Hips head world z = {hips_z:.4f} (target hand-drop reference)\n")

print("=== Stage A: candidate Shoulder local-X angles -> resulting Hand world position ===")
for side in ("Left", "Right"):
    sh = arm_obj.pose.bones[f"{side}Shoulder"]
    hand = arm_obj.pose.bones[f"{side}Hand"]
    print(f"\n{side} side:")
    for angle_deg in (-30, -50, -70, -80, -90, -100):
        sh.rotation_euler = Euler((math.radians(angle_deg), 0.0, 0.0), "XYZ")
        bpy.context.view_layer.update()
        hand_tail = hand.tail.copy()
        print(
            f"  Shoulder local-X={angle_deg:+4d}deg -> Hand.tail world=({hand_tail.x:+.4f},{hand_tail.y:+.4f},{hand_tail.z:+.4f})"
        )
    sh.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()

CHOSEN_SHOULDER_ANGLE_DEG = -80.0
print(
    f"\n=== Stage B: re-probe Arm's local-X/Z response in world Y, WITH Shoulder held at {CHOSEN_SHOULDER_ANGLE_DEG} deg ==="
)
for side in ("Left", "Right"):
    sh = arm_obj.pose.bones[f"{side}Shoulder"]
    a = arm_obj.pose.bones[f"{side}Arm"]
    sh.rotation_euler = Euler((math.radians(CHOSEN_SHOULDER_ANGLE_DEG), 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()
    rest_tail = a.tail.copy()
    print(f"\n{side}Arm: rest_tail (with shoulder offset)={tuple(round(c,4) for c in rest_tail)}")
    for axis_idx, axis_name in enumerate(("X", "Y", "Z")):
        angles = [0.0, 0.0, 0.0]
        angles[axis_idx] = math.radians(TEST_ANGLE_DEG)
        a.rotation_euler = Euler(tuple(angles), "XYZ")
        bpy.context.view_layer.update()
        test_tail = a.tail.copy()
        a.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
        bpy.context.view_layer.update()
        delta = test_tail - rest_tail
        print(
            f"  local-{axis_name} +{TEST_ANGLE_DEG}deg -> world tail delta=({delta.x:+.5f}, {delta.y:+.5f}, {delta.z:+.5f})"
        )
    sh.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()

print("\n=== Stage B (ForeArm): re-probe with Shoulder offset applied ===")
for side in ("Left", "Right"):
    sh = arm_obj.pose.bones[f"{side}Shoulder"]
    fa = arm_obj.pose.bones[f"{side}ForeArm"]
    sh.rotation_euler = Euler((math.radians(CHOSEN_SHOULDER_ANGLE_DEG), 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()
    rest_tail = fa.tail.copy()
    print(
        f"\n{side}ForeArm: rest_tail (with shoulder offset)={tuple(round(c,4) for c in rest_tail)}"
    )
    for axis_idx, axis_name in enumerate(("X", "Y", "Z")):
        angles = [0.0, 0.0, 0.0]
        angles[axis_idx] = math.radians(TEST_ANGLE_DEG)
        fa.rotation_euler = Euler(tuple(angles), "XYZ")
        bpy.context.view_layer.update()
        test_tail = fa.tail.copy()
        fa.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
        bpy.context.view_layer.update()
        delta = test_tail - rest_tail
        print(
            f"  local-{axis_name} +{TEST_ANGLE_DEG}deg -> world tail delta=({delta.x:+.5f}, {delta.y:+.5f}, {delta.z:+.5f})"
        )
    sh.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()

bpy.ops.object.mode_set(mode="OBJECT")
