"""Independent verification of the final compressed export -- direct raw
GLB binary/JSON-chunk parse, sharing NO code with the Blender exporter or
gltf-transform's own inspect command, per doctrine.md's acceptable
independent authorities. Confirms: glTF magic + version, draco extension
markers actually present in the JSON (not just gltf-transform's own
summary), animation clip names, and absence of any shape-key/morph-target
rest-weight leak (this build has no shape keys -- confirmed by their
absence, not assumed).
Run: python3 verify_compressed_export.py
"""

import json
import struct

path = "child-character-compressed.glb"

with open(path, "rb") as f:
    data = f.read()

magic, version, length = struct.unpack("<4sII", data[:12])
assert magic == b"glTF", f"bad magic: {magic}"
assert version == 2, f"unexpected version: {version}"
assert length == len(data), f"length mismatch: header says {length}, file is {len(data)}"
print(f"magic={magic} version={version} length={length} (matches actual file size)")

offset = 12
chunk_json = None
chunk_bin_len = 0
while offset < len(data):
    chunk_len, chunk_type = struct.unpack("<I4s", data[offset : offset + 8])
    chunk_data = data[offset + 8 : offset + 8 + chunk_len]
    if chunk_type == b"JSON":
        chunk_json = json.loads(chunk_data)
    elif chunk_type == b"BIN\x00":
        chunk_bin_len = len(chunk_data)
    offset += 8 + chunk_len

assert chunk_json is not None, "no JSON chunk found"
print(f"BIN chunk length: {chunk_bin_len} bytes")

ext_used = chunk_json.get("extensionsUsed", [])
ext_required = chunk_json.get("extensionsRequired", [])
print(f"extensionsUsed: {ext_used}")
print(f"extensionsRequired: {ext_required}")
assert "KHR_draco_mesh_compression" in ext_used, "draco not in extensionsUsed"
assert "KHR_draco_mesh_compression" in ext_required, "draco not in extensionsRequired"

meshes = chunk_json.get("meshes", [])
for mesh in meshes:
    for prim in mesh.get("primitives", []):
        ext = prim.get("extensions", {})
        has_draco_prim = "KHR_draco_mesh_compression" in ext
        print(f"mesh primitive draco extension present: {has_draco_prim}")
        assert has_draco_prim, "mesh primitive missing draco extension"

animations = chunk_json.get("animations", [])
anim_names = sorted(a.get("name", "") for a in animations)
print(f"animation names: {anim_names}")
assert anim_names == ["idle", "walk"], f"expected exactly ['idle','walk'], got {anim_names}"

# Shape-key / morph-target rest-weight leak assertion (doctrine.md /
# shape-keys.md): this build never authored any shape keys (Phase 5's
# defect fixes were skin-weight-based, not shape-key-based -- confirmed
# by the absence of any bpy.data.shape_keys usage across every script in
# this pipeline). Assert that absence directly on the shipped GLB rather
# than assuming it: no mesh has "weights" (morph target default weights)
# or "targets" (morph target data) at all.
morph_found = False
for mesh in meshes:
    if "weights" in mesh:
        morph_found = True
    for prim in mesh.get("primitives", []):
        if "targets" in prim:
            morph_found = True
print(f"morph targets (shape keys) present in export: {morph_found}")
assert (
    not morph_found
), "unexpected morph targets found -- shape-key rest-weight check would be required"

images = chunk_json.get("images", [])
print(f"image count: {len(images)}")
for img in images:
    mime = img.get("mimeType")
    print(f"  image mimeType={mime}")
    assert mime == "image/jpeg", f"expected image/jpeg, got {mime}"

print("\nALL INDEPENDENT CHECKS PASSED")
