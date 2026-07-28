"""Numeric gate for the walk cycle's PHYSICAL correctness: local rotation
angle values alone can be misleading (verify_walk_fcurve_values.py showed
LeftArm and RightArm often carry IDENTICAL local-Z angles at the same
frame, e.g. +18deg at frame 1, despite the pose table specifying opposite
"backward"/"forward" categories) -- because detect_sign's empirically
measured sign differs between LeftArm (-1) and RightArm (+1), an identical
local angle can still correspond to opposite WORLD-space motion. This
script settles the question directly: evaluate the baked action at each
pose-instant frame and measure each Hand/Foot bone's WORLD-space Y
position (front-back, the walk direction) relative to the Hips -- the
actual physical quantity a viewer would see, independent of local-axis
sign conventions.

Confirms: (a) left/right arms swing in COUNTER-phase (one forward while
the other is back, standard contralateral gait), (b) left/right legs swing
in counter-phase, and (c) the SAME-side arm/leg are in the correct
contralateral relationship to each other (left arm forward when right leg
forward, matching natural human gait -- not same-side arm/leg moving
together, which would look robotic/wrong).

Run: blender --background --factory-startup --python verify_walk_world_motion.py
"""

import json
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
action = bpy.data.actions["ChildWalk_Baked"]
arm_obj.animation_data.action = action

FRAMES = [1, 5, 9, 13, 17, 21, 25]
BONES = ["LeftHand", "RightHand", "LeftFoot", "RightFoot", "LeftToeBase", "RightToeBase"]

print(f"{'frame':>6} " + " ".join(f"{b:>16}" for b in BONES))
world_y = {b: [] for b in BONES}
for frame in FRAMES:
    bpy.context.scene.frame_set(frame)
    row = [frame]
    for b in BONES:
        y = arm_obj.pose.bones[b].tail.y
        world_y[b].append(y)
        row.append(round(y, 4))
    print(f"{row[0]:>6} " + " ".join(f"{v:>16.4f}" for v in row[1:]))

print("\n=== Counter-phase checks (world Y correlation, should be strongly negative) ===")


def correlation(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va < 1e-12 or vb < 1e-12:
        return 0.0
    return cov / (va**0.5 * vb**0.5)


pairs = [
    ("LeftHand", "RightHand", "arms should swing OPPOSITE"),
    ("LeftToeBase", "RightToeBase", "legs should swing OPPOSITE"),
    ("LeftHand", "RightToeBase", "left arm + right leg should swing TOGETHER (contralateral gait)"),
    ("RightHand", "LeftToeBase", "right arm + left leg should swing TOGETHER (contralateral gait)"),
]

results = {}
for a_name, b_name, desc in pairs:
    corr = correlation(world_y[a_name], world_y[b_name])
    results[f"{a_name}_vs_{b_name}"] = round(corr, 4)
    print(f"  {a_name:16s} vs {b_name:16s} corr={corr:+.4f}  ({desc})")

opposite_pass = (
    results["LeftHand_vs_RightHand"] < -0.5 and results["LeftToeBase_vs_RightToeBase"] < -0.5
)
contralateral_pass = (
    results["LeftHand_vs_RightToeBase"] > 0.5 and results["RightHand_vs_LeftToeBase"] > 0.5
)
print(f"\nOPPOSITE-SIDE-SWING PASS (corr<-0.5): {opposite_pass}")
print(f"CONTRALATERAL-GAIT PASS (corr>0.5): {contralateral_pass}")
print(
    "RESULT_JSON "
    + json.dumps(
        {
            "correlations": results,
            "opposite_pass": opposite_pass,
            "contralateral_pass": contralateral_pass,
        }
    )
)
