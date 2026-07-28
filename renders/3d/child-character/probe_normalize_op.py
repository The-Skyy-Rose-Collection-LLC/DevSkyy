"""Probe bpy.ops.object.vertex_group_normalize_all's real signature and
whether it can run headless without weight-paint mode, on THIS Blender
5.1.2 build -- before relying on memory for its semantics (doctrine.md).
Run: blender --background --factory-startup --python probe_normalize_op.py
"""

import bpy

op = bpy.ops.object.vertex_group_normalize_all
print("rna_type:", op.get_rna_type().name)
for p in op.get_rna_type().properties:
    if p.identifier == "rna_type":
        continue
    print(
        f"  param: {p.identifier} type={p.type} default={getattr(p, 'default', None)} description={p.description!r}"
    )

print("\npoll (no active object):", op.poll())
