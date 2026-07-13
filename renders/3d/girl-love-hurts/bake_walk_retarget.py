"""Author + bake the Love Hurts girl rig's walk-in-place cycle (locked plan step).

Fork taken this run: fresh_keyframe (Plan B -- see .wolf/cerebrum.md 2026-07-10:
retargeting from skyy.glb was ABANDONED, gate_bone_direction.py failed
critical bones). No walk animation exists anywhere yet (verified this session:
0 actions in love-hurts-girl-rig.blend, 0 animations in the exported .glb) --
so this step both AUTHORS the fresh-keyframed walk (the named 6-pose sequence:
contact-L, passing-R-up, high-point, contact-R, passing-L-up, high-point,
loop-close to contact-L) and BAKES it via `bpy.ops.nla.bake` with
`channel_types={'ROTATION'}` explicitly (excluding the default's LOCATION and
SCALE) -- a walk-IN-PLACE cycle, so no bone (least of all the parentless Hips
root) ever needs a location keyframe.

Per-bone swing/flex rotation SIGNS are not hand-guessed: `detect_sign()` applies
a small (5 deg) test rotation to each limb bone in isolation, reads the
resulting world-space tail delta, and picks the sign empirically -- the same
"can this check fail" discipline gate_bone_direction.py uses for its rest-pose
angle gate. Hips/Spine/neck/Head/Shoulders/Hand/ToeBase/head*/foot(other than
dorsiflex) bones are left at identity rotation (unanimated) -- deliberate
simplification: the named pose sequence describes leg/arm gait mechanics, and
skipping torso counter-twist avoids introducing an unverifiable-sign rotation
for no verification benefit.

Verification (this same script, run after the bake): parse the baked action's
F-curves directly (`action.fcurves`, `data_path` per bone). Assert location
channel count == 0 per bone. Where nonzero (should never happen given
channel_types={'ROTATION'}), compute peak-to-peak translation / bone rest
length (root-scale-normalized) and compare to the 2% threshold; fail loudly if
exceeded.

Run:
    blender -b --factory-startup -P bake_walk_retarget.py
"""

import json
import math
import shutil

import bpy
from mathutils import Euler

BLEND_PATH = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/"
    "renders/3d/girl-love-hurts/love-hurts-girl-rig.blend"
)
BACKUP_PATH = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/"
    "renders/3d/girl-love-hurts/love-hurts-girl-rig.pre-bake-backup.blend"
)

ARMATURE_NAME = "GirlArmature"

SOURCE_ACTION_NAME = "GirlWalk_Source"
BAKED_ACTION_NAME = "GirlWalk_Baked"

FRAME_START = 1
FRAME_END = 25  # frame 25 duplicates frame 1's pose -- explicit loop closure
BAKE_STEP = 1

TEST_ANGLE_DEG = 5.0  # small-angle probe for empirical sign detection
LOCATION_LEAK_THRESHOLD_PCT = 2.0  # peak-to-peak / rest-length, percent

# Bones whose local-X rotation swings the limb fore/aft from the hip/shoulder
# joint ("swing" bones) vs. bones whose local-X rotation flexes a hinge joint
# for ground/body clearance ("flex" bones, e.g. knee/elbow/ankle).
SWING_BONES = ["LeftUpLeg", "RightUpLeg", "LeftArm", "RightArm"]
FLEX_BONES = ["LeftLeg", "RightLeg", "LeftForeArm", "RightForeArm", "LeftFoot", "RightFoot"]
ALL_ANIMATED_BONES = SWING_BONES + FLEX_BONES

HIP_SWING_DEG = 24.0
ARM_SWING_DEG = 20.0
KNEE_FLEX_STANCE_DEG = 8.0
KNEE_FLEX_SWING_DEG = 55.0
KNEE_FLEX_HIGH_DEG = 15.0
ELBOW_FLEX_BASE_DEG = 12.0
ELBOW_FLEX_SWING_DEG = 18.0
FOOT_DORSIFLEX_SWING_DEG = 15.0
FOOT_DORSIFLEX_PRESTRIKE_DEG = 8.0

# Pose table -- literally the locked-plan pose sequence, 7 keyframe instants
# (frame 25 = frame 1, closing the loop). Each bone maps to (category, magnitude_deg).
# category in {"forward","backward"} (SWING_BONES, signed by detect_sign "neg_y"),
#            {"flex"} (FLEX_BONES, magnitude only, signed by detect_sign "pos_z"),
#            "neutral" (0 deg, no sign needed).
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
            "LeftForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
            "RightForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
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
            "LeftForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
            "RightForeArm": ("flex", ELBOW_FLEX_SWING_DEG),
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
            "LeftForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
            "RightForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
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
            "LeftForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
            "RightForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
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
            "LeftForeArm": ("flex", ELBOW_FLEX_SWING_DEG),
            "RightForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
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
            "LeftForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
            "RightForeArm": ("flex", ELBOW_FLEX_BASE_DEG),
        },
    ),
]
# Loop-close: frame FRAME_END repeats frame FRAME_START's pose exactly.
POSES.append((FRAME_END, "contact-L (loop close)", POSES[0][2]))


def iter_action_fcurves(action):
    """Blender 5.x layered-Action data model: F-curves no longer live at
    `action.fcurves` -- they're nested under `action.layers[*].strips[*]
    .channelbags[*].fcurves`. Verified this session via bpy introspection
    against this exact Blender 5.1.2 build (no `.fcurves` attribute on
    Action; `keyframe_insert` auto-creates a Layer/KEYFRAME-strip/Channelbag
    per slot). Flattens across every layer/strip/channelbag so callers can
    treat it like the pre-5.x flat `action.fcurves` list.
    """
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            for channelbag in strip.channelbags:
                for fc in channelbag.fcurves:
                    yield fc


def detect_sign(arm_obj, bone_name, metric):
    """Empirically determine the local-X rotation sign for `bone_name` that
    produces the desired world-space tail motion for `metric`:

      "neg_y"  -- forward swing (tail world Y decreases from rest)
      "pos_z"  -- flexion / clearance (tail world Z increases from rest)

    Applies TEST_ANGLE_DEG, reads the resulting tail delta, resets to rest,
    returns +1.0 or -1.0. This can fail loudly (raises) if the probe produces
    no measurable motion -- a genuine setup defect, not something to paper
    over with a hardcoded guess.
    """
    pb = arm_obj.pose.bones[bone_name]
    pb.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()
    rest_tail = pb.tail.copy()

    pb.rotation_euler = Euler((math.radians(TEST_ANGLE_DEG), 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()
    test_tail = pb.tail.copy()

    pb.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
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
            f"{bone_name}: {TEST_ANGLE_DEG} deg local-X probe produced no measurable "
            f"{metric} motion (delta={tuple(round(v, 6) for v in delta)}) -- cannot "
            "determine rotation sign, treating as a retargeting-setup bug."
        )
    return 1.0 if component > 0 else -1.0


def build_sign_table(arm_obj):
    signs = {}
    for name in SWING_BONES:
        signs[name] = detect_sign(arm_obj, name, "neg_y")
    for name in FLEX_BONES:
        signs[name] = detect_sign(arm_obj, name, "pos_z")
    return signs


def resolve_angle_deg(bone_name, category, magnitude_deg, signs):
    if category == "neutral":
        return 0.0
    if category == "flex":
        return magnitude_deg * signs[bone_name]
    if category == "forward":
        return magnitude_deg * signs[bone_name]
    if category == "backward":
        return -magnitude_deg * signs[bone_name]
    raise ValueError(f"unknown pose category {category!r} for {bone_name}")


def author_source_action(arm_obj, signs):
    action = bpy.data.actions.new(SOURCE_ACTION_NAME)
    action.use_fake_user = True
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    arm_obj.animation_data.action = action

    for bone_name in ALL_ANIMATED_BONES:
        arm_obj.pose.bones[bone_name].rotation_mode = "XYZ"

    for frame, label, bone_pose in POSES:
        for bone_name, (category, magnitude_deg) in bone_pose.items():
            pb = arm_obj.pose.bones[bone_name]
            angle_deg = resolve_angle_deg(bone_name, category, magnitude_deg, signs)
            pb.rotation_euler = Euler((math.radians(angle_deg), 0.0, 0.0), "XYZ")
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)
        print(f"  keyed frame {frame:3d} ({label})")

    # Sanity: source action must carry rotation fcurves only, never location.
    all_fcurves = list(iter_action_fcurves(action))
    location_curves = [fc for fc in all_fcurves if ".location" in fc.data_path]
    if location_curves:
        raise RuntimeError(
            f"{SOURCE_ACTION_NAME}: {len(location_curves)} location F-curve(s) were "
            "authored -- this is a walk-IN-PLACE cycle, no bone should ever carry a "
            "location keyframe. Aborting before bake."
        )
    print(
        f"Source action '{SOURCE_ACTION_NAME}': {len(all_fcurves)} F-curves, "
        f"0 location curves (verified)."
    )
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
        channel_types={"ROTATION"},  # explicit -- excludes the default's LOCATION+SCALE
    )

    baked_action = arm_obj.animation_data.action
    if baked_action is None:
        raise RuntimeError("nla.bake did not leave a baked action assigned to the armature")
    baked_action.name = BAKED_ACTION_NAME
    baked_action.use_fake_user = True

    bpy.ops.object.mode_set(mode="OBJECT")
    return baked_action


def verify_fcurves(arm_obj, action, bone_lengths, obj_scale):
    """Parse the baked action's F-curves directly. Assert 0 location F-curves
    per bone; where nonzero (should be impossible given channel_types={'ROTATION'}
    at bake time), compute peak-to-peak / root-scale-normalized rest length
    and compare against LOCATION_LEAK_THRESHOLD_PCT.
    """
    all_fcurves = list(iter_action_fcurves(action))

    per_bone_location_fcurves = {}
    per_bone_location_count = {b.name: 0 for b in arm_obj.data.bones}
    for fc in all_fcurves:
        dp = fc.data_path
        if not dp.startswith('pose.bones["'):
            continue
        bone_name = dp.split('"')[1]
        if ".location" in dp:
            per_bone_location_fcurves.setdefault(bone_name, []).append(fc)
            per_bone_location_count[bone_name] = per_bone_location_count.get(bone_name, 0) + 1

    # Explicit per-bone assertion: location channel count == 0 for every bone
    # in the armature (not just the ones that happen to show up nonzero).
    for bone_name, count in per_bone_location_count.items():
        assert (
            count == 0 or bone_name in per_bone_location_fcurves
        ), f"{bone_name}: location fcurve bookkeeping inconsistent"

    results = []
    worst_bone = None
    worst_ratio_pct = 0.0

    for bone_name, fcurves in per_bone_location_fcurves.items():
        rest_length = bone_lengths[bone_name] * obj_scale
        # peak-to-peak translation vector magnitude across frames: sample every
        # keyframe co-frame present on any of this bone's location fcurves.
        frames = sorted({kp.co.x for fc in fcurves for kp in fc.keyframe_points})
        axis_values = {0: [], 1: [], 2: []}
        for fc in fcurves:
            idx = fc.array_index
            for f in frames:
                axis_values[idx].append(fc.evaluate(f))
        peak_to_peak_per_axis = [
            (max(vals) - min(vals)) if vals else 0.0 for vals in axis_values.values()
        ]
        # combined vector peak-to-peak (conservative: sqrt of summed squared per-axis p2p)
        p2p = math.sqrt(sum(v * v for v in peak_to_peak_per_axis))
        ratio_pct = (p2p / rest_length) * 100.0 if rest_length > 1e-9 else float("inf")
        passed = ratio_pct < LOCATION_LEAK_THRESHOLD_PCT
        results.append(
            {
                "bone": bone_name,
                "peak_to_peak": round(p2p, 6),
                "rest_length": round(rest_length, 6),
                "ratio_pct": round(ratio_pct, 4),
                "passed": passed,
            }
        )
        if ratio_pct > worst_ratio_pct:
            worst_ratio_pct = ratio_pct
            worst_bone = bone_name
        if not passed:
            raise RuntimeError(
                f"{bone_name}: location F-curve peak-to-peak {p2p:.6f} is "
                f"{ratio_pct:.3f}% of root-scale-normalized rest length "
                f"{rest_length:.6f} -- exceeds {LOCATION_LEAK_THRESHOLD_PCT}% threshold. "
                "Treating as a retargeting-setup bug."
            )

    zero_location_fcurves = len(per_bone_location_fcurves) == 0
    summary = {
        "zero_location_fcurves": zero_location_fcurves,
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

    arm_obj = bpy.data.objects.get(ARMATURE_NAME)
    if arm_obj is None or arm_obj.type != "ARMATURE":
        raise RuntimeError(f"{ARMATURE_NAME} not found or not an ARMATURE object")

    loc = tuple(round(v, 6) for v in arm_obj.location)
    scale = tuple(round(v, 6) for v in arm_obj.scale)
    if loc != (0.0, 0.0, 0.0):
        raise RuntimeError(f"{ARMATURE_NAME}: root location is not identity: {loc}")
    if not (
        math.isclose(scale[0], scale[1], abs_tol=1e-6)
        and math.isclose(scale[1], scale[2], abs_tol=1e-6)
    ):
        raise RuntimeError(f"{ARMATURE_NAME}: root scale is non-uniform: {scale}")
    obj_scale = scale[0]

    bone_lengths = {b.name: b.length for b in arm_obj.data.bones}

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")

    # rotation_mode must be XYZ Euler BEFORE probing -- detect_sign() writes
    # rotation_euler, which is a no-op on pose evaluation while the bone's
    # active rotation_mode is still the default QUATERNION.
    for bone_name in ALL_ANIMATED_BONES:
        arm_obj.pose.bones[bone_name].rotation_mode = "XYZ"

    print("=== Empirical sign detection (5 deg probe per limb bone) ===")
    signs = build_sign_table(arm_obj)
    for name, sign in signs.items():
        print(f"  {name:16s} sign={sign:+.1f}")

    print("=== Authoring source walk-cycle keyframes (rotation-only) ===")
    author_source_action(arm_obj, signs)

    bpy.ops.object.mode_set(mode="OBJECT")

    print("=== Baking (Bake Action, channel_types={'ROTATION'} explicit) ===")
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
