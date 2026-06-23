"""Generation record dataclass for TRELLIS.2 jobs.

Tracks every image-to-3D generation job: inputs, parameters, outputs, status.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Status constants ──────────────────────────────────────────────────────────

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

VALID_STATUSES = {STATUS_PENDING, STATUS_RUNNING, STATUS_DONE, STATUS_FAILED}

# ── Resolution presets (from TRELLIS.2 app.py pipeline_type mapping) ─────────

RESOLUTION_PRESETS = {
    "low": {
        "sparse_structure_sampler_params": {
            "steps": 12,
            "cfg_strength": 7.5,
            "rescale": 0.7,
        },
        "shape_slat_sampler_params": {
            "steps": 12,
            "cfg_strength": 3.0,
            "rescale_cfg": 0.7,
            "rescale_t": 0.25,
        },
        "tex_slat_sampler_params": {
            "steps": 12,
            "cfg_strength": 3.0,
            "rescale_cfg": 0.7,
            "rescale_t": 0.25,
        },
    },
    "high": {
        "sparse_structure_sampler_params": {
            "steps": 50,
            "cfg_strength": 7.5,
            "rescale": 0.7,
        },
        "shape_slat_sampler_params": {
            "steps": 50,
            "cfg_strength": 3.0,
            "rescale_cfg": 0.7,
            "rescale_t": 0.25,
        },
        "tex_slat_sampler_params": {
            "steps": 50,
            "cfg_strength": 3.0,
            "rescale_cfg": 0.7,
            "rescale_t": 0.25,
        },
    },
}

# Default to high quality
DEFAULT_RESOLUTION = "high"


def new_job_id() -> str:
    """Generate a cryptographically random 8-byte hex job ID."""
    return secrets.token_hex(8)


def _timestamp() -> float:
    """Return current POSIX timestamp."""
    return time.time()


@dataclass
class GenerationRecord:
    """Immutable record of a single TRELLIS.2 image-to-3D generation job.

    Attributes:
        job_id: Unique identifier (16-char hex from secrets.token_hex(8)).
        image_path: Absolute path to the source image file.
        output_dir: Directory where outputs (GLB, latent) are written.
        resolution: Preset name ("low" or "high").
        seed: Integer seed for reproducibility (-1 means random).
        decimation_target: Target polygon count for GLB mesh decimation.
        texture_size: Texture atlas size (pixels per side).
        status: Current job status (pending/running/done/failed).
        created_at: POSIX timestamp when record was created.
        started_at: POSIX timestamp when runner was launched (or None).
        finished_at: POSIX timestamp when runner exited (or None).
        glb_path: Absolute path of the exported GLB file (or None).
        error: Error message if status is failed (or None).
        extra: Arbitrary metadata dict for future extensibility.
    """

    job_id: str
    image_path: str
    output_dir: str
    resolution: str = DEFAULT_RESOLUTION
    seed: int = -1
    decimation_target: int = 1_000_000
    texture_size: int = 4096
    status: str = STATUS_PENDING
    created_at: float = field(default_factory=_timestamp)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    glb_path: Optional[str] = None
    error: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    # ── Constructors ──────────────────────────────────────────────────────────

    @classmethod
    def new(
        cls,
        image_path: str,
        output_dir: str,
        resolution: str = DEFAULT_RESOLUTION,
        seed: int = -1,
        decimation_target: int = 1_000_000,
        texture_size: int = 4096,
    ) -> "GenerationRecord":
        """Create a new pending GenerationRecord with a fresh job_id."""
        if resolution not in RESOLUTION_PRESETS:
            raise ValueError(
                f"Unknown resolution preset {resolution!r}. "
                f"Valid options: {sorted(RESOLUTION_PRESETS)}"
            )
        return cls(
            job_id=new_job_id(),
            image_path=str(Path(image_path).resolve()),
            output_dir=str(Path(output_dir).resolve()),
            resolution=resolution,
            seed=seed,
            decimation_target=decimation_target,
            texture_size=texture_size,
        )

    # ── Transitions (return new instances — immutability) ─────────────────────

    def mark_running(self) -> "GenerationRecord":
        """Return copy of record with status=running and started_at set."""
        return GenerationRecord(
            **{**self._asdict(), "status": STATUS_RUNNING, "started_at": _timestamp()}
        )

    def mark_done(self, glb_path: str) -> "GenerationRecord":
        """Return copy of record with status=done and glb_path set."""
        return GenerationRecord(
            **{
                **self._asdict(),
                "status": STATUS_DONE,
                "finished_at": _timestamp(),
                "glb_path": str(Path(glb_path).resolve()),
            }
        )

    def mark_failed(self, error: str) -> "GenerationRecord":
        """Return copy of record with status=failed and error set."""
        return GenerationRecord(
            **{
                **self._asdict(),
                "status": STATUS_FAILED,
                "finished_at": _timestamp(),
                "error": error,
            }
        )

    # ── Serialization ─────────────────────────────────────────────────────────

    def _asdict(self) -> Dict[str, Any]:
        """Return dict representation (mirrors dataclasses.asdict but manual for speed)."""
        return {
            "job_id": self.job_id,
            "image_path": self.image_path,
            "output_dir": self.output_dir,
            "resolution": self.resolution,
            "seed": self.seed,
            "decimation_target": self.decimation_target,
            "texture_size": self.texture_size,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "glb_path": self.glb_path,
            "error": self.error,
            "extra": self.extra,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return self._asdict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationRecord":
        """Deserialize from a dict (as returned by to_dict())."""
        required = {"job_id", "image_path", "output_dir"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"GenerationRecord.from_dict missing keys: {missing}")
        return cls(
            job_id=data["job_id"],
            image_path=data["image_path"],
            output_dir=data["output_dir"],
            resolution=data.get("resolution", DEFAULT_RESOLUTION),
            seed=data.get("seed", -1),
            decimation_target=data.get("decimation_target", 1_000_000),
            texture_size=data.get("texture_size", 4096),
            status=data.get("status", STATUS_PENDING),
            created_at=data.get("created_at", 0.0),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            glb_path=data.get("glb_path"),
            error=data.get("error"),
            extra=data.get("extra", {}),
        )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_terminal(self) -> bool:
        """True if the job reached a final state (done or failed)."""
        return self.status in {STATUS_DONE, STATUS_FAILED}

    @property
    def duration_seconds(self) -> Optional[float]:
        """Wall-clock seconds from started_at to finished_at, or None."""
        if self.started_at is None or self.finished_at is None:
            return None
        return self.finished_at - self.started_at

    @property
    def sampler_params(self) -> Dict[str, Any]:
        """Resolved sampler params dict for the runner, keyed by preset name."""
        return RESOLUTION_PRESETS[self.resolution]

    def __repr__(self) -> str:
        return (
            f"GenerationRecord(job_id={self.job_id!r}, status={self.status!r}, "
            f"resolution={self.resolution!r}, image={self.image_path!r})"
        )


# ── Helpers ───────────────────────────────────────────────────────────────────


def validate_status(status: str) -> str:
    """Raise ValueError if status is not a known value, else return it."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Unknown status {status!r}. Valid: {sorted(VALID_STATUSES)}")
    return status
