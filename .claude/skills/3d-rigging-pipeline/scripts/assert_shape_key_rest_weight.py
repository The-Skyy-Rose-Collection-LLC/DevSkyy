#!/usr/bin/env python3
"""Assert every shape-keyed mesh node's REST morph-target weight is 0.0.

Standalone GLB JSON/binary-chunk parser -- shares NO code with any Blender
export path, per 3d-rigging-pipeline's doctrine.md independent-authority rule.
Reads only the GLB container's JSON chunk (never imports bpy), so it can run
as a plain python3 script with no Blender dependency.

A shape key's rest/default weight is exposed in glTF as node.weights (if the
node overrides it) or mesh.weights (the mesh-level default) -- node.weights
takes precedence per the glTF 2.0 spec. Any weight left non-zero here bleeds
the correction into every clip that doesn't explicitly animate it back down,
not just the clip it was meant to fix.

Usage:
    python3 assert_shape_key_rest_weight.py <file.glb> [--expect-nonzero NAME=VALUE ...]

Exit code 0 = every shape-keyed node's rest weight is 0.0 (or matches an
explicit --expect-nonzero override for a clip that deliberately holds a key
active, e.g. a wave-clip corrective key intentionally left at 1.0). Exit
code 1 = an unexplained non-zero rest weight was found.
"""

import argparse
import json
import struct
import sys

GLB_MAGIC = 0x46546C67  # 'glTF'
CHUNK_TYPE_JSON = 0x4E4F534A  # 'JSON'


def read_glb_json_chunk(path):
    with open(path, "rb") as f:
        data = f.read()

    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC:
        raise ValueError(f"{path}: not a GLB file (bad magic {magic:#x})")
    if len(data) < length:
        raise ValueError(f"{path}: truncated file, header says {length} bytes, got {len(data)}")

    offset = 12
    json_chunk = None
    while offset < length:
        chunk_len, chunk_type = struct.unpack_from("<II", data, offset)
        chunk_data = data[offset + 8 : offset + 8 + chunk_len]
        if chunk_type == CHUNK_TYPE_JSON:
            json_chunk = chunk_data
            break
        offset += 8 + chunk_len

    if json_chunk is None:
        raise ValueError(f"{path}: no JSON chunk found")
    return json.loads(json_chunk.decode("utf-8"))


def mesh_shape_key_names(mesh):
    """glTF has no native shape-key NAMES -- Blender's exporter writes them
    into mesh.extras.targetNames when present. Fall back to positional
    indices if absent."""
    extras = mesh.get("extras", {})
    names = extras.get("targetNames")
    targets = mesh.get("primitives", [{}])[0].get("targets", [])
    if names and len(names) == len(targets):
        return names
    return [f"target_{i}" for i in range(len(targets))]


def check_file(path, expected_nonzero):
    doc = read_glb_json_chunk(path)
    meshes = doc.get("meshes", [])
    nodes = doc.get("nodes", [])

    failures = []
    checked = []

    for node_idx, node in enumerate(nodes):
        mesh_idx = node.get("mesh")
        if mesh_idx is None:
            continue
        mesh = meshes[mesh_idx]
        targets = mesh.get("primitives", [{}])[0].get("targets", [])
        if not targets:
            continue

        # node.weights overrides mesh.weights per glTF 2.0 spec 5.23.
        rest_weights = node.get("weights", mesh.get("weights"))
        if rest_weights is None:
            rest_weights = [0.0] * len(targets)

        names = mesh_shape_key_names(mesh)
        if len(names) != len(rest_weights):
            raise ValueError(
                f"{path}: mesh {mesh.get('name', '?')!r} has {len(names)} shape-key name(s) "
                f"but {len(rest_weights)} rest weight(s) -- malformed export, fail loud rather "
                f"than silently truncate"
            )
        for name, weight in zip(names, rest_weights, strict=True):
            checked.append((name, weight))
            expected = expected_nonzero.get(name)
            if expected is not None:
                if abs(weight - expected) > 1e-6:
                    failures.append(
                        f"{name}: rest weight {weight} does not match declared "
                        f"expected-nonzero value {expected}"
                    )
            elif abs(weight) > 1e-9:
                failures.append(
                    f"{name}: rest weight is {weight}, expected 0.0 "
                    f"(pass --expect-nonzero {name}={weight} if this is deliberate)"
                )

    return checked, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb_path")
    parser.add_argument(
        "--expect-nonzero",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Declare a shape key deliberately held non-zero at rest (e.g. a "
        "clip-long corrective key). Repeatable.",
    )
    args = parser.parse_args()

    expected = {}
    for item in args.expect_nonzero:
        name, _, value = item.partition("=")
        expected[name] = float(value)

    checked, failures = check_file(args.glb_path, expected)

    print(f"Checked {len(checked)} shape-key rest weight(s) in {args.glb_path}:")
    for name, weight in checked:
        print(f"  {name}: {weight}")

    if failures:
        print(f"\nFAIL -- {len(failures)} unexplained non-zero rest weight(s):")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)

    print("\nPASS -- all rest weights are 0.0 or match a declared --expect-nonzero override.")
    sys.exit(0)


if __name__ == "__main__":
    main()
