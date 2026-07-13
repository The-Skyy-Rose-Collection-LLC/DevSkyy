"""verify.py's pure-numpy FK: the math a passing WS6 gate actually depends on.

Uses a hand-solved 2-joint chain (Root at origin, Child at [0,1,0], a vertex
fully weighted to Child at [0,2,0]) so every expected number below is derived
by hand, not just asserted against the code's own output. Rotating Root 90deg
about Z should carry that vertex rigidly from [0,2,0] to [-2,0,0] — it sits on
an unbent Root->Child->Vertex chain, so it behaves like a rigid rod hinged at
Root's origin.
"""

from __future__ import annotations

import numpy as np

from skyyrose.character_pipeline.skeleton import Skeleton
from skyyrose.character_pipeline.verify import (
    _local_matrices,
    _skin_matrices,
    _world_matrices,
    deform,
)


def _two_joint_skeleton() -> Skeleton:
    return Skeleton(
        names=["Root", "Child"],
        parents=[-1, 0],
        positions=np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
    )


def test_identity_pose_reproduces_bind_position():
    skel = _two_joint_skeleton()
    v = np.array([[0.0, 2.0, 0.0]])
    joints4 = np.array([[1, 1, 1, 1]])
    weights4 = np.array([[1.0, 0.0, 0.0, 0.0]])
    skin_mats = _skin_matrices(skel, {})
    deformed = deform(v, joints4, weights4, skin_mats)
    np.testing.assert_allclose(deformed, v, atol=1e-10)


def test_root_rotation_carries_child_weighted_vertex_rigidly():
    skel = _two_joint_skeleton()
    v = np.array([[0.0, 2.0, 0.0]])
    joints4 = np.array([[1, 1, 1, 1]])
    weights4 = np.array([[1.0, 0.0, 0.0, 0.0]])
    skin_mats = _skin_matrices(skel, {"Root": [("z", np.pi / 2)]})
    deformed = deform(v, joints4, weights4, skin_mats)
    np.testing.assert_allclose(deformed, [[-2.0, 0.0, 0.0]], atol=1e-9)


def test_world_matrices_compose_parent_before_child():
    skel = _two_joint_skeleton()
    local = _local_matrices(skel, {"Root": [("z", np.pi / 2)]})
    world = _world_matrices(skel, local)
    # Root has no parent: its world matrix IS its local matrix.
    np.testing.assert_allclose(world[0], local[0])
    # Child's world translation = Root's rotation applied to Child's local offset [0,1,0].
    np.testing.assert_allclose(world[1][:3, 3], [-1.0, 0.0, 0.0], atol=1e-9)


def test_weighted_blend_of_two_joints_averages_correctly():
    """A vertex split 50/50 between Root (stationary) and Child (moved by the
    pose) should land exactly halfway between where each joint alone would
    place it — the defining behavior of linear blend skinning."""
    skel = _two_joint_skeleton()
    v = np.array([[0.0, 1.0, 0.0]])
    joints4 = np.array([[0, 1, 1, 1]])
    weights4 = np.array([[0.5, 0.5, 0.0, 0.0]])
    skin_mats = _skin_matrices(skel, {"Root": [("z", np.pi / 2)]})
    deformed = deform(v, joints4, weights4, skin_mats)

    root_only = deform(v, np.array([[0, 0, 0, 0]]), np.array([[1.0, 0, 0, 0]]), skin_mats)
    child_only = deform(v, np.array([[1, 1, 1, 1]]), np.array([[1.0, 0, 0, 0]]), skin_mats)
    np.testing.assert_allclose(deformed, 0.5 * root_only + 0.5 * child_only, atol=1e-10)
