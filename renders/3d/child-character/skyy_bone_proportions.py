"""Extract skyy.glb's own 24-bone rest-pose landmarks as HEIGHT-FRACTIONS
(head_local.z / total_height, tail_local.z / total_height), plus X-offsets
for limb bones, so a new rig can be built for a DIFFERENT-proportioned
character using this project's own reference proportions (per bug-290's
lesson: use a reference rig's measured ratios, never a naive 50/50 midpoint).

Run: blender --background --factory-startup --python skyy_bone_proportions.py
"""

import json
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SKYY = os.path.join(
    HERE, "..", "..", "..", "wordpress-theme", "skyyrose-flagship", "assets", "models", "skyy.glb"
)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=SKYY)

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))

# total character height = mesh world-space bbox z-range
verts_z = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
z_min, z_max = min(verts_z), max(verts_z)
height = z_max - z_min
print(f"skyy.glb mesh world height={height:.5f} (z_min={z_min:.5f} z_max={z_max:.5f})")

report = {}
for b in arm.data.bones:
    head_w = arm.matrix_world @ b.head_local
    tail_w = arm.matrix_world @ b.tail_local
    report[b.name] = {
        "head_z_frac": round((head_w.z - z_min) / height, 5),
        "tail_z_frac": round((tail_w.z - z_min) / height, 5),
        "head_x": round(head_w.x, 5),
        "tail_x": round(tail_w.x, 5),
        "head_y": round(head_w.y, 5),
        "tail_y": round(tail_w.y, 5),
    }

print(json.dumps(report, indent=2))

out_path = os.path.join(HERE, "skyy_proportions.json")
with open(out_path, "w") as f:
    json.dump({"height": height, "z_min": z_min, "bones": report}, f, indent=2)
print(f"Wrote {out_path}")
