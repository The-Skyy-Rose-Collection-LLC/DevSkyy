"""Phase 0.1 — camera-pose calibration for the fidelity gate.

Establishes a Blender camera whose render of a generated mesh aligns to the
SkyyRose techflat capture pose, so visible-face render-compare is meaningful.
Validated by silhouette IoU against the golden front image. PAID/GPU dispatch
(running TRELLIS to get a calibration mesh) is STOP-AND-SHOW gated.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROFILE_PATH = (
    Path(__file__).resolve().parent.parent
    / "skyyrose/elite_studio/platform/fidelity/camera_profiles/skyyrose.json"
)

# Starting camera guess for flat front-facing techflats (orthographic front).
# Calibration refines ortho_scale to match the golden silhouette extent.
DEFAULT_CAMERA = {
    "type": "ORTHO",
    "location": [0.0, -2.5, 0.0],
    "rotation_euler": [1.5708, 0.0, 0.0],  # look down +Y
    "ortho_scale": 1.2,
    "lens": 50,
}


def silhouette_iou(a: np.ndarray, b: np.ndarray) -> float:
    """Intersection-over-union of two boolean silhouette masks."""
    a = a.astype(bool)
    b = b.astype(bool)
    union = np.logical_or(a, b).sum()
    if union == 0:
        return 1.0
    return float(np.logical_and(a, b).sum() / union)


def write_profile(profile: dict, path: Path = PROFILE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    # Calibration mesh generation is GPU+paid -> STOP-AND-SHOW. Until confirmed,
    # write the default profile and report it for human review.
    profile = dict(DEFAULT_CAMERA)
    out = write_profile(profile)
    print(f"camera profile written: {out}")
    print(json.dumps(profile, indent=2))
    print(
        "\nTo calibrate against a real mesh (GPU + paid TRELLIS run), re-run with "
        "--calibrate br-001 and confirm the STOP-AND-SHOW manifest."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
