"""Root-cause check for skin_weight_child.py's complete ARMATURE_AUTO
failure (0/67232 verts weighted, not a partial failure) -- rule out an
object-transform mismatch between the armature and mesh objects before
concluding the mesh topology itself defeats heat weighting.
Run: blender --background --factory-startup --python diagnose_heatweight_fail.py
"""

import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-rig.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")

print(
    f"arm_obj: loc={tuple(arm_obj.location)} rot={tuple(arm_obj.rotation_euler)} scale={tuple(arm_obj.scale)}"
)
print(
    f"mesh_obj: loc={tuple(mesh_obj.location)} rot={tuple(mesh_obj.rotation_euler)} scale={tuple(mesh_obj.scale)}"
)

mesh_verts_world = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
mesh_z = [v.z for v in mesh_verts_world]
mesh_x = [v.x for v in mesh_verts_world]
print(
    f"mesh world bbox: x=[{min(mesh_x):.4f},{max(mesh_x):.4f}] z=[{min(mesh_z):.4f},{max(mesh_z):.4f}]"
)

for b in arm_obj.data.bones:
    head_w = arm_obj.matrix_world @ Vector(b.head_local)
    tail_w = arm_obj.matrix_world @ Vector(b.tail_local)
    print(
        f"  bone {b.name}: head_world={tuple(round(c,4) for c in head_w)} tail_world={tuple(round(c,4) for c in tail_w)}"
    )

# Check if mesh has multiple UV-vert-split copies at the SAME position but
# is otherwise a proper closed volume -- heat weighting can fail if bones
# are literally outside a hollow/open mesh shell with no interior.
print(f"\nmesh polygon count: {len(mesh_obj.data.polygons)}")
print(f"mesh vertex count: {len(mesh_obj.data.vertices)}")
