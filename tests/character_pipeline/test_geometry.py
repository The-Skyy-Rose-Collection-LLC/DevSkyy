"""_geometry: point-segment distance and single-axis rotation matrix correctness."""

from __future__ import annotations

import numpy as np
import pytest

from skyyrose.character_pipeline._geometry import point_segment_distance, rotation_matrix


def test_point_segment_distance_perpendicular_to_midpoint():
    a, b = np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0])
    v = np.array([[0.5, 1.0, 0.0]])
    d = point_segment_distance(v, a, b)
    np.testing.assert_allclose(d, [1.0])


def test_point_segment_distance_clamps_past_endpoints():
    a, b = np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0])
    v = np.array(
        [[2.0, 0.0, 0.0]]
    )  # past `b` — nearest point is `b` itself, not an extrapolated line point
    d = point_segment_distance(v, a, b)
    np.testing.assert_allclose(d, [1.0])


def test_point_segment_distance_zero_length_segment_is_point_distance():
    a = b = np.array([0.0, 0.0, 0.0])
    v = np.array([[3.0, 4.0, 0.0]])
    d = point_segment_distance(v, a, b)
    np.testing.assert_allclose(d, [5.0])


@pytest.mark.parametrize(
    ("axis", "point", "expected"),
    [
        ("z", [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),  # +90deg about z: +x -> +y
        ("y", [1.0, 0.0, 0.0], [0.0, 0.0, -1.0]),  # +90deg about y: +x -> -z
        ("x", [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]),  # +90deg about x: +y -> +z
    ],
)
def test_rotation_matrix_quarter_turn(axis, point, expected):
    r = rotation_matrix(axis, np.pi / 2)
    result = r @ np.array(point)
    np.testing.assert_allclose(result, expected, atol=1e-10)


def test_rotation_matrix_zero_angle_is_identity():
    for axis in ("x", "y", "z"):
        np.testing.assert_allclose(rotation_matrix(axis, 0.0), np.eye(3), atol=1e-12)


def test_rotation_matrix_rejects_unknown_axis():
    with pytest.raises(ValueError):
        rotation_matrix("w", 0.5)
