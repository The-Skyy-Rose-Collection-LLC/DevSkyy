"""Retargeting-compatibility gate -- BEFORE any skin weighting or constraint setup.

Generalized, path-parameterized adaptation of the real, already-executed
`renders/3d/girl-love-hurts/gate_bone_direction.py` (bug-195's precedent: 15/24
bones failed comparing the Love Hurts Girl rig against skyy.glb, including
Hips 97.4 deg and LeftForeArm 126.2 deg). Same bone-category thresholds, same
math -- generalized to take two rig file paths as arguments instead of two
hardcoded ones, so a future character can be gated without editing this file.

For every corresponding bone pair between rig A (opened as the main .blend
file) and rig B (imported into the same session as a .glb), compute the
world-space head-to-tail unit-vector angle (arccos of the dot product, in
degrees) and check it against a per-bone-category threshold:

    10 deg max -- UpperArm / ForeArm / UpLeg / Leg / Spine-chain / neck-Head
    20 deg max -- Shoulder / Foot / ToeBase / Hand
    20 deg max, INFERRED -- head_end / headfront (auxiliary head-volume bones,
        not part of the standard chain the thresholds were written for; still
        computed and reported, never counted toward any_critical_bone_failed)

Any bone exceeding its threshold fails the gate FOR THAT BONE ONLY, not the
whole rig -- failing bones are recorded individually. A failed gate is a hard
stop for THIS rig pair (see reference/retargeting.md) -- it does not mean the
Local-Space Copy Rotation method is unsound in general.

Run:
    blender -b --factory-startup -P retarget_local_space_gate.py -- \\
        --rig-a /path/to/rig_a.blend --rig-a-armature ArmatureName \\
        --rig-b /path/to/rig_b.glb
"""

import json
import math
import sys

import bpy
from mathutils import Vector

# Canonical 24-bone hierarchy this project's characters share (verified
# against build_girl_rig.py and skyy.glb this session: identical 24 names,
# identical parent map). A rig using a different hierarchy needs a different
# EXPECTED_BONES/BONE_CATEGORY table -- this is a project convention, not a
# glTF/Blender universal, and generalizing past it is out of scope here.
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
    "spine_chain": 10.0,
    "neck_head": 10.0,
    "upper_arm": 10.0,
    "forearm": 10.0,
    "upleg": 10.0,
    "leg": 10.0,
    "shoulder": 20.0,
    "foot": 20.0,
    "toebase": 20.0,
    "hand": 20.0,
    "unlisted_head_aux": 20.0,
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

CRITICAL_CATEGORIES = {"spine_chain", "neck_head", "upper_arm", "forearm", "upleg", "leg"}


def _round_tuple(vals, n=6):
    return tuple(round(float(v), n) for v in vals)


def normalize_root_to_identity(obj):
    """Verify + enforce: root location/rotation = identity, root scale
    normalized to 1.0. Raises loudly if location or rotation is not already
    identity -- that would be a genuine cross-rig alignment defect, not a
    scale artifact to paper over."""
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


def find_armature(name=None, exclude_names=()):
    candidates = [
        o for o in bpy.data.objects if o.type == "ARMATURE" and o.name not in exclude_names
    ]
    if name:
        matches = [o for o in candidates if o.name == name]
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly 1 armature named {name!r}, found {len(matches)}")
        return matches[0]
    if len(candidates) != 1:
        raise RuntimeError(
            f"no --rig-*-armature given and found {len(candidates)} armature(s), not 1: "
            f"{[c.name for c in candidates]} -- pass the name explicitly"
        )
    return candidates[0]


def bone_unit_directions(arm_obj):
    """rest-pose, root-transform-normalized edit bones -> {name: unit Vector}."""
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


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    opts = {"rig_a": None, "rig_a_armature": None, "rig_b": None, "rig_b_armature": None}
    it = iter(argv)
    for arg in it:
        if arg == "--rig-a":
            opts["rig_a"] = next(it)
        elif arg == "--rig-a-armature":
            opts["rig_a_armature"] = next(it)
        elif arg == "--rig-b":
            opts["rig_b"] = next(it)
        elif arg == "--rig-b-armature":
            opts["rig_b_armature"] = next(it)
    if not opts["rig_a"] or not opts["rig_b"]:
        raise SystemExit(
            "usage: ... -- --rig-a <path.blend> [--rig-a-armature NAME] --rig-b <path.glb> [--rig-b-armature NAME]"
        )
    return opts


def main():
    opts = parse_args()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    if opts["rig_a"].endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=opts["rig_a"])
        rig_a_arm = find_armature(opts["rig_a_armature"])
    else:
        names_before = set(o.name for o in bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=opts["rig_a"])
        rig_a_arm = find_armature(opts["rig_a_armature"], exclude_names=names_before)
    normalize_root_to_identity(rig_a_arm)
    rig_a_dirs = bone_unit_directions(rig_a_arm)

    names_before = set(o.name for o in bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=opts["rig_b"])
    rig_b_arm = find_armature(opts["rig_b_armature"], exclude_names=names_before)
    normalize_root_to_identity(rig_b_arm)
    rig_b_dirs = bone_unit_directions(rig_b_arm)

    a_names, b_names = set(rig_a_dirs), set(rig_b_dirs)
    if a_names != EXPECTED_BONES:
        raise RuntimeError(
            f"rig A bone set != expected 24: extra={a_names - EXPECTED_BONES} missing={EXPECTED_BONES - a_names}"
        )
    if a_names != b_names:
        raise RuntimeError(
            f"bone-pair census failed -- missing_in_b={sorted(a_names - b_names)} missing_in_a={sorted(b_names - a_names)}"
        )

    results = []
    for name in BONE_ORDER:
        category = BONE_CATEGORY[name]
        threshold = CATEGORY_THRESHOLD_DEG[category]
        angle = angle_deg(rig_a_dirs[name], rig_b_dirs[name])
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

    print("")
    print("=" * 78)
    print(f"RETARGETING-COMPATIBILITY GATE -- {opts['rig_a']} vs {opts['rig_b']}")
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
