"""read_accessor must handle interleaved (byteStride) bufferViews correctly.

glTF legally allows vertex attributes to share one bufferView with a byteStride
(e.g. POSITION+NORMAL interleaved). A tight-packed `np.frombuffer` read on such
data returns silent garbage, not an exception — externally-produced GLBs
(FBX2glTF output, user passthrough input) are exactly where this layout shows
up, and GLBWriter's own output never interleaves, so no round-trip test can
catch it.
"""

from __future__ import annotations

import numpy as np
from pygltflib import GLTF2, Accessor, Asset, Buffer, BufferView

from skyyrose.character_pipeline import _glb_io

POSITIONS = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.float32)
NORMALS = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], dtype=np.float32)


def _interleaved_gltf() -> tuple[GLTF2, bytes]:
    """One bufferView holding [pos0 nrm0 pos1 nrm1 pos2 nrm2], stride 24 bytes;
    two accessors into it: positions at byteOffset 0, normals at byteOffset 12."""
    interleaved = np.hstack([POSITIONS, NORMALS]).astype(np.float32)  # (3, 6)
    blob = interleaved.tobytes()
    gltf = GLTF2(
        asset=Asset(version="2.0"),
        buffers=[Buffer(byteLength=len(blob))],
        bufferViews=[BufferView(buffer=0, byteOffset=0, byteLength=len(blob), byteStride=24)],
        accessors=[
            Accessor(bufferView=0, byteOffset=0, componentType=5126, count=3, type="VEC3"),
            Accessor(bufferView=0, byteOffset=12, componentType=5126, count=3, type="VEC3"),
        ],
    )
    return gltf, blob


def test_read_accessor_interleaved_positions():
    gltf, blob = _interleaved_gltf()
    np.testing.assert_array_equal(_glb_io.read_accessor(gltf, blob, 0), POSITIONS)


def test_read_accessor_interleaved_normals():
    gltf, blob = _interleaved_gltf()
    np.testing.assert_array_equal(_glb_io.read_accessor(gltf, blob, 1), NORMALS)


def test_read_accessor_tight_stride_matches_fast_path():
    """byteStride explicitly set to the tight element size must behave exactly
    like the unset-stride fast path."""
    blob = POSITIONS.tobytes()
    gltf = GLTF2(
        asset=Asset(version="2.0"),
        buffers=[Buffer(byteLength=len(blob))],
        bufferViews=[BufferView(buffer=0, byteOffset=0, byteLength=len(blob), byteStride=12)],
        accessors=[Accessor(bufferView=0, byteOffset=0, componentType=5126, count=3, type="VEC3")],
    )
    np.testing.assert_array_equal(_glb_io.read_accessor(gltf, blob, 0), POSITIONS)
