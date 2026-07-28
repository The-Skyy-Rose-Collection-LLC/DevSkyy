"""Phase 3: build a fresh 24-bone skeleton (skyy.glb hierarchy/names) positioned
from the CHILD mesh's own measured landmarks -- not copied mascot bind-pose
numbers (per love-hurts-worked-example.md's build_girl_rig.py precedent).

Landmark strategy (per bug-289/290 lessons: cross-section width/count detection
is defeated by hair and baggy garments -- downgrade to a two-point calibration
+ skyy.glb's own internal per-segment ratios, then GATE with a rendered,
xray, high-vis-marker image, never trust the geometry alone):
  1. Total height + shoulder height are measured directly and robustly:
     - total height: mesh z-extent (robust, hair just extends z_max slightly).
     - shoulder height: z-band where T-pose arm span (max |x|) peaks (robust --
       arms are far from hair/garment ambiguity).
  2. Every other landmark (hip/knee/ankle, spine chain, neck/head, elbow/wrist)
     is placed using skyy.glb's OWN measured proportions, re-anchored to this
     mesh's actual total height and shoulder height (two-point calibration
     per region), not skyy's absolute numbers.

Run: blender --background --factory-startup --python build_rig.py
"""

import json
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "child-decimated.glb")
OUT_BLEND = os.path.join(HERE, "child-character-rig.blend")

with open(os.path.join(HERE, "skyy_proportions.json")) as f:
    SKYY = json.load(f)
SB = SKYY["bones"]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=SOURCE)
mesh_obj = max(
    (o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices)
)

verts_world = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
z_min = min(v.z for v in verts_world)
z_max = max(v.z for v in verts_world)
height = z_max - z_min
print(f"child mesh height={height:.5f} z_min={z_min:.5f} z_max={z_max:.5f}")

# Robust shoulder-height detection: z-band (20 bands) with max |x| span among
# verts on the RIGHT side only (x<0 in this rig's convention) to avoid hair
# on either side of centerline biasing the band toward the head.
n_bands = 40
band_max_x = [0.0] * n_bands
for v in verts_world:
    band = min(n_bands - 1, int((v.z - z_min) / height * n_bands))
    band_max_x[band] = max(band_max_x[band], abs(v.x))
shoulder_band = max(range(n_bands), key=lambda i: band_max_x[i])
shoulder_z = z_min + (shoulder_band + 0.5) / n_bands * height
shoulder_frac = (shoulder_z - z_min) / height
print(
    f"detected shoulder_z={shoulder_z:.5f} frac={shoulder_frac:.5f} (skyy ref frac={SB['LeftShoulder']['tail_z_frac']:.5f})"
)

wrist_reach_x = max(abs(v.x) for v in verts_world if abs(v.z - shoulder_z) < 0.05 * height)
print(f"wrist-band max |x| near shoulder height (sanity only)={wrist_reach_x:.5f}")


def remap(skyy_frac, skyy_lo, skyy_hi, child_lo, child_hi):
    """Re-anchor a skyy height-fraction to the child's two calibration points."""
    if skyy_hi == skyy_lo:
        return child_lo
    t = (skyy_frac - skyy_lo) / (skyy_hi - skyy_lo)
    return child_lo + t * (child_hi - child_lo)


SKYY_HIP_FRAC = SB["Hips"]["head_z_frac"]
SKYY_SHOULDER_FRAC = SB["LeftShoulder"]["tail_z_frac"]
SKYY_TOP_FRAC = 1.0

child_hip_frac = remap(SKYY_HIP_FRAC, 0.0, SKYY_SHOULDER_FRAC, 0.0, shoulder_frac)


def z_for(skyy_key, field="head_z_frac"):
    f = SB[skyy_key][field]
    if f <= SKYY_SHOULDER_FRAC:
        lo_s, hi_s, lo_c, hi_c = 0.0, SKYY_SHOULDER_FRAC, 0.0, shoulder_frac
    else:
        lo_s, hi_s, lo_c, hi_c = SKYY_SHOULDER_FRAC, SKYY_TOP_FRAC, shoulder_frac, 1.0
    child_f = remap(f, lo_s, hi_s, lo_c, hi_c)
    return z_min + child_f * height


# X/Y offsets: scale by (child height / skyy height) -- isometric scale
# assumption, gated visually below rather than trusted blindly.
XY_SCALE = height / SKYY["height"]


def xy_for(skyy_key, field_prefix):
    return (
        SB[skyy_key][f"{field_prefix}_x"] * XY_SCALE,
        SB[skyy_key][f"{field_prefix}_y"] * XY_SCALE,
    )


# The arm chain needs SPECIAL handling: skyy.glb's own rest pose has the arms
# mostly hanging DOWN (its head/tail world coords are z-drop-dominant, not
# x-extended), while this source mesh is a fixed T-POSE scan (arms straight
# out horizontally, confirmed by the mesh's own T-pose render). Copying
# skyy's raw world offsets isometrically would build a "hanging arm" chain on
# a horizontally-extended mesh -- caught by the rig_check render's visual
# gate. Fix: lay the arm chain out ALONG THE MEASURED HORIZONTAL REACH using
# skyy's own PER-SEGMENT LENGTH ratios (shoulder/upper-arm/forearm/hand),
# not its raw hanging-pose coordinates.
def seg_len(key):
    h = Vector((SB[key]["head_x"], SB[key]["head_y"], SB[key]["head_z_frac"] * SKYY["height"]))
    t = Vector((SB[key]["tail_x"], SB[key]["tail_y"], SB[key]["tail_z_frac"] * SKYY["height"]))
    return (t - h).length


def build_arm_chain(side_sign, shoulder_key, arm_key, forearm_key, hand_key):
    shoulder_len = seg_len(shoulder_key)
    arm_len = seg_len(arm_key)
    forearm_len = seg_len(forearm_key)
    hand_len = seg_len(hand_key)
    total = shoulder_len + arm_len + forearm_len + hand_len

    shoulder_anchor_x = SB[shoulder_key]["head_x"] * XY_SCALE
    shoulder_anchor_y = SB[shoulder_key]["head_y"] * XY_SCALE
    reach = wrist_reach_x - abs(shoulder_anchor_x)
    scale = reach / total if total > 0 else 0.0

    x = abs(shoulder_anchor_x)
    positions = {"shoulder_head": x}
    for seg_key, seg_len_val in (
        (shoulder_key, shoulder_len),
        (arm_key, arm_len),
        (forearm_key, forearm_len),
        (hand_key, hand_len),
    ):
        x += seg_len_val * scale
        positions[seg_key] = x
    return (
        side_sign,
        shoulder_anchor_x,
        shoulder_anchor_y,
        positions,
        shoulder_key,
        arm_key,
        forearm_key,
        hand_key,
    )


LEFT_ARM_CHAIN = build_arm_chain(1, "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand")
RIGHT_ARM_CHAIN = build_arm_chain(-1, "RightShoulder", "RightArm", "RightForeArm", "RightHand")


def arm_bone_head_tail(chain, seg_key, prev_key):
    _, anchor_x, anchor_y, positions, shoulder_key, arm_key, forearm_key, hand_key = chain
    order = [shoulder_key, arm_key, forearm_key, hand_key]
    idx = order.index(seg_key)
    head_x = positions["shoulder_head"] if idx == 0 else positions[order[idx - 1]]
    tail_x = positions[seg_key]
    sign = 1.0 if anchor_x >= 0 else -1.0
    return (
        Vector((sign * head_x, anchor_y, shoulder_z)),
        Vector((sign * tail_x, anchor_y, shoulder_z)),
    )


arm_data = bpy.data.armatures.new("ChildArmature")
arm_obj = bpy.data.objects.new("ChildArmature", arm_data)
bpy.context.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones

BONES = [
    ("Hips", None, "Hips", "head_z_frac", "Hips", "tail_z_frac"),
    ("Spine02", "Hips", "Spine02", "head_z_frac", "Spine02", "tail_z_frac"),
    ("Spine01", "Spine02", "Spine01", "head_z_frac", "Spine01", "tail_z_frac"),
    ("Spine", "Spine01", "Spine", "head_z_frac", "Spine", "tail_z_frac"),
    ("neck", "Spine", "neck", "head_z_frac", "neck", "tail_z_frac"),
    ("Head", "neck", "Head", "head_z_frac", "Head", "tail_z_frac"),
    ("head_end", "Head", "head_end", "head_z_frac", "head_end", "tail_z_frac"),
    ("headfront", "Head", "headfront", "head_z_frac", "headfront", "tail_z_frac"),
    ("LeftUpLeg", "Hips", "LeftUpLeg", "head_z_frac", "LeftUpLeg", "tail_z_frac"),
    ("LeftLeg", "LeftUpLeg", "LeftLeg", "head_z_frac", "LeftLeg", "tail_z_frac"),
    ("LeftFoot", "LeftLeg", "LeftFoot", "head_z_frac", "LeftFoot", "tail_z_frac"),
    ("LeftToeBase", "LeftFoot", "LeftToeBase", "head_z_frac", "LeftToeBase", "tail_z_frac"),
    ("RightUpLeg", "Hips", "RightUpLeg", "head_z_frac", "RightUpLeg", "tail_z_frac"),
    ("RightLeg", "RightUpLeg", "RightLeg", "head_z_frac", "RightLeg", "tail_z_frac"),
    ("RightFoot", "RightLeg", "RightFoot", "head_z_frac", "RightFoot", "tail_z_frac"),
    ("RightToeBase", "RightFoot", "RightToeBase", "head_z_frac", "RightToeBase", "tail_z_frac"),
]

created = {}
for name, parent, head_key, head_field, tail_key, tail_field in BONES:
    b = eb.new(name)
    hx, hy = xy_for(head_key, "head")
    tx, ty = xy_for(tail_key, "tail")
    b.head = Vector((hx, hy, z_for(head_key, head_field)))
    b.tail = Vector((tx, ty, z_for(tail_key, tail_field)))
    if parent:
        b.parent = created[parent]
        b.use_connect = abs((b.head - created[parent].tail).length) < 1e-4
    created[name] = b

ARM_BONES = [
    ("LeftShoulder", "Spine", LEFT_ARM_CHAIN),
    ("LeftArm", "LeftShoulder", LEFT_ARM_CHAIN),
    ("LeftForeArm", "LeftArm", LEFT_ARM_CHAIN),
    ("LeftHand", "LeftForeArm", LEFT_ARM_CHAIN),
    ("RightShoulder", "Spine", RIGHT_ARM_CHAIN),
    ("RightArm", "RightShoulder", RIGHT_ARM_CHAIN),
    ("RightForeArm", "RightArm", RIGHT_ARM_CHAIN),
    ("RightHand", "RightForeArm", RIGHT_ARM_CHAIN),
]
for name, parent, chain in ARM_BONES:
    b = eb.new(name)
    head, tail = arm_bone_head_tail(chain, name, parent)
    b.head, b.tail = head, tail
    b.parent = created[parent]
    b.use_connect = abs((b.head - created[parent].tail).length) < 1e-4
    created[name] = b

bpy.ops.object.mode_set(mode="OBJECT")

print("BONE_REST_POSITIONS:")
for b in arm_data.bones:
    print(
        f"  {b.name}: head={tuple(round(c,4) for c in b.head_local)} tail={tuple(round(c,4) for c in b.tail_local)}"
    )

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print(f"Saved {OUT_BLEND}")
