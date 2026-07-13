"""Shared vector-geometry helpers used by segment.py, weights.py, and verify.py.

Kept separate from _glb_io.py (binary read/write) since this is pure numeric
math with no glTF dependency.
"""

from __future__ import annotations

import numpy as np


def point_segment_distance(V: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Distance from every row of `V` to the line segment a->b."""
    ab = b - a
    l2 = ab @ ab
    t = np.clip(((V - a) @ ab) / (l2 + 1e-12), 0, 1)
    return np.linalg.norm(V - (a + t[:, None] * ab), axis=1)


def rotation_matrix(axis: str, angle: float) -> np.ndarray:
    """3x3 rotation matrix for a single-axis rotation by `angle` radians."""
    c, s = np.cos(angle), np.sin(angle)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    if axis == "z":
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    raise ValueError(f"unknown rotation axis {axis!r}, expected 'x', 'y', or 'z'")
