"""
Independent re-derivation of the "Phase 7" F-curve/animation audit --
against the EXPORTED GLB's actual animation channels, parsed directly from
the binary container (glb_json_parser.py), not against the .blend's
in-Blender F-curves and not by re-importing into Blender (a genuinely
different code path from both the builder's Blender-side bake-verification
AND this same session's Blender-side gates -- this is the "what would a
real GLTFLoader in a browser actually see" check, matching one of the 4
independent methods bug-214's verifier used).

Locked expectations this audit checks against (traced to source, not
invented):
  - `renders/3d/girl-love-hurts/bake_walk_retarget.py` asserts, against the
    SAVED .blend, that the baked action has 0 location F-curves and that
    only 10 named limb bones (LeftArm, RightArm, LeftForeArm, RightForeArm,
    LeftUpLeg, RightUpLeg, LeftLeg, RightLeg, LeftFoot, RightFoot) carry
    real rotation variation -- the other 14 bones (Hips, Spine02, Spine01,
    Spine, neck, Head, head_end, headfront, LeftShoulder, RightShoulder,
    LeftHand, RightHand, LeftToeBase, RightToeBase) are rotationally static
    (confirmed empirically this session via fresh bpy introspection of the
    saved .blend: max peak-to-peak == 0.0 for all 14, nonzero for all 10).
    This module re-verifies BOTH claims against the export, independently.
  - glTF joint nodes routinely carry translation/rotation/scale animation
    channels for EVERY joint regardless of whether that joint's pose
    actually changes (Blender's exporter bakes full TRS tracks per joint
    when export_optimize_animation_keep_anim_armature=True) -- so "a
    channel exists" is NOT evidence of real motion. The only valid test is
    whether the channel's SAMPLED VALUES vary over time. A naive
    flatten-and-take-range check across X/Y/Z conflates "spread across
    axes" with "variation across time" and was caught + rejected as buggy
    during this verification session before it reached the gate below.

Run standalone (no Blender needed):
    python3 gate_animation_audit.py
"""

import json
import math

from glb_json_parser import read_accessor, read_glb

GLB_PATH = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/"
    "renders/3d/girl-love-hurts/love-hurts-girl-v1.glb"
)

EXPECTED_ANIMATED_BONES = {
    "LeftArm",
    "RightArm",
    "LeftForeArm",
    "RightForeArm",
    "LeftUpLeg",
    "RightUpLeg",
    "LeftLeg",
    "RightLeg",
    "LeftFoot",
    "RightFoot",
}
EXPECTED_STATIC_BONES = {
    "Hips",
    "Spine02",
    "Spine01",
    "Spine",
    "neck",
    "Head",
    "head_end",
    "headfront",
    "LeftShoulder",
    "RightShoulder",
    "LeftHand",
    "RightHand",
    "LeftToeBase",
    "RightToeBase",
}
ALL_24_BONES = EXPECTED_ANIMATED_BONES | EXPECTED_STATIC_BONES
assert len(ALL_24_BONES) == 24

TRANSLATION_CONSTANT_TOL_M = 1e-5  # meters, per-component, across all keyframes
SCALE_CONSTANT_TOL = 1e-5
SCALE_IDENTITY_TOL = 1e-4
ROTATION_STATIC_TOL_DEG = 0.05  # max allowed quaternion drift for a "static" bone
ROTATION_ANIMATED_MIN_DEG = 1.0  # min required quaternion swing for an "animated" bone
QUAT_NORMALIZED_TOL = 1e-3


def quat_angle_deg(q1, q2):
    """Angle (deg) between two unit quaternions (x,y,z,w order, glTF convention)."""
    dot = sum(a * b for a, b in zip(q1, q2, strict=True))
    dot = max(-1.0, min(1.0, abs(dot)))  # abs: q and -q represent the same rotation
    return math.degrees(2.0 * math.acos(dot))


def quat_length(q):
    return math.sqrt(sum(c * c for c in q))


def channel_series(gltf, bin_chunk, anim, node_idx, path):
    """Find the channel for (node_idx, path) in `anim` and return (times, values)."""
    for ch in anim["channels"]:
        if ch["target"]["node"] == node_idx and ch["target"]["path"] == path:
            sampler = anim["samplers"][ch["sampler"]]
            times = [t[0] for t in read_accessor(gltf, bin_chunk, sampler["input"])]
            values = read_accessor(gltf, bin_chunk, sampler["output"])
            return times, values, sampler.get("interpolation", "LINEAR")
    return None, None, None


def max_component_deviation(values):
    """Max |component - component[0]| across all keyframes, per-axis-aware (NOT the
    buggy flatten-and-range check: this compares each keyframe to keyframe 0 on
    matching axes, so a channel that is genuinely constant over time reports 0
    even though its X/Y/Z components differ wildly from each other)."""
    if not values:
        return 0.0
    base = values[0]
    max_dev = 0.0
    for v in values:
        for a, b in zip(v, base, strict=True):
            max_dev = max(max_dev, abs(a - b))
    return max_dev


def audit_animation(gltf, bin_chunk, anim, node_index_by_bone):
    anim_name = anim.get("name", "<unnamed>")
    per_bone = {}
    location_leak_bones = []
    scale_leak_bones = []
    static_bones_that_moved = []
    animated_bones_that_are_static = []
    non_normalized_quats = 0
    nan_or_inf_found = []

    for bone, node_idx in node_index_by_bone.items():
        t_times, t_vals, _ = channel_series(gltf, bin_chunk, anim, node_idx, "translation")
        r_times, r_vals, _ = channel_series(gltf, bin_chunk, anim, node_idx, "rotation")
        s_times, s_vals, _ = channel_series(gltf, bin_chunk, anim, node_idx, "scale")

        translation_dev = max_component_deviation(t_vals) if t_vals else 0.0
        scale_dev = max_component_deviation(s_vals) if s_vals else 0.0

        rotation_ptp_deg = 0.0
        if r_vals:
            base_q = r_vals[0]
            for q in r_vals:
                ql = quat_length(q)
                if not all(math.isfinite(c) for c in q):
                    nan_or_inf_found.append((bone, "rotation", q))
                elif abs(ql - 1.0) > QUAT_NORMALIZED_TOL:
                    non_normalized_quats += 1
                rotation_ptp_deg = max(rotation_ptp_deg, quat_angle_deg(base_q, q))

        if translation_dev > TRANSLATION_CONSTANT_TOL_M:
            location_leak_bones.append((bone, translation_dev))

        if s_vals:
            # identity check against the FIRST sample (constancy already checked via scale_dev)
            first_scale = s_vals[0]
            if any(abs(c - 1.0) > SCALE_IDENTITY_TOL for c in first_scale):
                scale_leak_bones.append((bone, first_scale))
        if scale_dev > SCALE_CONSTANT_TOL:
            scale_leak_bones.append((bone, ("time-varying", scale_dev)))

        if bone in EXPECTED_STATIC_BONES and rotation_ptp_deg > ROTATION_STATIC_TOL_DEG:
            static_bones_that_moved.append((bone, rotation_ptp_deg))
        if bone in EXPECTED_ANIMATED_BONES and rotation_ptp_deg < ROTATION_ANIMATED_MIN_DEG:
            animated_bones_that_are_static.append((bone, rotation_ptp_deg))

        per_bone[bone] = {
            "translation_time_deviation_m": translation_dev,
            "scale_time_deviation": scale_dev,
            "rotation_ptp_deg": round(rotation_ptp_deg, 4),
            "n_translation_keys": len(t_vals) if t_vals else 0,
            "n_rotation_keys": len(r_vals) if r_vals else 0,
        }

    gate_passed = (
        len(location_leak_bones) == 0
        and len(scale_leak_bones) == 0
        and len(static_bones_that_moved) == 0
        and len(animated_bones_that_are_static) == 0
        and len(nan_or_inf_found) == 0
        and non_normalized_quats == 0
    )

    return {
        "animation_name": anim_name,
        "per_bone": per_bone,
        "location_leak_bones": location_leak_bones,
        "scale_leak_bones": scale_leak_bones,
        "static_bones_that_moved_deg": static_bones_that_moved,
        "animated_bones_that_are_static_deg": animated_bones_that_are_static,
        "nan_or_inf_found": nan_or_inf_found,
        "non_normalized_quat_samples": non_normalized_quats,
        "gate_passed": gate_passed,
    }


def audit_skin(gltf, bin_chunk):
    skins = gltf.get("skins", [])
    if len(skins) != 1:
        return {"ok": False, "reason": f"expected exactly 1 skin, found {len(skins)}"}
    skin = skins[0]
    joints = skin["joints"]
    if len(joints) != 24:
        return {"ok": False, "reason": f"expected 24 joints, found {len(joints)}"}
    ibm = read_accessor(gltf, bin_chunk, skin["inverseBindMatrices"])
    if len(ibm) != 24:
        return {"ok": False, "reason": f"inverseBindMatrices count {len(ibm)} != 24 joints"}
    non_finite = [i for i, m in enumerate(ibm) if not all(math.isfinite(c) for c in m)]
    return {
        "ok": len(non_finite) == 0,
        "n_joints": len(joints),
        "n_inverse_bind_matrices": len(ibm),
        "non_finite_matrices": non_finite,
    }


def audit_mesh_skinning(gltf, bin_chunk):
    mesh = gltf["meshes"][0]
    prim = mesh["primitives"][0]
    attrs = prim["attributes"]
    required = {"POSITION", "JOINTS_0", "WEIGHTS_0"}
    missing = required - set(attrs)
    if missing:
        return {"ok": False, "reason": f"missing attributes: {missing}"}

    weights = read_accessor(gltf, bin_chunk, attrs["WEIGHTS_0"])
    n = len(weights)
    sample_idx = list(range(0, n, max(1, n // 500)))  # ~500-point sample, not all 47k
    bad_sum = []
    for i in sample_idx:
        w = weights[i]
        s = sum(w)
        if abs(s - 1.0) > 1e-3:
            bad_sum.append((i, s))

    return {
        "ok": len(bad_sum) == 0,
        "n_verts": n,
        "sampled": len(sample_idx),
        "weight_sum_failures": bad_sum[:20],
        "weight_sum_failures_total": len(bad_sum),
    }


def main():
    gltf, bin_chunk = read_glb(GLB_PATH)

    node_index_by_bone = {}
    for i, n in enumerate(gltf["nodes"]):
        name = n.get("name")
        if name in ALL_24_BONES:
            node_index_by_bone[name] = i
    missing_bones = ALL_24_BONES - set(node_index_by_bone)
    if missing_bones:
        raise RuntimeError(f"exported GLB missing expected bone nodes: {missing_bones}")

    animations = gltf.get("animations", [])
    print(f"exported animations: {[a.get('name') for a in animations]}")
    if len(animations) == 0:
        raise RuntimeError("exported GLB has 0 animations -- expected >=1 (GirlWalk_Baked)")

    baked = next((a for a in animations if a.get("name") == "GirlWalk_Baked"), None)
    if baked is None:
        raise RuntimeError(
            f"exported GLB has no animation named 'GirlWalk_Baked' -- found {[a.get('name') for a in animations]}"
        )

    result = audit_animation(gltf, bin_chunk, baked, node_index_by_bone)
    result["skin"] = audit_skin(gltf, bin_chunk)
    result["mesh_skinning"] = audit_mesh_skinning(gltf, bin_chunk)
    result["extra_animations_present"] = [
        a.get("name") for a in animations if a.get("name") != "GirlWalk_Baked"
    ]

    result["gate_passed"] = (
        result["gate_passed"] and result["skin"]["ok"] and result["mesh_skinning"]["ok"]
    )

    print("")
    print("=" * 78)
    print("GATE D -- ANIMATION / F-CURVE AUDIT (exported GLB, raw JSON parse)")
    print("=" * 78)
    print(f"animation under test: {result['animation_name']}")
    for bone in sorted(per_bone := result["per_bone"]):
        d = per_bone[bone]
        cat = "ANIMATED" if bone in EXPECTED_ANIMATED_BONES else "static"
        print(
            f"  {bone:16s} [{cat:8s}] rot_ptp={d['rotation_ptp_deg']:7.3f} deg  "
            f"trans_dev={d['translation_time_deviation_m']:.2e} m  "
            f"scale_dev={d['scale_time_deviation']:.2e}"
        )
    print("-" * 78)
    print(f"location_leak_bones (translation genuinely varies): {result['location_leak_bones']}")
    print(f"scale_leak_bones (non-identity or time-varying scale): {result['scale_leak_bones']}")
    print(
        f"static_bones_that_moved (>{ROTATION_STATIC_TOL_DEG} deg): {result['static_bones_that_moved_deg']}"
    )
    print(
        f"animated_bones_that_are_static (<{ROTATION_ANIMATED_MIN_DEG} deg): "
        f"{result['animated_bones_that_are_static_deg']}"
    )
    print(f"nan_or_inf_found: {result['nan_or_inf_found']}")
    print(f"non_normalized_quat_samples: {result['non_normalized_quat_samples']}")
    print(f"skin audit: {result['skin']}")
    print(f"mesh skinning audit: {result['mesh_skinning']}")
    print(f"extra (unexpected) animations present in file: {result['extra_animations_present']}")
    print(f"GATE_D_PASSED: {result['gate_passed']}")
    print("=" * 78)
    print("GATE_D_RESULT_JSON:" + json.dumps(result, default=str))
    return result


if __name__ == "__main__":
    main()
