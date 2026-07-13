"""WS6 — hard verification gate: pure-numpy LBS forward kinematics + QA renders.

Formalizes the ad-hoc heredoc poses from the validated session into named pose
gates (wave_R, wave_L, bow, look) with numeric assertions that exit nonzero on
failure — the actual gate, not the rendered images (those are for human review
only). No engine dependency: FK is composed by hand (local rotations down the
joint hierarchy -> world matrices -> skin_matrix = world @ inverse_bind ->
deform), matching what three.js's AnimationMixer + SkinnedMesh do at runtime,
so a passing gate here is a real guarantee about the shipped GLB.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from pygltflib import GLTF2

from . import _glb_io
from ._geometry import point_segment_distance, rotation_matrix
from .config import GATE, HAIR_Y_GAP_FRAC, SEED_BODY_X
from .convert import PipelineError
from .segment import ARM_L, ARM_R
from .skeleton import Skeleton

NON_ARM_EXCLUSION_R = (
    0.11  # slightly more generous than segment.py's TUBE_R (0.10), avoids boundary flakiness
)

_POSES: dict[str, dict[str, list[tuple[str, float]]]] = {
    "wave_R": {"mixamorig:RightArm": [("z", -1.15)], "mixamorig:RightForeArm": [("z", -0.35)]},
    "wave_L": {"mixamorig:LeftArm": [("z", 1.15)], "mixamorig:LeftForeArm": [("z", 0.35)]},
    "bow": {"mixamorig:Spine1": [("x", 0.35)]},
    "look": {"mixamorig:Head": [("y", 0.30)]},
}


class GateFailure(PipelineError):
    """Raised when a WS6 pose gate fails. `@dataclass` is deliberately NOT used
    here — decorating an Exception subclass replaces its `__init__`, which
    breaks positional-message + keyword-attribute construction (`GateFailure(msg,
    metric=..., value=..., threshold=...)` would bind `msg` to `metric` and then
    collide with the explicit `metric=` keyword)."""

    def __init__(self, message: str, *, metric: str, value: float, threshold: float) -> None:
        super().__init__(message)
        self.metric = metric
        self.value = value
        self.threshold = threshold


def _local_matrices(
    skel: Skeleton, pose_rotations: dict[str, list[tuple[str, float]]]
) -> np.ndarray:
    nj = len(skel.names)
    mats = np.zeros((nj, 4, 4))
    for i in range(nj):
        local_t = skel.positions[i] - (
            skel.positions[skel.parents[i]] if skel.parents[i] >= 0 else np.zeros(3)
        )
        r = np.eye(3)
        for axis, angle in pose_rotations.get(skel.names[i], []):
            r = rotation_matrix(axis, angle) @ r
        m = np.eye(4)
        m[:3, :3] = r
        m[:3, 3] = local_t
        mats[i] = m
    return mats


def _world_matrices(skel: Skeleton, local_mats: np.ndarray) -> np.ndarray:
    """Assumes joints are topologically sorted (parent index < child index),
    which build_skeleton() guarantees by construction."""
    nj = len(skel.names)
    world = np.zeros((nj, 4, 4))
    for i in range(nj):
        world[i] = local_mats[i] if skel.parents[i] < 0 else world[skel.parents[i]] @ local_mats[i]
    return world


def _skin_matrices(
    skel: Skeleton, pose_rotations: dict[str, list[tuple[str, float]]]
) -> np.ndarray:
    world = _world_matrices(skel, _local_matrices(skel, pose_rotations))
    nj = len(skel.names)
    ibm = np.zeros((nj, 4, 4))
    for i in range(nj):
        m = np.eye(4)
        m[:3, 3] = -skel.positions[i]
        ibm[i] = m
    return np.einsum("nij,njk->nik", world, ibm)


def deform(
    V: np.ndarray, joints4: np.ndarray, weights4: np.ndarray, skin_mats: np.ndarray
) -> np.ndarray:
    """Applies linear blend skinning under the given per-joint skin matrices."""
    homog = np.concatenate([V, np.ones((len(V), 1))], axis=1)
    out = np.zeros((len(V), 3))
    for k in range(joints4.shape[1]):
        j = joints4[:, k]
        w = weights4[:, k]
        transformed = np.einsum("nij,nj->ni", skin_mats[j], homog)[:, :3]
        out += w[:, None] * transformed
    return out


def _check(name: str, value: float, threshold: float, op: str) -> dict:
    passed = value <= threshold if op == "<=" else value >= threshold
    return {
        "metric": name,
        "value": float(value),
        "threshold": float(threshold),
        "op": op,
        "pass": bool(passed),
    }


def _build_masks(V: np.ndarray, skel: Skeleton) -> dict:
    idx = {n: i for i, n in enumerate(skel.names)}
    p = skel.positions
    neck_y = float(p[idx["mixamorig:Neck"]][1])
    crotch_y = float(p[idx["mixamorig:Hips"]][1])
    height = float(V[:, 1].max())
    hair = V[:, 1] > neck_y + HAIR_Y_GAP_FRAC * height
    torso_column = (np.abs(V[:, 0]) < SEED_BODY_X) & (V[:, 1] > crotch_y) & (V[:, 1] < neck_y)

    def tube_dist(side: str) -> np.ndarray:
        sho, elb, hnd = (
            p[idx[f"mixamorig:{side}Arm"]],
            p[idx[f"mixamorig:{side}ForeArm"]],
            p[idx[f"mixamorig:{side}Hand"]],
        )
        tip = hnd + np.array(
            [0, -0.14, 0]
        )  # matches segment.py's (unscaled) arm-tube tip offset exactly
        return np.minimum.reduce(
            [
                point_segment_distance(V, sho, elb),
                point_segment_distance(V, elb, hnd),
                point_segment_distance(V, hnd, tip),
            ]
        )

    return {
        "neck_y": neck_y,
        "crotch_y": crotch_y,
        "hair": hair,
        "torso_column": torso_column,
        "shoulder_l_y": float(p[idx["mixamorig:LeftArm"]][1]),
        "shoulder_r_y": float(p[idx["mixamorig:RightArm"]][1]),
        "dist_tube_l": tube_dist("Left"),
        "dist_tube_r": tube_dist("Right"),
    }


def _gate_wave(
    masks: dict, V: np.ndarray, seg_labels: np.ndarray, disp: np.ndarray, side: str
) -> list[dict]:
    arm_label = ARM_R if side == "R" else ARM_L
    shoulder_y = masks[f"shoulder_{side.lower()}_y"]
    dist_tube = masks[f"dist_tube_{side.lower()}"]
    x_sign = (V[:, 0] < 0) if side == "R" else (V[:, 0] > 0)
    non_arm_side = (
        (seg_labels != arm_label)
        & x_sign
        & (V[:, 1] < shoulder_y)
        & (dist_tube > NON_ARM_EXCLUSION_R)
    )
    arm_tube = seg_labels == arm_label
    return [
        _check(
            f"wave_{side}.non_arm_side_max_disp",
            disp[non_arm_side].max() if non_arm_side.any() else 0.0,
            GATE["static_max_disp"],
            "<=",
        ),
        _check(
            f"wave_{side}.arm_tube_mean_disp",
            disp[arm_tube].mean() if arm_tube.any() else 0.0,
            GATE["arm_min_mean_disp"],
            ">=",
        ),
        _check(
            f"wave_{side}.hair_max_disp",
            disp[masks["hair"]].max() if masks["hair"].any() else 0.0,
            GATE["static_max_disp"],
            "<=",
        ),
        _check(
            f"wave_{side}.torso_column_max_disp",
            disp[masks["torso_column"]].max() if masks["torso_column"].any() else 0.0,
            GATE["static_max_disp"],
            "<=",
        ),
    ]


def _gate_bow(skel: Skeleton, weights_joints: np.ndarray, disp: np.ndarray) -> list[dict]:
    idx = {n: i for i, n in enumerate(skel.names)}
    dominant = weights_joints[:, 0]
    foot_idx = [
        idx[n]
        for n in (
            "mixamorig:LeftFoot",
            "mixamorig:LeftToeBase",
            "mixamorig:LeftToe_End",
            "mixamorig:RightFoot",
            "mixamorig:RightToeBase",
            "mixamorig:RightToe_End",
        )
    ]
    head_idx = [idx["mixamorig:Head"], idx["mixamorig:HeadTop_End"]]
    feet_mask = np.isin(dominant, foot_idx)
    head_mask = np.isin(dominant, head_idx)
    return [
        _check(
            "bow.feet_max_disp",
            disp[feet_mask].max() if feet_mask.any() else 0.0,
            GATE["static_max_disp"],
            "<=",
        ),
        _check(
            "bow.head_mean_disp", disp[head_mask].mean() if head_mask.any() else 0.0, 0.15, ">="
        ),
    ]


def _gate_look(masks: dict, V: np.ndarray, disp: np.ndarray) -> list[dict]:
    below_neck = V[:, 1] < masks["neck_y"]
    return [
        _check(
            "look.below_neck_max_disp",
            disp[below_neck].max() if below_neck.any() else 0.0,
            GATE["static_max_disp"],
            "<=",
        )
    ]


def render_qa_png(
    V: np.ndarray,
    F: np.ndarray,
    out_path: str | Path,
    light_dir: tuple[float, float, float] = (0.4, 0.6, 0.7),
) -> None:
    """Front-view matplotlib PolyCollection painter's-algorithm render: backface
    cull (n_z>0), depth-sort far-to-near, lambert shade. Human-review artifact —
    the numeric gates above are the actual pass/fail decision.
    """
    tri = V[F.reshape(-1, 3)]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
    front = normals[:, 2] > 0
    tri, normals = tri[front], normals[front]
    order = np.argsort(tri.mean(1)[:, 2])  # far (smaller z) drawn first
    tri, normals = tri[order], normals[order]
    light = np.array(light_dir)
    light = light / np.linalg.norm(light)
    shade = np.clip(normals @ light, 0.15, 1.0)
    colors = np.stack([shade, shade, shade], axis=1)

    fig, ax = plt.subplots(figsize=(4, 6), dpi=100)
    ax.add_collection(PolyCollection(tri[:, :, :2], facecolors=colors, edgecolors="none"))
    ax.set_xlim(float(V[:, 0].min()) - 0.1, float(V[:, 0].max()) + 0.1)
    ax.set_ylim(float(V[:, 1].min()) - 0.1, float(V[:, 1].max()) + 0.1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(str(out_path), bbox_inches="tight", facecolor="black")
    plt.close(fig)


def _read_skeleton_from_glb(gltf: GLTF2, blob: bytes) -> Skeleton:
    """Reconstructs a Skeleton from a rigged GLB's Skin — used when verify runs
    standalone (`devskyy-character verify <rigged.glb>`) without an in-memory
    Skeleton from earlier workstreams."""
    skin = gltf.skins[0]
    joint_nodes = skin.joints
    ibm = (
        _glb_io.read_accessor(gltf, blob, skin.inverseBindMatrices)
        .astype(np.float64)
        .reshape(-1, 4, 4)
    )
    positions = -ibm.transpose(0, 2, 1)[:, :3, 3]
    names = [gltf.nodes[i].name for i in joint_nodes]
    node_to_local = {node_idx: i for i, node_idx in enumerate(joint_nodes)}
    parents = []
    for node_idx in joint_nodes:
        parent_local = -1
        for candidate_idx, node in enumerate(gltf.nodes):
            if node.children and node_idx in node.children:
                parent_local = node_to_local.get(candidate_idx, -1)
                break
        parents.append(parent_local)
    return Skeleton(names=names, parents=parents, positions=positions)


@dataclass
class VerifyReport:
    all_passed: bool
    gates: list[dict] = field(default_factory=list)
    round_trip: dict = field(default_factory=dict)


def verify_character(rigged_glb_path: str | Path, qa_dir: str | Path) -> VerifyReport:
    """WS6: runs every pose gate against the rigged GLB, renders a QA PNG per
    pose, and returns the full report. Raises GateFailure on the first failed
    assertion after writing the report — callers should write `report` to
    disk before re-raising so a failed run still leaves the evidence behind.
    """
    qa_dir = Path(qa_dir)
    qa_dir.mkdir(parents=True, exist_ok=True)

    gltf = GLTF2().load(str(rigged_glb_path))
    blob = gltf.binary_blob()
    prim = gltf.meshes[0].primitives[0]
    V = _glb_io.read_accessor(gltf, blob, prim.attributes.POSITION).astype(np.float64)
    F = _glb_io.read_accessor(gltf, blob, prim.indices).astype(np.uint32)
    joints4 = _glb_io.read_accessor(gltf, blob, prim.attributes.JOINTS_0).astype(np.int64)
    weights4 = _glb_io.read_accessor(gltf, blob, prim.attributes.WEIGHTS_0).astype(np.float64)
    skel = _read_skeleton_from_glb(gltf, blob)

    # seg_labels: recovered from JOINTS_0's dominant-joint arm assignment, since
    # the raw WS4 vertex labels aren't persisted in the GLB itself.
    idx = {n: i for i, n in enumerate(skel.names)}
    arm_joint_l = {
        idx[n] for n in skel.names if "Left" in n and ("Arm" in n or "Hand" in n or "Shoulder" in n)
    }
    arm_joint_r = {
        idx[n]
        for n in skel.names
        if "Right" in n and ("Arm" in n or "Hand" in n or "Shoulder" in n)
    }
    dominant = joints4[:, 0]
    seg_labels = np.full(len(V), 2)  # BODY default (ARM_L=0, ARM_R=1, BODY=2 — mirrors segment.py)
    seg_labels[np.isin(dominant, list(arm_joint_l))] = ARM_L
    seg_labels[np.isin(dominant, list(arm_joint_r))] = ARM_R

    masks = _build_masks(V, skel)

    gates: list[dict] = []
    for pose_name, rotations in _POSES.items():
        skin_mats = _skin_matrices(skel, rotations)
        deformed = deform(V, joints4, weights4, skin_mats)
        disp = np.linalg.norm(deformed - V, axis=1)
        render_qa_png(deformed, F, qa_dir / f"{pose_name}.png")
        if pose_name in ("wave_R", "wave_L"):
            gates.extend(_gate_wave(masks, V, seg_labels, disp, pose_name[-1]))
        elif pose_name == "bow":
            gates.extend(_gate_bow(skel, joints4, disp))
        elif pose_name == "look":
            gates.extend(_gate_look(masks, V, disp))

    raw = Path(rigged_glb_path).read_bytes()
    b64 = base64.b64encode(raw).decode()
    round_trip = {
        "reload_ok": bool(gltf.meshes and gltf.meshes[0].primitives),
        "texture_last": gltf.images[0].bufferView == len(gltf.bufferViews) - 1,
        "base64_roundtrip_ok": base64.b64decode(b64) == raw,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    gates.append(
        _check("round_trip.texture_last", 1.0 if round_trip["texture_last"] else 0.0, 1.0, ">=")
    )
    gates.append(
        _check(
            "round_trip.base64_roundtrip_ok",
            1.0 if round_trip["base64_roundtrip_ok"] else 0.0,
            1.0,
            ">=",
        )
    )

    all_passed = all(g["pass"] for g in gates)
    report = VerifyReport(all_passed=all_passed, gates=gates, round_trip=round_trip)
    (qa_dir / "verify_report.json").write_text(
        json.dumps({"all_passed": all_passed, "gates": gates, "round_trip": round_trip}, indent=2)
    )

    if not all_passed:
        failed = next(g for g in gates if not g["pass"])
        raise GateFailure(
            f"WS6 verification failed: {failed['metric']}={failed['value']:.5f} "
            f"({failed['op']} {failed['threshold']} required)",
            metric=failed["metric"],
            value=failed["value"],
            threshold=failed["threshold"],
        )
    return report
