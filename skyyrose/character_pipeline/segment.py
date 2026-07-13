"""WS4 — geodesic segmentation: ArmL/ArmR/Body labeling + iterative weld cut.

AI watertight meshes weld touching surfaces (hands to thighs, drawstrings to
wrists). Pants sit euclidean-close to a hanging hand but geodesic-FAR (the
surface path runs up the torso, over the shoulder, down the arm) — multi-source
Dijkstra labeling exploits that gap. The arm-tube filter then catches welded
flaps that are geodesically reachable through the weld itself but sit far
outside the physical arm.

Ports rig_girl.py's validated algorithm (confirmed on Love Hurts Girl: "pass 0:
cut 204 welded bridge triangles / pass 1: converged"), with one generalization:
the reference script's weld-cut gate was an ABSOLUTE `y < 1.05` — that number
only worked because it happened to sit just above THAT model's shoulder height.
Here the gate is `WELD_CUT_SHOULDER_FRACTION * shoulder_y`, the actual
invariant spec section 2 describes ("the only legitimate arm/body boundary is
at the shoulder"), which generalizes to any character height. The seed y-bounds
(reference script's literal 0.50/1.28/0.40/1.35) are likewise re-expressed as
fractions of crotch_y/neck_y/head_y rather than copied as absolute meters.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

from ._geometry import point_segment_distance as _seg_dist
from .config import (
    SEED_ARM_R,
    SEED_BODY_X,
    SHOULDER_BLEND_R,
    TUBE_R,
    WELD_CUT_MAX_PASSES,
    WELD_CUT_SHOULDER_FRACTION,
)
from .convert import PipelineError
from .skeleton import Skeleton

ARM_L, ARM_R, BODY = 0, 1, 2

# Fractions derived from rig_girl.py's validated absolute-meter seed bounds:
# y_lo=0.50/crotch_y(0.64)=0.78125, y_lower_catchall=0.40/0.64=0.625. The upper
# catchall (validated 1.35, between neck_y 1.28 and head_y ~1.38) is computed
# directly as the neck-head midpoint rather than a stored fraction.
_SEED_Y_LO_FRAC = 0.78125
_SEED_Y_LOWER_CATCHALL_FRAC = 0.625


@dataclass
class SegmentResult:
    faces: np.ndarray  # (M,) uint32 flat triangle indices, post weld-cut
    labels: np.ndarray  # (NV,) per-vertex label: ARM_L/ARM_R/BODY
    passes_run: int
    total_cut: int
    converged: bool


def _label_verts(
    V: np.ndarray, F: np.ndarray, seeds: tuple[np.ndarray, np.ndarray, np.ndarray]
) -> np.ndarray:
    """Multi-source Dijkstra: labels every vertex by geodesic proximity to the
    3 seed sets (armL, armR, body). Disconnected islands fall back to body."""
    tri = F.reshape(-1, 3)
    E = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    w = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    nv = len(V)
    rows = [E[:, 0], E[:, 1]]
    cols = [E[:, 1], E[:, 0]]
    wts = [w, w]
    for k, seed_mask in enumerate(seeds):
        s = np.where(seed_mask)[0]
        rows.append(np.full(len(s), nv + k))
        cols.append(s)
        wts.append(np.zeros(len(s)))
    graph = coo_matrix(
        (np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))),
        shape=(nv + 3, nv + 3),
    ).tocsr()
    d = dijkstra(graph, directed=False, indices=[nv, nv + 1, nv + 2])[:, :nv]
    labels = np.argmin(d, axis=0)
    labels[~np.isfinite(d.min(axis=0))] = BODY
    return labels


def _arm_tube_mask(
    V: np.ndarray, sho: np.ndarray, elb: np.ndarray, hnd: np.ndarray, tube_r: float
) -> np.ndarray:
    tip = hnd + np.array([0, -0.14, 0])
    d = np.minimum.reduce([_seg_dist(V, sho, elb), _seg_dist(V, elb, hnd), _seg_dist(V, hnd, tip)])
    return d < tube_r


def segment_mesh(V: np.ndarray, F: np.ndarray, skel: Skeleton) -> SegmentResult:
    """WS4: labels every vertex ArmL/ArmR/Body, iteratively cuts welded
    arm<->body bridge triangles below the shoulder, and re-labels on the cut
    mesh until convergence (or WELD_CUT_MAX_PASSES, which raises loudly).
    """
    idx = {n: i for i, n in enumerate(skel.names)}
    p = skel.positions
    x = V[:, 0]
    crotch_y = float(p[idx["mixamorig:Hips"]][1])
    neck_y = float(p[idx["mixamorig:Neck"]][1])
    head_y = float(p[idx["mixamorig:Head"]][1])

    elb_l, hnd_l, sho_l = (
        p[idx["mixamorig:LeftForeArm"]],
        p[idx["mixamorig:LeftHand"]],
        p[idx["mixamorig:LeftArm"]],
    )
    elb_r, hnd_r, sho_r = (
        p[idx["mixamorig:RightForeArm"]],
        p[idx["mixamorig:RightHand"]],
        p[idx["mixamorig:RightArm"]],
    )

    arm_x_gate = SHOULDER_BLEND_R  # 0.13m — matches the reference script's validated arm-seed gate
    seed_arm_l = (_seg_dist(V, elb_l, hnd_l) < SEED_ARM_R) & (x > arm_x_gate)
    seed_arm_l |= (_seg_dist(V, sho_l + (elb_l - sho_l) * 0.35, elb_l) < SEED_ARM_R) & (
        x > arm_x_gate
    )
    seed_arm_r = (_seg_dist(V, elb_r, hnd_r) < SEED_ARM_R) & (x < -arm_x_gate)
    seed_arm_r |= (_seg_dist(V, sho_r + (elb_r - sho_r) * 0.35, elb_r) < SEED_ARM_R) & (
        x < -arm_x_gate
    )

    y_lo = _SEED_Y_LO_FRAC * crotch_y
    y_lower_catchall = _SEED_Y_LOWER_CATCHALL_FRAC * crotch_y
    y_upper_catchall = (neck_y + head_y) / 2
    seed_body = (
        ((np.abs(x) < SEED_BODY_X) & (V[:, 1] > y_lo) & (V[:, 1] < neck_y))
        | (V[:, 1] < y_lower_catchall)
        | (V[:, 1] > y_upper_catchall)
    )
    seed_body &= ~(seed_arm_l | seed_arm_r)

    tube_l = _arm_tube_mask(V, sho_l, elb_l, hnd_l, TUBE_R)
    tube_r = _arm_tube_mask(V, sho_r, elb_r, hnd_r, TUBE_R)

    def filtered_labels(faces: np.ndarray) -> np.ndarray:
        labels = _label_verts(V, faces, (seed_arm_l, seed_arm_r, seed_body))
        labels[(labels == ARM_L) & ~tube_l] = BODY
        labels[(labels == ARM_R) & ~tube_r] = BODY
        return labels

    shoulder_y = max(float(sho_l[1]), float(sho_r[1]))
    cut_gate_y = WELD_CUT_SHOULDER_FRACTION * shoulder_y

    faces = F.copy()
    total_cut = 0
    converged = False
    passes_run = 0
    for it in range(WELD_CUT_MAX_PASSES):
        passes_run = it + 1
        labels = filtered_labels(faces)
        tri = faces.reshape(-1, 3)
        tri_labels = labels[tri]
        mixed = (tri_labels == BODY).any(1) & ((tri_labels == ARM_L) | (tri_labels == ARM_R)).any(1)
        low = V[tri].mean(1)[:, 1] < cut_gate_y
        cut = mixed & low
        if not cut.any():
            converged = True
            break
        total_cut += int(cut.sum())
        faces = tri[~cut].reshape(-1).astype(np.uint32)

    if not converged:
        raise PipelineError(
            f"weld-cut did not converge within {WELD_CUT_MAX_PASSES} passes "
            f"({total_cut} triangles cut so far) — inspect the mesh for a bridge "
            "the arm-tube filter can't isolate"
        )

    final_labels = filtered_labels(faces)
    return SegmentResult(
        faces=faces,
        labels=final_labels,
        passes_run=passes_run,
        total_cut=total_cut,
        converged=converged,
    )
