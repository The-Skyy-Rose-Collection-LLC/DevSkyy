"""Check whether the skin_weight_child.py hair-seam gate's failing verts
(w_head ~0.944-0.945, right at the 0.95 threshold) are genuinely
mid-hair -- which would indicate a real crack-seam defect (bug-297
precedent) -- or are actually positioned near the neck/Head joint itself,
where a smooth blend to neck is the CORRECT heat-solver behavior, and the
gate's own z-cutoff (70% of head bone span) is simply too close to that
joint for this particular head bone's proportions.
Run: blender --background --factory-startup --python diagnose_hair_boundary.py
"""

import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-skinned.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")

head_bone = arm_obj.data.bones["Head"]
neck_bone = arm_obj.data.bones["neck"]
print(f"neck: head_z={neck_bone.head_local.z:.4f} tail_z={neck_bone.tail_local.z:.4f}")
print(f"Head: head_z={head_bone.head_local.z:.4f} tail_z={head_bone.tail_local.z:.4f}")

head_z_gi = mesh_obj.vertex_groups["Head"].index
neck_z_gi = mesh_obj.vertex_groups["neck"].index


def get_weight(v, gi):
    for g in v.groups:
        if g.group == gi:
            return g.weight
    return 0.0


# Distribution of z for the failing verts vs all hair-sampled verts
head_span = head_bone.tail_local.z - head_bone.head_local.z
hair_z_min = head_bone.head_local.z + 0.7 * head_span
print(f"hair_z_min cutoff = {hair_z_min:.4f} (Head.head_z + 70%% of Head span)")

fail_zs = []
pass_zs = []
for v in mesh_obj.data.vertices:
    if v.co.z < hair_z_min:
        continue
    w_head = get_weight(v, head_z_gi)
    w_neck = get_weight(v, neck_z_gi)
    if w_head < 0.95 or w_neck > 0.05:
        fail_zs.append(v.co.z)
    else:
        pass_zs.append(v.co.z)

fail_zs.sort()
pass_zs.sort()
print(f"\nfailing verts z-range: [{fail_zs[0]:.4f}, {fail_zs[-1]:.4f}] n={len(fail_zs)}")
print(f"passing verts z-range: [{pass_zs[0]:.4f}, {pass_zs[-1]:.4f}] n={len(pass_zs)}")
print(f"Head.head_z (jaw/joint) = {head_bone.head_local.z:.4f}")
print(
    f"mesh full z range: [{min(v.co.z for v in mesh_obj.data.vertices):.4f}, {max(v.co.z for v in mesh_obj.data.vertices):.4f}]"
)

# Are failing verts close to Head.head_z (the neck/Head joint) specifically?
dist_to_joint = [abs(z - head_bone.head_local.z) for z in fail_zs]
print(
    f"\nfailing verts' distance to Head.head_z joint: min={min(dist_to_joint):.4f} max={max(dist_to_joint):.4f} mean={sum(dist_to_joint)/len(dist_to_joint):.4f}"
)
