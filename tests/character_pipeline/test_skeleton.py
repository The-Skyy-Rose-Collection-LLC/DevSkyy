"""skeleton.py: joint count, topological ordering, and proportional placement.

The parent-index-less-than-child-index invariant (asserted here) is exactly
what verify.py's `_world_matrices` relies on for a single forward pass over
`range(nj)` — if this ever breaks, WS6's FK silently uses stale parent world
matrices instead of raising, so it's worth locking down directly.
"""

from __future__ import annotations

import numpy as np

from skyyrose.character_pipeline.landmarks import Landmarks
from skyyrose.character_pipeline.skeleton import (
    JOINT_NAMES,
    JOINT_PARENTS,
    NUM_JOINTS,
    build_skeleton,
)


def _synthetic_landmarks(height: float = 1.911) -> Landmarks:
    crotch_y, neck_y = 0.64 * (height / 1.911), 1.28 * (height / 1.911)
    return Landmarks(
        height=height,
        crotch_y=crotch_y,
        z_hip=0.05,
        z_chest=0.02,
        z_head=0.03,
        z_foot_l=np.array([0.11, 0.05, 0.10]),
        z_foot_r=np.array([-0.11, 0.05, 0.10]),
        shoulder_l=np.array([0.20, 1.24 * (height / 1.911), 0.02]),
        shoulder_r=np.array([-0.20, 1.24 * (height / 1.911), 0.02]),
        hand_l=np.array([0.25, 0.70 * (height / 1.911), -0.02]),
        hand_r=np.array([-0.25, 0.70 * (height / 1.911), -0.02]),
        neck_y=neck_y,
    )


def test_joint_tables_have_matching_length():
    assert len(JOINT_NAMES) == NUM_JOINTS == 25
    assert len(JOINT_PARENTS) == NUM_JOINTS


def test_every_parent_index_precedes_its_child():
    """build_skeleton's own FK-friendly invariant: verify.py computes world
    matrices in a single forward pass over range(nj), which is only correct
    if every parent has already been visited."""
    for child_i, parent_i in enumerate(JOINT_PARENTS):
        assert (
            parent_i < child_i
        ), f"{JOINT_NAMES[child_i]} (parent index {parent_i}) violates topological order"


def test_hips_is_the_only_root():
    roots = [i for i, p in enumerate(JOINT_PARENTS) if p < 0]
    assert roots == [0]
    assert JOINT_NAMES[0] == "mixamorig:Hips"


def test_build_skeleton_produces_anatomically_ordered_joints():
    skel = build_skeleton(_synthetic_landmarks())
    idx = {n: i for i, n in enumerate(skel.names)}
    p = skel.positions
    assert (
        p[idx["mixamorig:Hips"]][1]
        < p[idx["mixamorig:Neck"]][1]
        < p[idx["mixamorig:HeadTop_End"]][1]
    )
    assert p[idx["mixamorig:Head"]][1] < p[idx["mixamorig:HeadTop_End"]][1]
    # left/right symmetry: arm joints mirror in x, share y and z
    for base in ("Arm", "ForeArm", "Hand"):
        left, right = p[idx[f"mixamorig:Left{base}"]], p[idx[f"mixamorig:Right{base}"]]
        np.testing.assert_allclose(left[0], -right[0], atol=1e-9)


def test_build_skeleton_scales_with_height():
    """Running the same landmark shape at 2x height should produce joints at
    roughly 2x the Y position — the core promise behind height-normalization."""
    tall = build_skeleton(_synthetic_landmarks(height=1.911))
    short = build_skeleton(_synthetic_landmarks(height=0.9555))  # half height
    idx = {n: i for i, n in enumerate(tall.names)}
    ratio = (
        short.positions[idx["mixamorig:HeadTop_End"]][1]
        / tall.positions[idx["mixamorig:HeadTop_End"]][1]
    )
    assert 0.45 < ratio < 0.55
