"""clean.py's _bake_transform must use the inverse-transpose for normals.

`n' = M @ n` is only direction-correct when M's linear part is a rotation or
isotropic scale; a non-uniformly-scaled ancestor node needs the inverse-
transpose (the normal matrix), or normals come out wrong-direction with no
error — visible only as broken lighting at runtime.

Hand-derivable case: a plane sloping at 45deg in YZ has normal (0, 1, 1)/√2.
Squash the geometry by 2x in Y (scale [1, 0.5, 1]): the surface flattens, so
the correct normal ROTATES TOWARD +Y — (0, 2, 1)/√5 — while naively
transforming the normal like a position would squash it TOWARD +Z —
(0, 0.5, 1)/√1.25. Opposite directions of tilt; the test discriminates cleanly.
"""

from __future__ import annotations

import numpy as np

from skyyrose.character_pipeline.clean import _bake_transform


def test_normals_under_nonuniform_scale_use_inverse_transpose():
    v = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 1.0]])
    n = np.tile(np.array([0.0, 1.0, 1.0]) / np.sqrt(2.0), (3, 1))

    transform = np.diag([1.0, 0.5, 1.0, 1.0])  # squash Y by 2x
    _, n_out = _bake_transform(v, n, transform)

    expected = np.array([0.0, 2.0, 1.0]) / np.sqrt(5.0)
    np.testing.assert_allclose(n_out, np.tile(expected, (3, 1)), atol=1e-12)


def test_normals_under_pure_rotation_unchanged_behavior():
    """Inverse-transpose of a rotation IS the rotation — the fix must not
    change behavior for the rotation-only case every real asset so far uses."""
    v = np.array([[1.0, 2.0, 3.0]])
    n = np.array([[0.0, 0.0, 1.0]])

    c, s = np.cos(-np.pi / 2), np.sin(-np.pi / 2)
    transform = np.eye(4)
    transform[:3, :3] = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

    # Rx(-90deg) maps +z to +y: row 1 of the matrix is (0, c, -s) = (0, 0, +1).
    _, n_out = _bake_transform(v, n, transform)
    np.testing.assert_allclose(n_out, [[0.0, 1.0, 0.0]], atol=1e-12)
