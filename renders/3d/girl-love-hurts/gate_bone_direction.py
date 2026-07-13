"""
Retargeting-compatibility gate -- BEFORE any skin weighting.

For every corresponding bone pair between the Love Hurts girl rig and the
skyy.glb mascot rig (both root-scale-normalized to 1.0, both at their own
rest pose, both root world transform = identity), compute the world-space
head-to-tail unit-vector angle (arccos of the dot product, in degrees) and
check it against a per-bone-category threshold:

    10 deg max -- UpperArm / ForeArm / UpLeg / Leg / Spine-chain / neck-Head
    20 deg max -- Shoulder / Foot / ToeBase / Hand

`head_end` and `headfront` are NOT named in the locked threshold spec (they
are auxiliary head-volume bones present in this 24-bone rig, not part of the
standard Mixamo-style chain the thresholds were written for). They are still
computed and reported, defaulted to the lenient 20 deg tier (same tier as
other leaf/effector bones: Hand/Foot/ToeBase) and explicitly flagged as an
inferred threshold in the report -- they do NOT count toward
`any_critical_bone_failed`.

Any bone exceeding its threshold fails the gate FOR THAT BONE ONLY, not the
whole rig -- failing bones are recorded individually.

Run:
    blender -b --factory-startup -P gate_bone_direction.py
"""

import json
import math

import bpy
from mathutils import Vector

GIRL_BLEND = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/"
    "renders/3d/girl-love-hurts/love-hurts-girl-rig.blend"
)
MASCOT_GLB = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/"
    "wordpress-theme/skyyrose-flagship/assets/models/skyy.glb"
)

# Canonical 24-bone hierarchy shared by both rigs (build_girl_rig.py clones
# this exact set from skyy.glb -- verified this session via bpy dump of both
# files: identical 24 names, identical parent map).
EXPECTED_BONES = {
    "Hips",
    "LeftUpLeg",
    "LeftLeg",
    "LeftFoot",
    "LeftToeBase",
    "RightUpLeg",
    "RightLeg",
    "RightFoot",
    "RightToeBase",
    "Spine02",
    "Spine01",
    "Spine",
    "LeftShoulder",
    "LeftArm",
    "LeftForeArm",
    "LeftHand",
    "RightShoulder",
    "RightArm",
    "RightForeArm",
    "RightHand",
    "neck",
    "Head",
    "head_end",
    "headfront",
}

# Print order (chain-grouped, readable table).
BONE_ORDER = [
    "Hips",
    "Spine02",
    "Spine01",
    "Spine",
    "neck",
    "Head",
    "head_end",
    "headfront",
    "LeftShoulder",
    "LeftArm",
    "LeftForeArm",
    "LeftHand",
    "RightShoulder",
    "RightArm",
    "RightForeArm",
    "RightHand",
    "LeftUpLeg",
    "LeftLeg",
    "LeftFoot",
    "LeftToeBase",
    "RightUpLeg",
    "RightLeg",
    "RightFoot",
    "RightToeBase",
]
assert set(BONE_ORDER) == EXPECTED_BONES

CATEGORY_THRESHOLD_DEG = {
    "spine_chain": 10.0,  # Hips, Spine02, Spine01, Spine
    "neck_head": 10.0,  # neck, Head
    "upper_arm": 10.0,  # LeftArm, RightArm
    "forearm": 10.0,  # LeftForeArm, RightForeArm
    "upleg": 10.0,  # LeftUpLeg, RightUpLeg
    "leg": 10.0,  # LeftLeg, RightLeg
    "shoulder": 20.0,  # LeftShoulder, RightShoulder
    "foot": 20.0,  # LeftFoot, RightFoot
    "toebase": 20.0,  # LeftToeBase, RightToeBase
    "hand": 20.0,  # LeftHand, RightHand
    "unlisted_head_aux": 20.0,  # head_end, headfront -- inferred, see module docstring
}

BONE_CATEGORY = {
    "Hips": "spine_chain",
    "Spine02": "spine_chain",
    "Spine01": "spine_chain",
    "Spine": "spine_chain",
    "neck": "neck_head",
    "Head": "neck_head",
    "head_end": "unlisted_head_aux",
    "headfront": "unlisted_head_aux",
    "LeftArm": "upper_arm",
    "RightArm": "upper_arm",
    "LeftForeArm": "forearm",
    "RightForeArm": "forearm",
    "LeftUpLeg": "upleg",
    "RightUpLeg": "upleg",
    "LeftLeg": "leg",
    "RightLeg": "leg",
    "LeftShoulder": "shoulder",
    "RightShoulder": "shoulder",
    "LeftFoot": "foot",
    "RightFoot": "foot",
    "LeftToeBase": "toebase",
    "RightToeBase": "toebase",
    "LeftHand": "hand",
    "RightHand": "hand",
}
assert set(BONE_CATEGORY) == EXPECTED_BONES

# Categories whose threshold comes from the locked spec (not inferred) --
# these are the only ones that can trip `any_critical_bone_failed`.
CRITICAL_CATEGORIES = {
    "spine_chain",
    "neck_head",
    "upper_arm",
    "forearm",
    "upleg",
    "leg",
}


def _round_tuple(vals, n=6):
    return tuple(round(float(v), n) for v in vals)


def normalize_root_to_identity(obj):
    """Verify + enforce: root location/rotation = identity, root scale
    normalized to 1.0. Raises loudly if location or rotation is not already
    identity (that would be a genuine cross-rig alignment defect, not a
    scale artifact to paper over). Only uniform scale is silently
    normalized to 1.0 -- direction (unit head->tail vector) is invariant
    under uniform scale, so this cannot mask a real orientation mismatch.
    """
    loc = _round_tuple(obj.location)
    if loc != (0.0, 0.0, 0.0):
        raise RuntimeError(f"{obj.name}: root location is not identity: {loc}")

    if obj.rotation_mode == "QUATERNION":
        rot = _round_tuple(obj.rotation_quaternion)
        if rot != (1.0, 0.0, 0.0, 0.0):
            raise RuntimeError(f"{obj.name}: root rotation (quat) is not identity: {rot}")
    elif obj.rotation_mode == "AXIS_ANGLE":
        raise RuntimeError(
            f"{obj.name}: unexpected AXIS_ANGLE rotation_mode, cannot verify identity"
        )
    else:
        rot = _round_tuple(obj.rotation_euler)
        if rot != (0.0, 0.0, 0.0):
            raise RuntimeError(f"{obj.name}: root rotation (euler) is not identity: {rot}")

    sx, sy, sz = obj.scale
    if not (
        math.isclose(sx, sy, rel_tol=1e-4, abs_tol=1e-6)
        and math.isclose(sy, sz, rel_tol=1e-4, abs_tol=1e-6)
    ):
        raise RuntimeError(
            f"{obj.name}: root scale is non-uniform, refusing to normalize: {tuple(obj.scale)}"
        )
    if sx <= 0:
        raise RuntimeError(f"{obj.name}: root scale is non-positive: {tuple(obj.scale)}")

    obj.scale = (1.0, 1.0, 1.0)


def find_new_armature(names_before):
    candidates = [
        o for o in bpy.data.objects if o.type == "ARMATURE" and o.name not in names_before
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"expected exactly 1 new ARMATURE object after mascot import, found {len(candidates)}: "
            f"{[c.name for c in candidates]}"
        )
    return candidates[0]


def bone_unit_directions(arm_obj):
    """rest-pose, root-transform-normalized edit bones -> {name: unit Vector}.

    With the root object transform normalized to identity (see
    normalize_root_to_identity), EditBone.head/.tail are directly in world
    space (verified against build_girl_rig.py, which assigns world-space
    mesh landmark coordinates straight into eb.head/eb.tail with the
    armature object's transform held at identity).
    """
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    out = {}
    try:
        for eb in arm_obj.data.edit_bones:
            direction = eb.tail - eb.head
            if direction.length < 1e-9:
                raise RuntimeError(
                    f"{arm_obj.name}.{eb.name}: zero-length bone, cannot compute direction"
                )
            out[eb.name] = direction.normalized()
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
    return out


def angle_deg(v1: Vector, v2: Vector) -> float:
    dot = max(-1.0, min(1.0, v1.dot(v2)))
    return math.degrees(math.acos(dot))


def main():
    # --- load girl rig, read rest-pose bone directions ---
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=GIRL_BLEND)

    girl_arm = next(
        (o for o in bpy.data.objects if o.type == "ARMATURE" and o.name == "GirlArmature"), None
    )
    if girl_arm is None:
        raise RuntimeError("GirlArmature object not found in love-hurts-girl-rig.blend")
    normalize_root_to_identity(girl_arm)
    girl_dirs = bone_unit_directions(girl_arm)

    # --- import mascot rig into the SAME session, read rest-pose bone directions ---
    names_before = set(o.name for o in bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=MASCOT_GLB)
    mascot_arm = find_new_armature(names_before)
    normalize_root_to_identity(mascot_arm)
    mascot_dirs = bone_unit_directions(mascot_arm)

    # --- bone-name census (fail loud, not silent, on any mismatch) ---
    girl_names = set(girl_dirs)
    mascot_names = set(mascot_dirs)
    missing_in_mascot = girl_names - mascot_names
    missing_in_girl = mascot_names - girl_names
    if girl_names != EXPECTED_BONES:
        raise RuntimeError(
            f"girl rig bone set != expected 24: extra={girl_names - EXPECTED_BONES} missing={EXPECTED_BONES - girl_names}"
        )
    if missing_in_mascot or missing_in_girl:
        raise RuntimeError(
            f"bone-pair census failed -- missing_in_mascot={sorted(missing_in_mascot)} "
            f"missing_in_girl={sorted(missing_in_girl)}"
        )

    # --- per-bone-pair angle + threshold check ---
    results = []
    for name in BONE_ORDER:
        category = BONE_CATEGORY[name]
        threshold = CATEGORY_THRESHOLD_DEG[category]
        angle = angle_deg(girl_dirs[name], mascot_dirs[name])
        passed = angle <= threshold
        results.append(
            {
                "bone": name,
                "category": category,
                "angle_deg": round(angle, 3),
                "threshold_deg": threshold,
                "passed": passed,
                "critical": category in CRITICAL_CATEGORIES,
                "threshold_inferred": category == "unlisted_head_aux",
            }
        )

    failing = [r for r in results if not r["passed"]]
    any_critical_failed = any(r["critical"] and not r["passed"] for r in results)
    gate_passed = len(failing) == 0

    # --- human-readable table ---
    print("")
    print("=" * 78)
    print("RETARGETING-COMPATIBILITY GATE -- girl rig vs skyy.glb mascot rig")
    print("(rest pose, root scale normalized to 1.0, root world transform = identity)")
    print("=" * 78)
    header = f"{'bone':<16}{'category':<16}{'angle(deg)':>12}{'thresh(deg)':>13}{'result':>10}"
    print(header)
    print("-" * len(header))
    for r in results:
        flag = " *inferred*" if r["threshold_inferred"] else ""
        status = "PASS" if r["passed"] else "FAIL"
        print(
            f"{r['bone']:<16}{r['category']:<16}{r['angle_deg']:>12.3f}{r['threshold_deg']:>13.1f}{status:>10}{flag}"
        )
    print("-" * len(header))
    print(
        f"Bones failing gate ({len(failing)}): {[r['bone'] for r in failing] if failing else 'none'}"
    )
    print(f"Any CRITICAL-category bone failed: {any_critical_failed}")
    print(f"Overall gate_passed (0 bones failing): {gate_passed}")
    print("=" * 78)

    summary = {
        "gate_passed": gate_passed,
        "any_critical_bone_failed": any_critical_failed,
        "failing_bones": [r["bone"] for r in failing],
        "per_bone": results,
    }
    print("GATE_RESULT_JSON:" + json.dumps(summary))


if __name__ == "__main__":
    main()
