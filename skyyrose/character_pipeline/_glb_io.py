"""Shared GLB binary read/write helpers used across every character_pipeline workstream.

Both reference scripts (clean_static.py, rig_girl.py) duplicated an identical
accessor-reader and a chunk-accumulator closure. This module exists once so
convert/clean/landmarks/segment/weights/verify/package share the exact same
byte-layout logic instead of six copies drifting apart.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from pygltflib import GLTF2, Accessor, BufferView

_COMPONENT_DTYPES = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_TYPE_SIZES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_accessor(gltf: GLTF2, blob: bytes, index: int) -> np.ndarray:
    """Read a glTF accessor's data out of the binary blob as a numpy array.

    Handles both tight-packed and interleaved (byteStride) bufferViews — glTF
    legally allows attributes to share a strided view, and externally-produced
    GLBs (FBX2glTF output, user passthrough) are exactly where that layout
    appears; a flat frombuffer read on strided data returns silent garbage.
    """
    acc = gltf.accessors[index]
    bv = gltf.bufferViews[acc.bufferView]
    start = (bv.byteOffset or 0) + (acc.byteOffset or 0)
    ts = _TYPE_SIZES[acc.type]
    dt = _COMPONENT_DTYPES[acc.componentType]
    tight = ts * np.dtype(dt).itemsize
    stride = bv.byteStride or 0
    if stride and stride != tight:
        raw = np.frombuffer(blob, dtype=np.uint8)
        offsets = start + np.arange(acc.count)[:, None] * stride + np.arange(tight)[None, :]
        arr = np.frombuffer(raw[offsets].tobytes(), dtype=dt)
    else:
        arr = np.frombuffer(blob, dtype=dt, count=acc.count * ts, offset=start)
    return arr.reshape(acc.count, ts) if ts > 1 else arr


def image_bytes(gltf: GLTF2, blob: bytes, image_index: int) -> bytes:
    """Slice an embedded image's raw bytes out of the binary blob."""
    bv = gltf.bufferViews[gltf.images[image_index].bufferView]
    start = bv.byteOffset or 0
    return blob[start : start + bv.byteLength]


@dataclass
class GLBWriter:
    """Accumulates accessors/bufferViews/images into one 4-byte-padded binary blob.

    Generalizes the `add()` closure duplicated in both reference scripts: pads
    each chunk to glTF's required 4-byte alignment, tracks the running byte
    offset, and returns the accessor (or bufferView, for images) index needed
    to wire into `Attributes(...)` / `Skin(...)` / `Image(...)`.
    """

    chunks: list[bytes] = field(default_factory=list)
    views: list[BufferView] = field(default_factory=list)
    accessors: list[Accessor] = field(default_factory=list)
    _offset: int = 0

    def add_accessor(
        self,
        data: bytes,
        target: int | None,
        component_type: int,
        count: int,
        accessor_type: str,
        minmax: tuple[list, list] | None = None,
    ) -> int:
        """Appends a data chunk as a new bufferView + accessor pair. Returns the accessor index."""
        pad = (-self._offset) % 4
        self._offset += pad
        self.chunks.append(b"\x00" * pad + data)
        self.views.append(
            BufferView(buffer=0, byteOffset=self._offset, byteLength=len(data), target=target)
        )
        acc = Accessor(
            bufferView=len(self.views) - 1,
            componentType=component_type,
            count=count,
            type=accessor_type,
        )
        if minmax:
            acc.min, acc.max = minmax
        self.accessors.append(acc)
        self._offset += len(data)
        return len(self.accessors) - 1

    def add_image(self, data: bytes) -> int:
        """Appends a raw image blob as a bufferView with no accessor/target. Returns the bufferView index."""
        pad = (-self._offset) % 4
        self._offset += pad
        self.chunks.append(b"\x00" * pad + data)
        self.views.append(BufferView(buffer=0, byteOffset=self._offset, byteLength=len(data)))
        self._offset += len(data)
        return len(self.views) - 1

    def finalize(self) -> bytes:
        """Concatenates every chunk into the final binary blob to pass to `GLTF2.set_binary_blob()`."""
        return b"".join(self.chunks)
