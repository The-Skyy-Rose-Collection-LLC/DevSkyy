"""WS3b — 25-joint mixamorig skeleton builder.

Ports rig_girl.py's joint table, parameterized on the `Landmarks` auto-detected
in WS3a instead of inline hardcoded numbers. Every joint offset that doesn't
sit directly on a detected landmark is expressed as a FRACTION of a real
anatomical span (torso span = neck_y-crotch_y, leg span = crotch_y, or overall
height) derived from the reference model's validated absolute-meter offsets —
so a differently-proportioned character (e.g. a child-proportioned mascot)
gets joints scaled to its own measurements, not Love Hurts Girl's.

Bind pose stays the model's natural relaxed pose — never symmetrized, never
T-pose-baked (spec section 2, "the Skyy lesson: likeness preservation over
geometric perfection").
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .landmarks import Landmarks

JOINT_NAMES = [
    "mixamorig:Hips",
    "mixamorig:Spine",
    "mixamorig:Spine1",
    "mixamorig:Spine2",
    "mixamorig:Neck",
    "mixamorig:Head",
    "mixamorig:HeadTop_End",
    "mixamorig:LeftShoulder",
    "mixamorig:LeftArm",
    "mixamorig:LeftForeArm",
    "mixamorig:LeftHand",
    "mixamorig:RightShoulder",
    "mixamorig:RightArm",
    "mixamorig:RightForeArm",
    "mixamorig:RightHand",
    "mixamorig:LeftUpLeg",
    "mixamorig:LeftLeg",
    "mixamorig:LeftFoot",
    "mixamorig:LeftToeBase",
    "mixamorig:LeftToe_End",
    "mixamorig:RightUpLeg",
    "mixamorig:RightLeg",
    "mixamorig:RightFoot",
    "mixamorig:RightToeBase",
    "mixamorig:RightToe_End",
]
# Hips=-1(root); Spine chain 0..3; Head chain 4..6; arms hang off Spine2(3);
# legs hang off Hips(0). Matches rig_girl.py's validated parent-index table.
JOINT_PARENTS = [
    -1,
    0,
    1,
    2,
    3,
    4,
    5,
    3,
    7,
    8,
    9,
    3,
    11,
    12,
    13,
    0,
    15,
    16,
    17,
    18,
    0,
    20,
    21,
    22,
    23,
]
NUM_JOINTS = len(JOINT_NAMES)

# ---- offset fractions derived from rig_girl.py's validated absolute meters -
# (offset_meters / reference_span_meters), reference model: crotch_y=0.64,
# neck_y=1.28, height=1.911, torso_span=neck_y-crotch_y=0.64.
_SPINE_FRAC = (0.25, 0.4844, 0.7188)  # Spine, Spine1, Spine2 above crotch_y, frac of torso_span
_HEAD_FRAC = 0.1587  # Head above neck_y, frac of (height - neck_y)
_STUB_Y_FRAC = (
    0.0625  # LeftShoulder below neck_y (frac torso_span) & LeftUpLeg below crotch_y (frac crotch_y)
)
_SHOULDER_STUB_X_FRAC = (
    0.35  # LeftShoulder.x as a fraction of the detected LeftArm.x (proportional heuristic)
)
_LEG_Y_FRAC = 0.5156  # LeftLeg.y, frac of crotch_y
_FOOT_Y_FRAC = 0.1406  # LeftFoot.y, frac of crotch_y
_TOEBASE_Y_FRAC = 0.0469  # LeftToeBase.y, frac of crotch_y
_TOEEND_Y_FRAC = 0.0313  # LeftToe_End.y, frac of crotch_y
_HIP_X_FRAC = 0.0471  # LeftUpLeg.x, frac of height
_LEG_X_FRAC = 0.0523  # LeftLeg.x, frac of height
_FOOT_X_FRAC = 0.0576  # LeftFoot.x, frac of height
_TOEBASE_X_FRAC = 0.0680  # LeftToeBase.x, frac of height
_TOEEND_X_FRAC = 0.0733  # LeftToe_End.x, frac of height
_LEG_Z_OFFSET_FRAC = -0.00523  # LeftLeg.z relative to z_hip, frac of height
_FOOT_Z_OFFSET_FRAC = -0.01047  # LeftFoot.z relative to z_hip, frac of height
_TOEBASE_Z_OFFSET_FRAC = 0.03140  # LeftToeBase.z relative to z_foot, frac of height
_TOEEND_Z_OFFSET_FRAC = 0.07326  # LeftToe_End.z relative to z_foot, frac of height


@dataclass
class Skeleton:
    names: list[str]
    parents: list[int]
    positions: np.ndarray  # (25, 3) world-space bind positions


def build_skeleton(lm: Landmarks) -> Skeleton:
    """WS3b: builds the 25-joint mixamorig skeleton from auto-detected landmarks."""
    height = lm.height
    torso_span = lm.neck_y - lm.crotch_y
    leg_span = lm.crotch_y
    xl, yl, zl = (float(v) for v in lm.shoulder_l)
    xr, yr, zr = (float(v) for v in lm.shoulder_r)
    hxl, hyl, hzl = (float(v) for v in lm.hand_l)
    hxr, hyr, hzr = (float(v) for v in lm.hand_r)
    elbow_l = ((xl + hxl) / 2 + 0.01, (yl + hyl) / 2, (lm.z_chest + hzl) / 2)
    elbow_r = ((xr + hxr) / 2 - 0.01, (yr + hyr) / 2, (lm.z_chest + hzr) / 2)

    spine_y, spine1_y, spine2_y = (lm.crotch_y + f * torso_span for f in _SPINE_FRAC)
    head_y = lm.neck_y + _HEAD_FRAC * (height - lm.neck_y)
    shoulder_stub_y = lm.neck_y - _STUB_Y_FRAC * torso_span
    upleg_stub_y = lm.crotch_y - _STUB_Y_FRAC * leg_span

    positions = np.array(
        [
            (0.0, lm.crotch_y, lm.z_hip),  # 0 Hips
            (0.0, spine_y, lm.z_hip),  # 1 Spine
            (0.0, spine1_y, (lm.z_hip + lm.z_chest) / 2),  # 2 Spine1
            (0.0, spine2_y, lm.z_chest),  # 3 Spine2
            (0.0, lm.neck_y, lm.z_chest),  # 4 Neck
            (0.0, head_y, lm.z_head),  # 5 Head
            (0.0, height, lm.z_head),  # 6 HeadTop_End
            (_SHOULDER_STUB_X_FRAC * xl, shoulder_stub_y, lm.z_chest),  # 7 LeftShoulder
            (xl, yl, zl),  # 8 LeftArm
            elbow_l,  # 9 LeftForeArm
            (hxl, hyl + 0.06 * height / 1.911, hzl),  # 10 LeftHand
            (_SHOULDER_STUB_X_FRAC * xr, shoulder_stub_y, lm.z_chest),  # 11 RightShoulder
            (xr, yr, zr),  # 12 RightArm
            elbow_r,  # 13 RightForeArm
            (hxr, hyr + 0.06 * height / 1.911, hzr),  # 14 RightHand
            (_HIP_X_FRAC * height, upleg_stub_y, lm.z_hip),  # 15 LeftUpLeg
            (
                _LEG_X_FRAC * height,
                _LEG_Y_FRAC * leg_span,
                lm.z_hip + _LEG_Z_OFFSET_FRAC * height,
            ),  # 16 LeftLeg
            (
                _FOOT_X_FRAC * height,
                _FOOT_Y_FRAC * leg_span,
                lm.z_hip + _FOOT_Z_OFFSET_FRAC * height,
            ),  # 17 LeftFoot
            (
                _TOEBASE_X_FRAC * height,
                _TOEBASE_Y_FRAC * leg_span,
                float(lm.z_foot_l[2]) + _TOEBASE_Z_OFFSET_FRAC * height,
            ),  # 18 LeftToeBase
            (
                _TOEEND_X_FRAC * height,
                _TOEEND_Y_FRAC * leg_span,
                float(lm.z_foot_l[2]) + _TOEEND_Z_OFFSET_FRAC * height,
            ),  # 19 LeftToe_End
            (-_HIP_X_FRAC * height, upleg_stub_y, lm.z_hip),  # 20 RightUpLeg
            (
                -_LEG_X_FRAC * height,
                _LEG_Y_FRAC * leg_span,
                lm.z_hip + _LEG_Z_OFFSET_FRAC * height,
            ),  # 21 RightLeg
            (
                -_FOOT_X_FRAC * height,
                _FOOT_Y_FRAC * leg_span,
                lm.z_hip + _FOOT_Z_OFFSET_FRAC * height,
            ),  # 22 RightFoot
            (
                -_TOEBASE_X_FRAC * height,
                _TOEBASE_Y_FRAC * leg_span,
                float(lm.z_foot_r[2]) + _TOEBASE_Z_OFFSET_FRAC * height,
            ),  # 23 RightToeBase
            (
                -_TOEEND_X_FRAC * height,
                _TOEEND_Y_FRAC * leg_span,
                float(lm.z_foot_r[2]) + _TOEEND_Z_OFFSET_FRAC * height,
            ),  # 24 RightToe_End
        ],
        dtype=np.float64,
    )
    return Skeleton(names=JOINT_NAMES, parents=JOINT_PARENTS, positions=positions)
