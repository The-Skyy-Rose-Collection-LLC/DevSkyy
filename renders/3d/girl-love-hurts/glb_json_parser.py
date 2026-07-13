"""
Minimal, independent binary-glTF (.glb) container + accessor decoder.

Pure stdlib Python (struct + json), no bpy, no third-party glTF library (none
available in this environment -- gltf-transform is not installed here either,
matching the "no npx registry" constraint noted in prior sessions' bug-194
verification). Deliberately re-derived from the glTF 2.0 binary container
spec directly rather than trusting any prior script or a Blender re-import,
so that Gate D (F-curve/animation audit) checks exactly what a real runtime
GLTFLoader would parse from the exported bytes -- the same authoritative
method bug-214's independent verifier used ("raw glTF JSON parse") as one of
its 4 cross-checks.

GLB container layout (spec, verified against the exported file's own magic +
chunk headers, not assumed):
    12-byte header:  magic("glTF") uint32, version uint32, length uint32
    chunk 0 (JSON):  chunkLength uint32, chunkType uint32 (0x4E4F534A), data
    chunk 1 (BIN):   chunkLength uint32, chunkType uint32 (0x004E4942), data
"""

import json
import struct

GLTF_MAGIC = b"glTF"
CHUNK_TYPE_JSON = 0x4E4F534A
CHUNK_TYPE_BIN = 0x004E4942

COMPONENT_TYPE_STRUCT = {
    5120: ("b", 1),  # BYTE
    5121: ("B", 1),  # UNSIGNED_BYTE
    5122: ("h", 2),  # SHORT
    5123: ("H", 2),  # UNSIGNED_SHORT
    5125: ("I", 4),  # UNSIGNED_INT
    5126: ("f", 4),  # FLOAT
}

TYPE_COMPONENT_COUNT = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT4": 16,
}


def read_glb(path):
    """Parse the GLB container. Returns (gltf_json: dict, bin_chunk: bytes|None)."""
    with open(path, "rb") as f:
        data = f.read()

    magic, version, total_length = struct.unpack_from("<4sII", data, 0)
    if magic != GLTF_MAGIC:
        raise ValueError(f"not a GLB file (magic={magic!r})")
    if total_length != len(data):
        raise ValueError(f"GLB header length {total_length} != actual file size {len(data)}")

    offset = 12
    json_chunk = None
    bin_chunk = None
    while offset < total_length:
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        chunk_data = data[offset + 8 : offset + 8 + chunk_length]
        if chunk_type == CHUNK_TYPE_JSON:
            json_chunk = chunk_data
        elif chunk_type == CHUNK_TYPE_BIN:
            bin_chunk = chunk_data
        else:
            raise ValueError(f"unexpected GLB chunk type 0x{chunk_type:08X} at offset {offset}")
        offset += 8 + chunk_length

    if json_chunk is None:
        raise ValueError("GLB has no JSON chunk")

    gltf = json.loads(json_chunk.decode("utf-8"))
    return gltf, bin_chunk


def read_accessor(gltf, bin_chunk, accessor_index):
    """Decode accessor `accessor_index` into a flat list of tuples (one tuple
    per element, length = component count). Only the single-buffer,
    non-sparse, bufferView-backed case is supported -- anything else fails
    loudly rather than silently returning wrong data."""
    accessor = gltf["accessors"][accessor_index]
    if "sparse" in accessor:
        raise NotImplementedError(f"accessor {accessor_index}: sparse accessors not supported")
    if "bufferView" not in accessor:
        raise NotImplementedError(
            f"accessor {accessor_index}: bufferView-less accessors not supported"
        )

    buffer_view = gltf["bufferViews"][accessor["bufferView"]]
    if buffer_view.get("buffer", 0) != 0:
        raise NotImplementedError("multi-buffer GLBs not supported")
    if bin_chunk is None:
        raise ValueError("accessor references bufferView but GLB has no BIN chunk")

    comp_fmt, comp_size = COMPONENT_TYPE_STRUCT[accessor["componentType"]]
    n_comp = TYPE_COMPONENT_COUNT[accessor["type"]]
    count = accessor["count"]

    bv_offset = buffer_view.get("byteOffset", 0)
    acc_offset = accessor.get("byteOffset", 0)
    base_offset = bv_offset + acc_offset

    default_element_stride = comp_size * n_comp
    stride = buffer_view.get("byteStride", default_element_stride)

    fmt = "<" + comp_fmt * n_comp
    out = []
    for i in range(count):
        elem_offset = base_offset + i * stride
        vals = struct.unpack_from(fmt, bin_chunk, elem_offset)
        out.append(vals)

    normalized = accessor.get("normalized", False)
    if normalized and comp_fmt in ("b", "B", "h", "H"):
        max_val = {"b": 127, "B": 255, "h": 32767, "H": 65535}[comp_fmt]
        out = [tuple(v / max_val for v in elem) for elem in out]

    return out


def node_name(gltf, node_index):
    return gltf["nodes"][node_index].get("name", f"<node {node_index}>")
