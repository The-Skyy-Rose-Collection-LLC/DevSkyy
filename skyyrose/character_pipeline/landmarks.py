"""WS3a — landmark auto-detection via Y-axis slice clustering.

Generalizes rig_girl.py's hardcoded absolute-meter measurements (its bands
were literally where THIS model's hips/shoulders/hands happened to sit at
1.911m tall) into height-normalized detection: Y-bands scale with detected
mesh height (the spec's `H`-suffixed fractions); X/Z point-distance gates and
scan resolution stay fixed absolute meters, matching every other constant in
config.py's registry (only BONE_RADII scale with height — spec section 3/5).
`character.yaml` overrides win over auto-detection for any individual field.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import (
    CLUSTER_GAP,
    LANDMARK_BANDS_FRAC,
    LANDMARK_X_GATE_CHEST,
    LANDMARK_X_GATE_FOOT,
    LANDMARK_X_GATE_FOOT_MIN,
    LANDMARK_X_GATE_HAND,
    LANDMARK_X_GATE_SHOULDER,
    SLICE_BAND_THICKNESS,
    SLICE_STEP,
    CharacterConfig,
)
from .convert import PipelineError


@dataclass
class Landmarks:
    height: float
    crotch_y: float
    z_hip: float
    z_chest: float
    z_head: float
    z_foot_l: np.ndarray
    z_foot_r: np.ndarray
    shoulder_l: np.ndarray
    shoulder_r: np.ndarray
    hand_l: np.ndarray
    hand_r: np.ndarray
    neck_y: float


def _cluster_1d(idx_sorted: np.ndarray, x_sorted: np.ndarray, gap: float) -> list[np.ndarray]:
    """Splits an x-sorted index array into clusters wherever the gap between
    consecutive x-values exceeds `gap` (CLUSTER_GAP)."""
    if len(idx_sorted) == 0:
        return []
    breaks = np.where(np.diff(x_sorted) > gap)[0] + 1
    return [group for group in np.split(idx_sorted, breaks) if len(group) > 0]


def _band_clusters(
    V: np.ndarray, y0: float, y1: float, x_abs_gate: float | None = None
) -> list[np.ndarray]:
    """Vert indices within Y band [y0,y1), optionally pre-filtered to |x|>x_abs_gate, clustered by x-gap."""
    mask = (V[:, 1] >= y0) & (V[:, 1] < y1)
    if x_abs_gate is not None:
        mask &= np.abs(V[:, 0]) > x_abs_gate
    idx = np.where(mask)[0]
    if len(idx) < 5:
        return []
    order = np.argsort(V[idx, 0])
    return _cluster_1d(idx[order], V[idx[order], 0], CLUSTER_GAP)


def _find_crotch_y(V: np.ndarray, height: float) -> float:
    """Highest Y in the lower half where the slice splits into exactly 2 leg clusters."""
    best = 0.0
    for y0 in np.arange(0.0, 0.5 * height, SLICE_STEP):
        if len(_band_clusters(V, y0, y0 + SLICE_BAND_THICKNESS)) == 2:
            best = max(best, float(y0))
    if best == 0.0:
        raise PipelineError(
            "could not detect crotch_y: no band in the lower half split into exactly 2 clusters"
        )
    return best


def _outer_cluster(V: np.ndarray, clusters: list[np.ndarray], side: str) -> np.ndarray:
    """Vert indices of the cluster whose mean |x| is largest on `side` ('left'=+x, 'right'=-x)."""
    side_clusters = [c for c in clusters if (V[c, 0].mean() > 0) == (side == "left")]
    if not side_clusters:
        raise PipelineError(f"no {side} cluster found in band")
    return max(side_clusters, key=lambda c: abs(V[c, 0].mean()))


def _find_neck_y(V: np.ndarray, shoulder_y: float, head_band_y0: float) -> float:
    """Narrowest single-cluster band between the shoulders and the head/hair mass."""
    best_y, best_extent = shoulder_y, np.inf
    for y0 in np.arange(shoulder_y, head_band_y0, SLICE_STEP):
        clusters = _band_clusters(V, y0, y0 + SLICE_BAND_THICKNESS)
        if len(clusters) != 1:
            continue
        extent = V[clusters[0], 0].max() - V[clusters[0], 0].min()
        if extent < best_extent:
            best_extent, best_y = extent, float(y0)
    return best_y


def _band_mean(V: np.ndarray, y0: float, y1: float, x_gate: float | None = None) -> np.ndarray:
    mask = (V[:, 1] >= y0) & (V[:, 1] < y1)
    if x_gate is not None:
        mask &= np.abs(V[:, 0]) > x_gate
    if mask.sum() < 5:
        raise PipelineError(f"fewer than 5 verts in band y=[{y0:.3f},{y1:.3f}) x_gate={x_gate}")
    return V[mask].mean(axis=0)


def _foot_mean(V: np.ndarray, y0: float, y1: float, side: str) -> np.ndarray:
    mask = (V[:, 1] >= y0) & (V[:, 1] < y1)
    mask &= (V[:, 0] > 0) if side == "left" else (V[:, 0] < 0)
    mask &= (np.abs(V[:, 0]) > LANDMARK_X_GATE_FOOT_MIN) & (np.abs(V[:, 0]) < LANDMARK_X_GATE_FOOT)
    if mask.sum() < 5:
        raise PipelineError(f"fewer than 5 verts detected for {side} foot")
    return V[mask].mean(axis=0)


def detect_landmarks(V: np.ndarray, config: CharacterConfig | None = None) -> Landmarks:
    """WS3a: auto-detects the 25-joint skeleton's anatomical landmarks from the
    cleaned, grounded mesh. `config.landmark_overrides` wins over any individual
    auto-detected field.
    """
    overrides = config.landmark_overrides if config else {}
    height = float(V[:, 1].max())

    def frac_band(key: str) -> tuple[float, float]:
        lo, hi = LANDMARK_BANDS_FRAC[key]
        return lo * height, hi * height

    crotch_y = overrides.get("crotch_y", _find_crotch_y(V, height))

    hip_y0, hip_y1 = frac_band("hip_z")
    z_hip = overrides.get("z_hip", float(_band_mean(V, hip_y0, hip_y1, LANDMARK_X_GATE_CHEST)[2]))

    chest_y0, chest_y1 = frac_band("chest_z")
    z_chest = overrides.get(
        "z_chest", float(_band_mean(V, chest_y0, chest_y1, LANDMARK_X_GATE_CHEST)[2])
    )

    head_y0, head_y1 = frac_band("head_z")
    z_head = overrides.get("z_head", float(_band_mean(V, head_y0, head_y1)[2]))

    foot_y0, foot_y1 = frac_band("foot_z")
    z_foot_l = (
        np.array(overrides["z_foot_l"])
        if "z_foot_l" in overrides
        else _foot_mean(V, foot_y0, foot_y1, "left")
    )
    z_foot_r = (
        np.array(overrides["z_foot_r"])
        if "z_foot_r" in overrides
        else _foot_mean(V, foot_y0, foot_y1, "right")
    )

    sho_y0, sho_y1 = frac_band("shoulder")
    sho_clusters = _band_clusters(V, sho_y0, sho_y1, LANDMARK_X_GATE_SHOULDER)
    if "shoulder_l" in overrides:
        shoulder_l = np.array(overrides["shoulder_l"])
    else:
        cluster = _outer_cluster(V, sho_clusters, "left")
        shoulder_l = V[cluster].mean(axis=0)
        shoulder_l[1] = V[cluster, 1].max()  # refine y as top of the arm cluster
    if "shoulder_r" in overrides:
        shoulder_r = np.array(overrides["shoulder_r"])
    else:
        cluster = _outer_cluster(V, sho_clusters, "right")
        shoulder_r = V[cluster].mean(axis=0)
        shoulder_r[1] = V[cluster, 1].max()

    hand_y0, hand_y1 = frac_band("hand")
    hand_clusters = _band_clusters(V, hand_y0, hand_y1, LANDMARK_X_GATE_HAND)
    hand_l = (
        np.array(overrides["hand_l"])
        if "hand_l" in overrides
        else V[_outer_cluster(V, hand_clusters, "left")].mean(axis=0)
    )
    hand_r = (
        np.array(overrides["hand_r"])
        if "hand_r" in overrides
        else V[_outer_cluster(V, hand_clusters, "right")].mean(axis=0)
    )

    neck_y = overrides.get(
        "neck_y", _find_neck_y(V, max(float(shoulder_l[1]), float(shoulder_r[1])), head_y0)
    )

    return Landmarks(
        height=height,
        crotch_y=crotch_y,
        z_hip=z_hip,
        z_chest=z_chest,
        z_head=z_head,
        z_foot_l=z_foot_l,
        z_foot_r=z_foot_r,
        shoulder_l=shoulder_l,
        shoulder_r=shoulder_r,
        hand_l=hand_l,
        hand_r=hand_r,
        neck_y=neck_y,
    )
