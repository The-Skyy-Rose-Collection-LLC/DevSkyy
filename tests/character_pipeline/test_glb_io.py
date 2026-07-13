"""_glb_io round-trip: what GLBWriter writes, read_accessor must read back exactly."""

from __future__ import annotations

import numpy as np
from pygltflib import (
    ARRAY_BUFFER,
    ELEMENT_ARRAY_BUFFER,
    GLTF2,
    Asset,
    Attributes,
    Buffer,
    Mesh,
    Node,
    Primitive,
    Scene,
)

from skyyrose.character_pipeline import _glb_io


def _build_triangle_glb(tmp_path):
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32)
    indices = np.array([0, 1, 2], dtype=np.uint32)

    writer = _glb_io.GLBWriter()
    a_pos = writer.add_accessor(
        positions.tobytes(),
        ARRAY_BUFFER,
        5126,
        len(positions),
        "VEC3",
        (positions.min(0).tolist(), positions.max(0).tolist()),
    )
    a_idx = writer.add_accessor(
        indices.tobytes(), ELEMENT_ARRAY_BUFFER, 5125, len(indices), "SCALAR"
    )
    blob = writer.finalize()

    gltf = GLTF2(
        asset=Asset(version="2.0"),
        scenes=[Scene(nodes=[0])],
        scene=0,
        nodes=[Node(name="Tri", mesh=0)],
        meshes=[Mesh(primitives=[Primitive(attributes=Attributes(POSITION=a_pos), indices=a_idx)])],
        buffers=[Buffer(byteLength=len(blob))],
        bufferViews=writer.views,
        accessors=writer.accessors,
    )
    gltf.set_binary_blob(blob)
    out_path = tmp_path / "tri.glb"
    gltf.save(str(out_path))
    return out_path, positions, indices


def test_read_accessor_round_trips_positions(tmp_path):
    out_path, positions, _ = _build_triangle_glb(tmp_path)
    reloaded = GLTF2().load(str(out_path))
    blob = reloaded.binary_blob()
    prim = reloaded.meshes[0].primitives[0]
    read_back = _glb_io.read_accessor(reloaded, blob, prim.attributes.POSITION)
    np.testing.assert_array_equal(read_back, positions)


def test_read_accessor_round_trips_indices(tmp_path):
    out_path, _, indices = _build_triangle_glb(tmp_path)
    reloaded = GLTF2().load(str(out_path))
    blob = reloaded.binary_blob()
    prim = reloaded.meshes[0].primitives[0]
    read_back = _glb_io.read_accessor(reloaded, blob, prim.indices)
    np.testing.assert_array_equal(read_back, indices)


def test_glb_writer_pads_every_chunk_to_four_bytes():
    writer = _glb_io.GLBWriter()
    # 3-byte payload forces the next chunk to need padding.
    writer.add_accessor(b"\x01\x02\x03", None, 5121, 3, "SCALAR")
    writer.add_accessor(b"\x04\x05\x06\x07", None, 5121, 4, "SCALAR")
    blob = writer.finalize()
    assert writer.views[1].byteOffset % 4 == 0
    assert len(blob) % 4 == 0


def test_add_image_returns_bufferview_not_accessor_index():
    writer = _glb_io.GLBWriter()
    writer.add_accessor(b"\x00" * 12, ARRAY_BUFFER, 5126, 1, "VEC3")
    img_view = writer.add_image(b"fake-jpeg-bytes")
    assert img_view == len(writer.views) - 1
    assert len(writer.accessors) == 1  # image adds a bufferView, not an accessor
