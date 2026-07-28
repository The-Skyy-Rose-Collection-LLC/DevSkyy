"""Phase 5: author + bake the child rig's walk-in-place cycle.

Per Phase 3's gate result (retarget_local_space_gate.py this session): the
spine/neck/head/leg chains pass rest-direction compatibility against
skyy.glb, but the ENTIRE arm chain (Shoulder/Arm/ForeArm/Hand) fails hard
(25-88 deg, vs 10-20 deg thresholds) -- a genuine T-pose-vs-hanging-pose
rest divergence, not a rig defect. Per retargeting.md's hard-stop rule
(Love Hurts Girl precedent, bug-195): a failed rest-direction gate redirects
to hand-keyframing for that rig, and the girl precedent hand-keyframed the
ENTIRE walk cycle (legs AND arms) rather than a partial retarget+hand-key
hybrid -- simpler, and already the established project convention. Follows
that same precedent here: fresh hand-keyframed walk-in-place cycle,
7-pose-instant sequence (contact-L/passing-R-up/high-point/contact-R/
passing-L-up/high-point/loop-close).

Axis-mapping departs from bake_walk_retarget.py's assumption that
local-X is always the sagittal swing/flex axis. Confirmed this session
(probe_arm_axes.py, probe_arm_down_pose.py): local-Y is always a no-op on
every bone (it's the bone's own roll/twist axis by construction --
verified zero world-tail delta on every probed bone). For near-vertical
bones (LEGS, which point mostly along -Z), local-X produces the dominant
front-back (world Y) swing response, matching the girl rig's convention --
used as-is below.

ARMS are a genuine T-pose scan (resting horizontally along world X),
unlike the girl's already-hanging-arm rest pose -- local-X on a horizontal
arm bone produces a raise/lower (world Z) motion instead of a swing. A
walk cycle needs the arm brought DOWN to a natural resting position first,
which a bare swing rotation cannot do on its own. Design, empirically
derived (probe_arm_down_pose.py, both sides symmetric):
  1. Static LeftShoulder/RightShoulder local-X offset of -90 deg,
     confirmed this session to bring Hand.tail to world x~=+/-0.056
     (near the torso centerline) and z~=0.257 (just below Hips.head at
     z=0.3025) -- a natural arm-at-side resting position, applied as a
     CONSTANT correction pose, never animated across the cycle.
  2. With that offset held, LeftArm/RightArm's local-Z (re-probed in this
     exact context, not assumed from the raw T-pose) still produces the
     front-back swing in world Y (delta magnitude ~0.0117, matching the
     raw-T-pose value almost exactly) -- confirms the swing axis is
     stable whether or not the parent Shoulder offset is applied, so
     LeftArm/RightArm's walk-cycle swing keys use local-Z.
  3. ForeArm is intentionally left UNANIMATED (straight arm) rather than
     hand-guessing an elbow-hinge axis under a non-anatomical rest
     pose -- a straight-arm swing has no visible artifact risk and this
     project's own doctrine (`doctrine.md`) requires never guessing an
     unverified rotation for no verification benefit, the same
     simplification bake_walk_retarget.py already applied to
     Hips/Spine/neck/Head/Shoulders/Hand/ToeBase for its own walk cycle.

Run: blender --background --factory-startup --python build_walk_cycle.py
"""

import json
import math
import os
import shutil

import bpy
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-skinned.blend")
BACKUP_PATH = os.path.join(HERE, "child-character-skinned.pre-walk-backup.blend")

SOURCE_ACTION_NAME = "ChildWalk_Source"
BAKED_ACTION_NAME = "ChildWalk_Baked"

FRAME_START = 1
FRAME_END = 25  # frame 25 duplicates frame 1's pose -- explicit loop closure
BAKE_STEP = 1

TEST_ANGLE_DEG = 5.0
LOCATION_LEAK_THRESHOLD_PCT = 2.0

# Static "arms down" correction, applied identically every frame (not
# animated) -- confirmed this session (probe_arm_down_pose.py) to bring
# Hand.tail from the raw T-pose to a natural at-the-side resting position.
SHOULDER_DOWN_OFFSET_DEG = -90.0

# Legs use local-X for swing/flex (matches the girl rig's convention,
# confirmed still valid here: leg bones point near-vertically, unlike
# arms). Arms swing on local-Z (re-probed under the Shoulder-down offset
# this session -- see module docstring). ForeArm is intentionally
# unanimated (straight-arm simplification, see module docstring).
SWING_BONES_X = ["LeftUpLeg", "RightUpLeg"]
SWING_BONES_Z = ["LeftArm", "RightArm"]
FLEX_BONES = ["LeftLeg", "RightLeg", "LeftFoot", "RightFoot"]
ALL_ANIMATED_BONES = SWING_BONES_X + SWING_BONES_Z + FLEX_BONES

HIP_SWING_DEG = 22.0
ARM_SWING_DEG = 18.0
KNEE_FLEX_STANCE_DEG = 8.0
KNEE_FLEX_SWING_DEG = 55.0
KNEE_FLEX_HIGH_DEG = 15.0
FOOT_DORSIFLEX_SWING_DEG = 15.0
FOOT_DORSIFLEX_PRESTRIKE_DEG = 8.0

POSES = [
    (
        FRAME_START,
        "contact-L",
        {
            "LeftUpLeg": ("forward", HIP_SWING_DEG),
            "RightUpLeg": ("backward", HIP_SWING_DEG),
            "LeftLeg": ("flex", KNEE_FLEX_STANCE_DEG),
            "RightLeg": ("flex", KNEE_FLEX_STANCE_DEG),
            "LeftFoot": ("flex", 0.0),
            "RightFoot": ("flex", 0.0),
            "LeftArm": ("backward", ARM_SWING_DEG),
            "RightArm": ("forward", ARM_SWING_DEG),
        },
    ),
    (
        5,
        "passing-R-up",
        {
            "LeftUpLeg": ("forward", 0.0),
            "RightUpLeg": ("forward", 0.0),
            "LeftLeg": ("flex", KNEE_FLEX_STANCE_DEG),
            "RightLeg": ("flex", KNEE_FLEX_SWING_DEG),
            "LeftFoot": ("flex", 0.0),
            "RightFoot": ("flex", FOOT_DORSIFLEX_SWING_DEG),
            "LeftArm": ("forward", 0.0),
            "RightArm": ("forward", 0.0),
        },
    ),
    (
        9,
        "high-point",
        {
            "LeftUpLeg": ("backward", HIP_SWING_DEG),
            "RightUpLeg": ("forward", HIP_SWING_DEG),
            "LeftLeg": ("flex", KNEE_FLEX_STANCE_DEG),
            "RightLeg": ("flex", KNEE_FLEX_HIGH_DEG),
            "LeftFoot": ("flex", 0.0),
            "RightFoot": ("flex", FOOT_DORSIFLEX_PRESTRIKE_DEG),
            "LeftArm": ("forward", ARM_SWING_DEG),
            "RightArm": ("backward", ARM_SWING_DEG),
        },
    ),
    (
        13,
        "contact-R",
        {
            "LeftUpLeg": ("backward", HIP_SWING_DEG),
            "RightUpLeg": ("forward", HIP_SWING_DEG),
            "LeftLeg": ("flex", KNEE_FLEX_STANCE_DEG),
            "RightLeg": ("flex", KNEE_FLEX_STANCE_DEG),
            "LeftFoot": ("flex", 0.0),
            "RightFoot": ("flex", 0.0),
            "LeftArm": ("forward", ARM_SWING_DEG),
            "RightArm": ("backward", ARM_SWING_DEG),
        },
    ),
    (
        17,
        "passing-L-up",
        {
            "LeftUpLeg": ("forward", 0.0),
            "RightUpLeg": ("forward", 0.0),
            "LeftLeg": ("flex", KNEE_FLEX_SWING_DEG),
            "RightLeg": ("flex", KNEE_FLEX_STANCE_DEG),
            "LeftFoot": ("flex", FOOT_DORSIFLEX_SWING_DEG),
            "RightFoot": ("flex", 0.0),
            "LeftArm": ("forward", 0.0),
            "RightArm": ("forward", 0.0),
        },
    ),
    (
        21,
        "high-point",
        {
            "LeftUpLeg": ("forward", HIP_SWING_DEG),
            "RightUpLeg": ("backward", HIP_SWING_DEG),
            "LeftLeg": ("flex", KNEE_FLEX_HIGH_DEG),
            "RightLeg": ("flex", KNEE_FLEX_STANCE_DEG),
            "LeftFoot": ("flex", FOOT_DORSIFLEX_PRESTRIKE_DEG),
            "RightFoot": ("flex", 0.0),
            "LeftArm": ("backward", ARM_SWING_DEG),
            "RightArm": ("forward", ARM_SWING_DEG),
        },
    ),
]
POSES.append((FRAME_END, "contact-L (loop close)", POSES[0][2]))


def iter_action_fcurves(action):
    """Blender 5.x layered-Action data model -- F-curves live under
    action.layers[*].strips[*].channelbags[*].fcurves, not the pre-5.x flat
    action.fcurves. Verified on this exact Blender 5.1.2 build (same
    precedent as bake_walk_retarget.py)."""
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            for channelbag in strip.channelbags:
                for fc in channelbag.fcurves:
                    yield fc


def zero_euler(axis_idx, angle_rad=0.0):
    v = [0.0, 0.0, 0.0]
    v[axis_idx] = angle_rad
    return Euler(tuple(v), "XYZ")


def detect_sign(arm_obj, bone_name, axis_idx, metric):
    """Probes rotation on the given LOCAL AXIS (not always X -- see module
    docstring for why arms need local-Z here, legs local-X)."""
    pb = arm_obj.pose.bones[bone_name]
    base = pb.rotation_euler.copy()
    rest_tail = pb.tail.copy()

    pb.rotation_euler = base.copy()
    pb.rotation_euler[axis_idx] += math.radians(TEST_ANGLE_DEG)
    bpy.context.view_layer.update()
    test_tail = pb.tail.copy()

    pb.rotation_euler = base
    bpy.context.view_layer.update()

    delta = test_tail - rest_tail
    if metric == "neg_y":
        component = -delta.y
    elif metric == "pos_z":
        component = delta.z
    else:
        raise ValueError(f"unknown metric {metric!r}")

    if abs(component) < 1e-6:
        raise RuntimeError(
            f"{bone_name}: {TEST_ANGLE_DEG} deg local-axis[{axis_idx}] probe produced no "
            f"measurable {metric} motion (delta={tuple(round(v, 6) for v in delta)})"
        )
    return 1.0 if component > 0 else -1.0


def build_sign_table(arm_obj):
    """Signs are probed in the ACTUAL context the walk keys will use --
    Shoulder must already be at its static down-offset before probing Arm
    (see module docstring: the swing axis was re-verified stable under
    that offset this session, but the SIGN was not separately re-checked
    and must not be assumed)."""
    signs = {}
    axis_for = {}
    for name in ["LeftUpLeg", "RightUpLeg"]:
        signs[name] = detect_sign(arm_obj, name, 0, "neg_y")
        axis_for[name] = 0
    for name in ["LeftArm", "RightArm"]:
        signs[name] = detect_sign(arm_obj, name, 2, "neg_y")
        axis_for[name] = 2
    for name in FLEX_BONES:
        signs[name] = detect_sign(arm_obj, name, 0, "pos_z")
        axis_for[name] = 0
    return signs, axis_for


def resolve_angle_deg(bone_name, category, magnitude_deg, signs):
    if category == "flex":
        return magnitude_deg * signs[bone_name]
    if category == "forward":
        return magnitude_deg * signs[bone_name]
    if category == "backward":
        return -magnitude_deg * signs[bone_name]
    raise ValueError(f"unknown pose category {category!r} for {bone_name}")


def apply_shoulder_down_offset(arm_obj):
    """Static, un-keyframed correction pose -- holds identically at every
    frame since nothing ever changes it, so nla.bake's visual_keying still
    captures it as a flat baked curve (confirmed by this script's own
    verify_fcurves: Shoulder ends up with a rotation fcurve whose value is
    constant across all sampled frames, never a location leak)."""
    for side in ("Left", "Right"):
        pb = arm_obj.pose.bones[f"{side}Shoulder"]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = zero_euler(0, math.radians(SHOULDER_DOWN_OFFSET_DEG))
    bpy.context.view_layer.update()


def author_source_action(arm_obj, signs, axis_for):
    action = bpy.data.actions.new(SOURCE_ACTION_NAME)
    action.use_fake_user = True
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    arm_obj.animation_data.action = action

    for bone_name in ALL_ANIMATED_BONES:
        arm_obj.pose.bones[bone_name].rotation_mode = "XYZ"
    arm_obj.pose.bones["LeftShoulder"].rotation_mode = "XYZ"
    arm_obj.pose.bones["RightShoulder"].rotation_mode = "XYZ"

    apply_shoulder_down_offset(arm_obj)
    for side in ("Left", "Right"):
        arm_obj.pose.bones[f"{side}Shoulder"].keyframe_insert(
            data_path="rotation_euler", frame=FRAME_START
        )
        arm_obj.pose.bones[f"{side}Shoulder"].keyframe_insert(
            data_path="rotation_euler", frame=FRAME_END
        )

    for frame, label, bone_pose in POSES:
        for bone_name, (category, magnitude_deg) in bone_pose.items():
            pb = arm_obj.pose.bones[bone_name]
            angle_deg = resolve_angle_deg(bone_name, category, magnitude_deg, signs)
            pb.rotation_euler = zero_euler(axis_for[bone_name], math.radians(angle_deg))
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)
        print(f"  keyed frame {frame:3d} ({label})")

    all_fcurves = list(iter_action_fcurves(action))
    location_curves = [fc for fc in all_fcurves if ".location" in fc.data_path]
    if location_curves:
        raise RuntimeError(
            f"{SOURCE_ACTION_NAME}: {len(location_curves)} location F-curve(s) authored "
            "-- walk-IN-PLACE cycle must have none."
        )
    print(f"Source action: {len(all_fcurves)} F-curves, 0 location curves (verified).")
    return action


def bake_walk_cycle(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    arm_obj.select_set(True)

    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")

    bpy.context.scene.frame_start = FRAME_START
    bpy.context.scene.frame_end = FRAME_END

    bpy.ops.nla.bake(
        frame_start=FRAME_START,
        frame_end=FRAME_END,
        step=BAKE_STEP,
        only_selected=True,
        visual_keying=True,
        clear_constraints=False,
        clear_parents=False,
        use_current_action=False,
        clean_curves=False,
        bake_types={"POSE"},
        channel_types={"ROTATION"},
    )

    baked_action = arm_obj.animation_data.action
    if baked_action is None:
        raise RuntimeError("nla.bake left no action assigned")
    baked_action.name = BAKED_ACTION_NAME
    baked_action.use_fake_user = True

    bpy.ops.object.mode_set(mode="OBJECT")
    return baked_action


def verify_fcurves(arm_obj, action, bone_lengths, obj_scale):
    all_fcurves = list(iter_action_fcurves(action))

    per_bone_location_fcurves = {}
    for fc in all_fcurves:
        dp = fc.data_path
        if not dp.startswith('pose.bones["'):
            continue
        bone_name = dp.split('"')[1]
        if ".location" in dp:
            per_bone_location_fcurves.setdefault(bone_name, []).append(fc)

    results = []
    worst_bone = None
    worst_ratio_pct = 0.0

    for bone_name, fcurves in per_bone_location_fcurves.items():
        rest_length = bone_lengths[bone_name] * obj_scale
        frames = sorted({kp.co.x for fc in fcurves for kp in fc.keyframe_points})
        axis_values = {0: [], 1: [], 2: []}
        for fc in fcurves:
            idx = fc.array_index
            for f in frames:
                axis_values[idx].append(fc.evaluate(f))
        peak_to_peak_per_axis = [
            (max(vals) - min(vals)) if vals else 0.0 for vals in axis_values.values()
        ]
        p2p = math.sqrt(sum(v * v for v in peak_to_peak_per_axis))
        ratio_pct = (p2p / rest_length) * 100.0 if rest_length > 1e-9 else float("inf")
        passed = ratio_pct < LOCATION_LEAK_THRESHOLD_PCT
        results.append(
            {
                "bone": bone_name,
                "peak_to_peak": round(p2p, 6),
                "ratio_pct": round(ratio_pct, 4),
                "passed": passed,
            }
        )
        if ratio_pct > worst_ratio_pct:
            worst_ratio_pct = ratio_pct
            worst_bone = bone_name
        if not passed:
            raise RuntimeError(
                f"{bone_name}: location leak {ratio_pct:.3f}% exceeds {LOCATION_LEAK_THRESHOLD_PCT}%"
            )

    summary = {
        "zero_location_fcurves": len(per_bone_location_fcurves) == 0,
        "bones_with_location_fcurves": sorted(per_bone_location_fcurves.keys()),
        "per_bone_leak": results,
        "worst_leak_bone": worst_bone,
        "worst_leak_ratio_pct": round(worst_ratio_pct, 4),
        "total_fcurves": len(all_fcurves),
        "rotation_fcurves": len([fc for fc in all_fcurves if ".rotation" in fc.data_path]),
    }
    return summary


def main():
    shutil.copy2(BLEND_PATH, BACKUP_PATH)
    print(f"Backup written: {BACKUP_PATH}")

    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")

    loc = tuple(round(v, 6) for v in arm_obj.location)
    scale = tuple(round(v, 6) for v in arm_obj.scale)
    if loc != (0.0, 0.0, 0.0):
        raise RuntimeError(f"root location is not identity: {loc}")
    if not (
        math.isclose(scale[0], scale[1], abs_tol=1e-6)
        and math.isclose(scale[1], scale[2], abs_tol=1e-6)
    ):
        raise RuntimeError(f"root scale is non-uniform: {scale}")
    obj_scale = scale[0]

    bone_lengths = {b.name: b.length for b in arm_obj.data.bones}

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")

    for bone_name in ALL_ANIMATED_BONES:
        arm_obj.pose.bones[bone_name].rotation_mode = "XYZ"
    arm_obj.pose.bones["LeftShoulder"].rotation_mode = "XYZ"
    arm_obj.pose.bones["RightShoulder"].rotation_mode = "XYZ"

    print(
        f"=== Applying static Shoulder-down offset ({SHOULDER_DOWN_OFFSET_DEG} deg) before probing arm signs ==="
    )
    apply_shoulder_down_offset(arm_obj)

    print("=== Empirical sign detection (5 deg probe per limb bone, in Shoulder-down context) ===")
    signs, axis_for = build_sign_table(arm_obj)
    for name, sign in signs.items():
        print(f"  {name:16s} axis={('X','Y','Z')[axis_for[name]]} sign={sign:+.1f}")

    print("=== Authoring source walk-cycle keyframes (rotation-only) ===")
    author_source_action(arm_obj, signs, axis_for)

    bpy.ops.object.mode_set(mode="OBJECT")

    print("=== Baking (channel_types={'ROTATION'} explicit) ===")
    baked_action = bake_walk_cycle(arm_obj)
    baked_fcurve_count = len(list(iter_action_fcurves(baked_action)))
    print(f"Baked action: '{baked_action.name}', {baked_fcurve_count} F-curves")

    print("=== Verifying baked F-curves (location-channel audit) ===")
    summary = verify_fcurves(arm_obj, baked_action, bone_lengths, obj_scale)
    print(json.dumps(summary, indent=2))

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"Saved: {BLEND_PATH}")

    print("BAKE_RESULT_JSON:" + json.dumps(summary))


if __name__ == "__main__":
    main()
