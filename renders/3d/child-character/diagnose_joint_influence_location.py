"""Location check for the >4-joint-influence verts: are they concentrated
at the wrist/hair seams already validated clean in Phase 4 (which would
mean the truncate-to-4 export step could reintroduce a defect there), or
elsewhere (e.g. armpit/shoulder multi-bone junctions, an expected location
for legitimate multi-bone blending)?
Run: blender --background --factory-startup --python diagnose_joint_influence_location.py
"""

import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND)
mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")

bone_head = {b.name: Vector(b.head_local) for b in arm_obj.data.bones}

over4_verts = [v for v in mesh_obj.data.vertices if len(v.groups) > 4]
print(f"verts with >4 groups: {len(over4_verts)}")

# Check distance from each such vertex to the nearest wrist point and
# nearest hair-region z-threshold (reusing Phase 4's own thresholds).
head_bone = arm_obj.data.bones["Head"]
head_span = head_bone.tail_local.z - head_bone.head_local.z
hair_z_min = head_bone.head_local.z + 0.7 * head_span

near_wrist = 0
near_hair = 0
near_shoulder = 0
other = 0
for v in over4_verts:
    p = v.co
    is_hair = p.z >= hair_z_min
    left_wrist_dist = (p - bone_head["LeftHand"]).length
    right_wrist_dist = (p - bone_head["RightHand"]).length
    left_sh_dist = (p - bone_head["LeftShoulder"]).length
    right_sh_dist = (p - bone_head["RightShoulder"]).length
    if is_hair:
        near_hair += 1
    elif min(left_wrist_dist, right_wrist_dist) < 0.05:
        near_wrist += 1
    elif min(left_sh_dist, right_sh_dist) < 0.10:
        near_shoulder += 1
    else:
        other += 1

print(f"near hair region (z>={hair_z_min:.4f}): {near_hair}")
print(f"near wrist (<0.05 from LeftHand/RightHand head): {near_wrist}")
print(f"near shoulder (<0.10 from LeftShoulder/RightShoulder head): {near_shoulder}")
print(f"other location: {other}")
