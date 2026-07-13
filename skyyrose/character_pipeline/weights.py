"""WS5 — capsule-based LBS weight solve + rigged GLB assembly.

Radius-normalized point-to-segment distance (`dn = distance/bone.radius;
w = 1/(dn**4+1e-6)`) prevents thin bones from outcompeting thick ones purely
because they're numerically closer — a flat inverse-distance falloff would let
the afro (large radius) lose weight to a nearby thin neck bone. Region masks
(arm/body/hair/leg-side gates) come from WS4's segmentation labels. Ports
rig_girl.py's validated weight solve and IBM/skin export, with bone radii and
every mask threshold scaled to the character's own detected height instead of
hardcoded to Love Hurts Girl's 1.911m.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from pygltflib import (
    ARRAY_BUFFER,
    ELEMENT_ARRAY_BUFFER,
    GLTF2,
    Asset,
    Attributes,
    Buffer,
)
from pygltflib import Image as GImage
from pygltflib import (
    Material,
    Mesh,
    Node,
    PbrMetallicRoughness,
    Primitive,
    Sampler,
    Scene,
    Skin,
    Texture,
    TextureInfo,
)

from . import _glb_io
from ._geometry import point_segment_distance as _point_segment_distance
from .config import (
    HAIR_Y_GAP_FRAC,
    LEG_SIDE_GATE_FRAC,
    MAX_INFLUENCES,
    PBR,
    REFERENCE_HEIGHT,
    SHOULDER_BLEND_R,
    TORSO_COLUMN_Y_LO_FRAC,
    WEIGHT_FALLOFF_POW,
    CharacterConfig,
)
from .segment import ARM_L, ARM_R, SegmentResult
from .skeleton import Skeleton

# (start_joint, end_joint, radius_key) — every weight-bearing bone segment.
# Leaf joints (HeadTop_End, Toe_End) bear no weight; hands extend past the
# wrist below.
_BONE_SEGMENTS = [
    ("mixamorig:Hips", "mixamorig:Spine", "Hips"),
    ("mixamorig:Spine", "mixamorig:Spine1", "Spine"),
    ("mixamorig:Spine1", "mixamorig:Spine2", "Spine1"),
    ("mixamorig:Spine2", "mixamorig:Neck", "Spine2"),
    ("mixamorig:Neck", "mixamorig:Head", "Neck"),
    ("mixamorig:Head", "mixamorig:HeadTop_End", "Head"),
    ("mixamorig:LeftShoulder", "mixamorig:LeftArm", "Shoulder"),
    ("mixamorig:LeftArm", "mixamorig:LeftForeArm", "Arm"),
    ("mixamorig:LeftForeArm", "mixamorig:LeftHand", "ForeArm"),
    ("mixamorig:RightShoulder", "mixamorig:RightArm", "Shoulder"),
    ("mixamorig:RightArm", "mixamorig:RightForeArm", "Arm"),
    ("mixamorig:RightForeArm", "mixamorig:RightHand", "ForeArm"),
    ("mixamorig:LeftUpLeg", "mixamorig:LeftLeg", "UpLeg"),
    ("mixamorig:LeftLeg", "mixamorig:LeftFoot", "Leg"),
    ("mixamorig:LeftFoot", "mixamorig:LeftToeBase", "Foot"),
    ("mixamorig:LeftToeBase", "mixamorig:LeftToe_End", "Toe"),
    ("mixamorig:RightUpLeg", "mixamorig:RightLeg", "UpLeg"),
    ("mixamorig:RightLeg", "mixamorig:RightFoot", "Leg"),
    ("mixamorig:RightFoot", "mixamorig:RightToeBase", "Foot"),
    ("mixamorig:RightToeBase", "mixamorig:RightToe_End", "Toe"),
]
_HAND_EXTENSION_FRAC = 0.13 / REFERENCE_HEIGHT  # 13cm past the wrist, on the reference model


@dataclass
class WeightsResult:
    joints: np.ndarray  # (NV,4) uint8
    weights: np.ndarray  # (NV,4) float32
    dead_vert_count: int
    coverage: dict[str, int] = field(default_factory=dict)


def _region_masks(
    V: np.ndarray, skel: Skeleton, seg: SegmentResult, bone_joint_names: list[str], height: float
) -> np.ndarray:
    idx = {n: i for i, n in enumerate(skel.names)}
    p = skel.positions
    y, x = V[:, 1], V[:, 0]
    nv, nb = len(V), len(bone_joint_names)

    is_armb = np.array(["Arm" in n or "Hand" in n or "Shoulder" in n for n in bone_joint_names])
    is_left = np.array(["Left" in n for n in bone_joint_names])
    is_right = np.array(["Right" in n for n in bone_joint_names])
    is_leg = np.array(["Leg" in n or "Foot" in n or "Toe" in n for n in bone_joint_names])
    is_headchain = np.array([n in ("mixamorig:Neck", "mixamorig:Head") for n in bone_joint_names])
    is_head_only = np.array(
        [n in ("mixamorig:Head", "mixamorig:HeadTop_End") for n in bone_joint_names]
    )

    sho_l, sho_r = p[idx["mixamorig:LeftArm"]], p[idx["mixamorig:RightArm"]]
    blend_l = np.linalg.norm(V - sho_l, axis=1) < SHOULDER_BLEND_R
    blend_r = np.linalg.norm(V - sho_r, axis=1) < SHOULDER_BLEND_R
    arm_l_v = seg.labels == ARM_L
    arm_r_v = seg.labels == ARM_R

    allowed = np.ones((nv, nb), bool)
    allowed[:, is_armb & is_left] &= (arm_l_v | blend_l)[:, None]
    allowed[:, is_armb & is_right] &= (arm_r_v | blend_r)[:, None]
    allowed[:, ~is_armb] &= (~(arm_l_v | arm_r_v) | blend_l | blend_r)[:, None]

    neck_y = float(p[idx["mixamorig:Neck"]][1])
    hair = y > neck_y + HAIR_Y_GAP_FRAC * height
    allowed[hair] = False
    allowed[np.ix_(hair, is_headchain)] = True

    # Head/HeadTop_End carry an oversized radius (the afro) so their radius-normalized
    # reach can otherwise out-compete much-closer Spine bones for torso verts far below
    # the neck (dn=distance/radius lets a big-radius-but-farther bone win). Every other
    # bone group (arm, leg) already has an explicit region gate; Head needs the same:
    # it may only influence verts at or above the neck, never chest/torso geometry.
    allowed[:, is_head_only] &= (y >= neck_y)[:, None]

    crotch_y = float(p[idx["mixamorig:Hips"]][1])
    leg_territory_y = TORSO_COLUMN_Y_LO_FRAC * crotch_y
    below = (y < leg_territory_y) & ~(arm_l_v | arm_r_v)
    allowed[np.ix_(below, ~is_leg)] = False
    gate = LEG_SIDE_GATE_FRAC * height
    allowed[:, is_leg & is_left] &= (x > -gate)[:, None]
    allowed[:, is_leg & is_right] &= (x < gate)[:, None]

    return allowed


def solve_weights(
    V: np.ndarray, skel: Skeleton, seg: SegmentResult, config: CharacterConfig | None = None
) -> WeightsResult:
    """WS5: radius-normalized capsule LBS weights over every weight-bearing
    bone segment, region-masked by WS4's arm/body labels, top-4 normalized.
    """
    config = config or CharacterConfig()
    idx = {n: i for i, n in enumerate(skel.names)}
    p = skel.positions
    height = float(V[:, 1].max())
    nv = len(V)

    bone_joint_idx: list[int] = []
    bone_joint_names: list[str] = []
    seg_a, seg_b, radii = [], [], []
    for start, end, radius_key in _BONE_SEGMENTS:
        bone_joint_idx.append(idx[start])
        bone_joint_names.append(start)
        seg_a.append(p[idx[start]])
        seg_b.append(p[idx[end]])
        radii.append(config.bone_radius(radius_key, height))
    for hand_joint in ("mixamorig:LeftHand", "mixamorig:RightHand"):
        a = p[idx[hand_joint]]
        end = a + np.array([0.0, -_HAND_EXTENSION_FRAC * height, 0.0])
        bone_joint_idx.append(idx[hand_joint])
        bone_joint_names.append(hand_joint)
        seg_a.append(a)
        seg_b.append(end)
        radii.append(config.bone_radius("Hand", height))

    bone_joint = np.array(bone_joint_idx)
    a_arr, b_arr, r_arr = np.stack(seg_a), np.stack(seg_b), np.array(radii)
    nb = len(bone_joint)

    allowed = _region_masks(V, skel, seg, bone_joint_names, height)

    w_full = np.zeros((nv, nb))
    for bi in range(nb):
        d = _point_segment_distance(V, a_arr[bi], b_arr[bi])
        dn = d / r_arr[bi]
        w_full[:, bi] = 1.0 / (dn**WEIGHT_FALLOFF_POW + 1e-6)
    w_full[~allowed] = 0.0

    dead = w_full.sum(1) == 0
    dead_count = int(dead.sum())
    if dead.any():
        midpoints = (a_arr + b_arr) / 2
        for vi in np.where(dead)[0]:
            d = np.linalg.norm(V[vi] - midpoints, axis=1)
            w_full[vi, np.argmin(d)] = 1.0

    top4 = np.argsort(-w_full, axis=1)[:, :MAX_INFLUENCES]
    w4 = np.take_along_axis(w_full, top4, axis=1)
    w4 = w4 / w4.sum(1, keepdims=True)
    j4 = bone_joint[top4].astype(np.uint8)
    w4 = w4.astype(np.float32)

    strong = w4 > 0.1
    coverage: dict[str, int] = {}
    for k in range(MAX_INFLUENCES):
        for joint_i in j4[:, k][strong[:, k]]:
            name = skel.names[int(joint_i)]
            coverage[name] = coverage.get(name, 0) + 1

    return WeightsResult(joints=j4, weights=w4, dead_vert_count=dead_count, coverage=coverage)


def write_rigged_glb(
    clean_glb_path: str | Path,
    V: np.ndarray,
    F: np.ndarray,
    skel: Skeleton,
    weights: WeightsResult,
    out_path: str | Path,
) -> Path:
    """Writes the final skinned GLB: joint node tree (local translations),
    column-major inverse bind matrices, Skin, and skinned mesh — reusing the
    UV/material/texture already finalized by WS2's clean GLB.
    """
    clean = GLTF2().load(str(clean_glb_path))
    blob = clean.binary_blob()
    prim = clean.meshes[0].primitives[0]
    N = _glb_io.read_accessor(clean, blob, prim.attributes.NORMAL).astype(np.float32)
    UV = _glb_io.read_accessor(clean, blob, prim.attributes.TEXCOORD_0).astype(np.float32)
    tex_bytes = _glb_io.image_bytes(clean, blob, 0)

    nj = len(skel.names)
    p = skel.positions
    ibm = np.zeros((nj, 4, 4), dtype=np.float32)
    for i in range(nj):
        m = np.eye(4, dtype=np.float32)
        m[:3, 3] = -p[i]
        ibm[i] = m
    ibm_gltf = ibm.transpose(0, 2, 1).copy()  # glTF stores matrices column-major

    children: dict[int, list[int]] = {i: [] for i in range(nj)}
    for i, parent in enumerate(skel.parents):
        if parent >= 0:
            children[parent].append(i)
    nodes = []
    for i in range(nj):
        local = p[i] - (p[skel.parents[i]] if skel.parents[i] >= 0 else np.zeros(3))
        nodes.append(
            Node(name=skel.names[i], translation=local.tolist(), children=children[i] or None)
        )
    mesh_node_index = len(nodes)
    nodes.append(Node(name="CharacterMesh", mesh=0, skin=0))

    v32 = V.astype(np.float32)
    writer = _glb_io.GLBWriter()
    a_pos = writer.add_accessor(
        v32.tobytes(),
        ARRAY_BUFFER,
        5126,
        len(v32),
        "VEC3",
        (v32.min(0).tolist(), v32.max(0).tolist()),
    )
    a_nrm = writer.add_accessor(N.tobytes(), ARRAY_BUFFER, 5126, len(N), "VEC3")
    a_uv = writer.add_accessor(UV.tobytes(), ARRAY_BUFFER, 5126, len(UV), "VEC2")
    a_jnt = writer.add_accessor(
        weights.joints.tobytes(), ARRAY_BUFFER, 5121, len(weights.joints), "VEC4"
    )
    a_wgt = writer.add_accessor(
        weights.weights.tobytes(), ARRAY_BUFFER, 5126, len(weights.weights), "VEC4"
    )
    a_idx = writer.add_accessor(
        F.astype(np.uint32).tobytes(), ELEMENT_ARRAY_BUFFER, 5125, len(F), "SCALAR"
    )
    a_ibm = writer.add_accessor(ibm_gltf.tobytes(), None, 5126, nj, "MAT4")
    img_view = writer.add_image(tex_bytes)  # texture LAST — enables package.py's surgical swap
    bin_blob = writer.finalize()

    out = GLTF2(
        asset=Asset(version="2.0", generator="SkyyRose character_pipeline"),
        scenes=[Scene(nodes=[0, mesh_node_index])],
        scene=0,
        nodes=nodes,
        meshes=[
            Mesh(
                name="CharacterMesh",
                primitives=[
                    Primitive(
                        attributes=Attributes(
                            POSITION=a_pos,
                            NORMAL=a_nrm,
                            TEXCOORD_0=a_uv,
                            JOINTS_0=a_jnt,
                            WEIGHTS_0=a_wgt,
                        ),
                        indices=a_idx,
                        material=0,
                    )
                ],
            )
        ],
        skins=[
            Skin(
                name="CharacterSkin", inverseBindMatrices=a_ibm, joints=list(range(nj)), skeleton=0
            )
        ],
        materials=[
            Material(
                name="CharacterMesh_mat",
                pbrMetallicRoughness=PbrMetallicRoughness(
                    baseColorTexture=TextureInfo(index=0),
                    metallicFactor=PBR["metallic"],
                    roughnessFactor=PBR["roughness"],
                ),
                doubleSided=False,
            )
        ],
        textures=[Texture(source=0, sampler=0)],
        samplers=[Sampler(magFilter=9729, minFilter=9987, wrapS=10497, wrapT=10497)],
        images=[GImage(name="BaseColor", mimeType="image/jpeg", bufferView=img_view)],
        buffers=[Buffer(byteLength=len(bin_blob))],
        bufferViews=writer.views,
        accessors=writer.accessors,
    )
    out.set_binary_blob(bin_blob)
    out_path = Path(out_path)
    out.save(str(out_path))
    return out_path
