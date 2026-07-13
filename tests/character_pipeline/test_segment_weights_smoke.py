"""segment.py + weights.py smoke test on a small synthetic humanoid-shaped grid mesh.

Builds a regular triangulated grid spanning a plausible body silhouette (torso
column + two arm strips, all in one connected sheet — no engineered welds, so
the weld-cut loop should converge with zero cuts) and a hand-built 25-joint
Skeleton with proportions in the same coordinate space. This isn't a
photoreal character; it exists to prove the segmentation + weight-solve
pipeline runs end-to-end on real mesh connectivity and produces
spatially-sane, numerically-valid output.
"""

from __future__ import annotations

import numpy as np

from skyyrose.character_pipeline.segment import ARM_L, ARM_R, BODY, segment_mesh
from skyyrose.character_pipeline.skeleton import JOINT_NAMES, JOINT_PARENTS, Skeleton
from skyyrose.character_pipeline.weights import solve_weights


def _grid_mesh(
    rows: int, cols: int, x0: float, x1: float, y0: float, y1: float
) -> tuple[np.ndarray, np.ndarray]:
    xs = np.linspace(x0, x1, cols)
    ys = np.linspace(y0, y1, rows)
    verts = np.array([[x, y, 0.0] for y in ys for x in xs])
    faces = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            i0 = r * cols + c
            i1 = i0 + 1
            i2 = i0 + cols
            i3 = i2 + 1
            faces += [i0, i2, i1, i1, i2, i3]
    return verts, np.array(faces, dtype=np.uint32)


def _synthetic_body_mesh() -> tuple[np.ndarray, np.ndarray]:
    """A torso column (narrow, tall) and two arm strips (wide, at shoulder
    height) sharing enough grid resolution to stay a single connected sheet."""
    torso_v, torso_f = _grid_mesh(rows=12, cols=3, x0=-0.10, x1=0.10, y0=0.0, y1=1.90)
    arm_l_v, arm_l_f = _grid_mesh(rows=3, cols=6, x0=0.10, x1=0.55, y0=1.15, y1=1.30)
    arm_r_v, arm_r_f = _grid_mesh(rows=3, cols=6, x0=-0.55, x1=-0.10, y0=1.15, y1=1.30)

    offset_l = len(torso_v)
    offset_r = offset_l + len(arm_l_v)
    verts = np.vstack([torso_v, arm_l_v, arm_r_v])
    faces = np.concatenate([torso_f, arm_l_f + offset_l, arm_r_f + offset_r])

    # Stitch the arm strips to the torso column with a bridging triangle strip
    # at shoulder height (row 4 of the 12-row torso grid, y ~= 1.90*4/11).
    torso_cols = 3
    shoulder_row = 7
    torso_edge_l = shoulder_row * torso_cols + (
        torso_cols - 1
    )  # rightmost torso vert at shoulder height
    torso_edge_r = shoulder_row * torso_cols  # leftmost torso vert at shoulder height
    arm_l_root_top = offset_l + 0 * 6  # arm strip's innermost column, top row
    arm_l_root_bot = offset_l + 1 * 6
    arm_r_root_top = offset_r + 0 * 6 + 5
    arm_r_root_bot = offset_r + 1 * 6 + 5

    bridge = np.array(
        [
            torso_edge_l,
            arm_l_root_top,
            arm_l_root_bot,
            arm_r_root_top,
            torso_edge_r,
            arm_r_root_bot,
        ],
        dtype=np.uint32,
    )
    faces = np.concatenate([faces, bridge])
    return verts, faces


def _synthetic_skeleton() -> Skeleton:
    """25 joints in the same coordinate space as `_synthetic_body_mesh`,
    matching JOINT_NAMES/JOINT_PARENTS ordering exactly."""
    idx = {n: i for i, n in enumerate(JOINT_NAMES)}
    p = np.zeros((25, 3))
    p[idx["mixamorig:Hips"]] = [0, 0.64, 0]
    p[idx["mixamorig:Spine"]] = [0, 0.80, 0]
    p[idx["mixamorig:Spine1"]] = [0, 0.95, 0]
    p[idx["mixamorig:Spine2"]] = [0, 1.10, 0]
    p[idx["mixamorig:Neck"]] = [0, 1.28, 0]
    p[idx["mixamorig:Head"]] = [0, 1.38, 0]
    p[idx["mixamorig:HeadTop_End"]] = [0, 1.90, 0]
    p[idx["mixamorig:LeftShoulder"]] = [0.06, 1.24, 0]
    p[idx["mixamorig:LeftArm"]] = [0.15, 1.22, 0]
    p[idx["mixamorig:LeftForeArm"]] = [0.35, 1.22, 0]
    p[idx["mixamorig:LeftHand"]] = [0.53, 1.22, 0]
    p[idx["mixamorig:RightShoulder"]] = [-0.06, 1.24, 0]
    p[idx["mixamorig:RightArm"]] = [-0.15, 1.22, 0]
    p[idx["mixamorig:RightForeArm"]] = [-0.35, 1.22, 0]
    p[idx["mixamorig:RightHand"]] = [-0.53, 1.22, 0]
    p[idx["mixamorig:LeftUpLeg"]] = [0.09, 0.60, 0]
    p[idx["mixamorig:LeftLeg"]] = [0.09, 0.33, 0]
    p[idx["mixamorig:LeftFoot"]] = [0.09, 0.09, 0]
    p[idx["mixamorig:LeftToeBase"]] = [0.09, 0.03, 0.06]
    p[idx["mixamorig:LeftToe_End"]] = [0.09, 0.02, 0.14]
    p[idx["mixamorig:RightUpLeg"]] = [-0.09, 0.60, 0]
    p[idx["mixamorig:RightLeg"]] = [-0.09, 0.33, 0]
    p[idx["mixamorig:RightFoot"]] = [-0.09, 0.09, 0]
    p[idx["mixamorig:RightToeBase"]] = [-0.09, 0.03, 0.06]
    p[idx["mixamorig:RightToe_End"]] = [-0.09, 0.02, 0.14]
    return Skeleton(names=JOINT_NAMES, parents=JOINT_PARENTS, positions=p)


def test_segment_mesh_labels_arm_regions_correctly():
    v, f = _synthetic_body_mesh()
    skel = _synthetic_skeleton()
    result = segment_mesh(v, f, skel)

    assert result.converged
    assert (result.labels == ARM_L).any()
    assert (result.labels == ARM_R).any()
    assert (result.labels == BODY).any()
    # Every vertex far out on the left arm strip must be labeled ARM_L, not BODY.
    far_left_arm = np.where((v[:, 0] > 0.45) & (v[:, 1] > 1.1) & (v[:, 1] < 1.35))[0]
    assert far_left_arm.size > 0
    assert (result.labels[far_left_arm] == ARM_L).all()
    # A torso vertex far below the shoulder must never be labeled arm.
    low_torso = np.where((np.abs(v[:, 0]) < 0.11) & (v[:, 1] < 0.3))[0]
    assert low_torso.size > 0
    assert (result.labels[low_torso] == BODY).all()


def test_segment_mesh_converges_with_no_engineered_welds():
    """This synthetic mesh has no welded bridge triangles (unlike an AI export),
    so the weld-cut loop should converge on pass 0 with nothing to cut."""
    v, f = _synthetic_body_mesh()
    skel = _synthetic_skeleton()
    result = segment_mesh(v, f, skel)
    assert result.total_cut == 0
    assert result.passes_run == 1


def test_solve_weights_produces_valid_normalized_output():
    v, f = _synthetic_body_mesh()
    skel = _synthetic_skeleton()
    seg = segment_mesh(v, f, skel)
    weights = solve_weights(v, skel, seg)

    assert weights.joints.shape == (len(v), 4)
    assert weights.weights.shape == (len(v), 4)
    np.testing.assert_allclose(weights.weights.sum(axis=1), 1.0, atol=1e-5)
    assert weights.joints.max() < len(JOINT_NAMES)
    assert weights.joints.min() >= 0
    assert (
        weights.dead_vert_count == 0
    )  # every vertex sits within some bone's radius-normalized reach
