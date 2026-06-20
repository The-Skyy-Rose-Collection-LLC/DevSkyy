"""TRELLIS configuration.

Declarative configuration for the TRELLIS provider: backend selection,
quality presets, output paths, and resource limits. Created from environment
variables via :meth:`TrellisConfig.from_env`.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

# =============================================================================
# Backends
# =============================================================================


class TrellisBackend(StrEnum):
    """Where the TRELLIS model runs.

    - ``HF_SPACE``: hosted HuggingFace Space ``JeffreyXiang/TRELLIS``
      (free, slower, no GPU required client-side). Default.
    - ``LOCAL``: run TRELLIS in-process from the vendored repo at
      ``vendor/trellis``. Requires CUDA GPU + model weights downloaded.
    - ``REPLICATE``: hosted via Replicate's TRELLIS endpoint
      (paid, fast, no GPU required client-side).
    - ``MODAL``: hosted via Modal serverless GPU
      (paid, fastest cold-start-free, requires Modal account).
    """

    HF_SPACE = "hf_space"
    LOCAL = "local"
    REPLICATE = "replicate"
    MODAL = "modal"


class TrellisQualityPreset(StrEnum):
    """Quality presets that map onto TRELLIS sampling parameters.

    DRAFT: 8 SS + 8 SLAT steps, mesh simplify 0.85 — for previews / QA
    STANDARD: 12 SS + 12 SLAT steps, simplify 0.95 — production default
    PRODUCTION: 20 SS + 20 SLAT steps, simplify 0.97, 2048 texture — hero shots
    """

    DRAFT = "draft"
    STANDARD = "standard"
    PRODUCTION = "production"


# =============================================================================
# Sampling parameter table
# =============================================================================


@dataclass(frozen=True, slots=True)
class TrellisSamplingParams:
    """TRELLIS sampling hyperparameters per quality preset."""

    ss_sampling_steps: int
    ss_guidance_strength: float
    slat_sampling_steps: int
    slat_guidance_strength: float
    mesh_simplify: float
    texture_size: int
    target_polycount: int

    @classmethod
    def for_preset(cls, preset: TrellisQualityPreset) -> TrellisSamplingParams:
        """Return canonical params for a quality preset."""
        return _PRESET_PARAMS[preset]


_PRESET_PARAMS: dict[TrellisQualityPreset, TrellisSamplingParams] = {
    TrellisQualityPreset.DRAFT: TrellisSamplingParams(
        ss_sampling_steps=8,
        ss_guidance_strength=7.5,
        slat_sampling_steps=8,
        slat_guidance_strength=3.0,
        mesh_simplify=0.85,
        texture_size=1024,
        target_polycount=40_000,
    ),
    TrellisQualityPreset.STANDARD: TrellisSamplingParams(
        ss_sampling_steps=12,
        ss_guidance_strength=7.5,
        slat_sampling_steps=12,
        slat_guidance_strength=3.0,
        mesh_simplify=0.95,
        texture_size=1024,
        target_polycount=80_000,
    ),
    TrellisQualityPreset.PRODUCTION: TrellisSamplingParams(
        ss_sampling_steps=20,
        ss_guidance_strength=8.0,
        slat_sampling_steps=20,
        slat_guidance_strength=3.5,
        mesh_simplify=0.97,
        texture_size=2048,
        target_polycount=150_000,
    ),
}


# =============================================================================
# Top-level config
# =============================================================================


def _default_output_dir() -> str:
    return os.getenv("TRELLIS_OUTPUT_DIR") or os.getenv(
        "THREE_D_OUTPUT_DIR", "./assets/3d-models-generated"
    )


def _default_cache_dir() -> str:
    return os.getenv("TRELLIS_CACHE_DIR", "./.cache/trellis")


@dataclass(slots=True)
class TrellisConfig:
    """Top-level TRELLIS configuration.

    All fields have sensible defaults — instantiate with ``TrellisConfig()`` for
    HF Space inference, or ``TrellisConfig(backend=TrellisBackend.LOCAL)`` for
    local GPU inference.

    Attributes:
        backend: Which TRELLIS backend to use (HF_SPACE by default).
        quality: Quality preset; controls sampling steps and texture size.
        hf_space_id: HuggingFace Space ID (only used when backend=HF_SPACE).
        hf_token: HuggingFace API token (for private spaces / rate limits).
        local_repo_path: Path to the vendored TRELLIS repo (LOCAL backend).
        local_model_name: TRELLIS model checkpoint (LOCAL backend).
        replicate_model: Replicate model identifier (REPLICATE backend).
        replicate_token: Replicate API token (REPLICATE backend).
        modal_app: Modal app name (MODAL backend).
        output_dir: Where to write generated GLB/USDZ artifacts.
        cache_dir: Cache directory for preprocessing intermediates.
        max_input_resolution: Cap on input image resolution.
        min_input_resolution: Minimum acceptable input resolution.
        seed: Random seed for reproducibility (None = stochastic).
        timeout_seconds: Hard timeout for a single generation call.
        retry_attempts: Number of retry attempts on transient failures.
        retry_backoff_seconds: Initial backoff; doubles per attempt.
        enable_background_removal: Run rembg/SAM on inputs before generation.
        enable_postprocess: Run mesh cleanup + format conversion.
        export_formats: Which output formats to emit (always includes input).
        export_usdz_for_ios: Also emit ``.usdz`` for iOS AR Quick Look.
    """

    # Backend selection
    backend: TrellisBackend = field(
        default_factory=lambda: TrellisBackend(
            os.getenv("TRELLIS_BACKEND", TrellisBackend.HF_SPACE.value)
        )
    )
    quality: TrellisQualityPreset = field(
        default_factory=lambda: TrellisQualityPreset(
            os.getenv("TRELLIS_QUALITY", TrellisQualityPreset.STANDARD.value)
        )
    )

    # HF Space
    hf_space_id: str = field(
        default_factory=lambda: os.getenv("TRELLIS_HF_SPACE", "JeffreyXiang/TRELLIS")
    )
    hf_token: str | None = field(
        default_factory=lambda: os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")
    )

    # Local backend
    local_repo_path: str = field(
        default_factory=lambda: os.getenv("TRELLIS_LOCAL_PATH", "./vendor/trellis")
    )
    local_model_name: str = field(
        default_factory=lambda: os.getenv("TRELLIS_MODEL", "microsoft/TRELLIS-image-large")
    )

    # Replicate backend
    replicate_model: str = field(
        default_factory=lambda: os.getenv(
            "TRELLIS_REPLICATE_MODEL",
            "firtoz/trellis:e8f6c45206993f297372f5436b90350817bd9b4a0d52d2a76df50c1c8afa2b3c",
        )
    )
    replicate_token: str | None = field(default_factory=lambda: os.getenv("REPLICATE_API_TOKEN"))

    # Modal backend
    modal_app: str = field(default_factory=lambda: os.getenv("TRELLIS_MODAL_APP", "trellis-3d"))

    # I/O
    output_dir: str = field(default_factory=_default_output_dir)
    cache_dir: str = field(default_factory=_default_cache_dir)

    # Resolution limits
    max_input_resolution: int = 2048
    min_input_resolution: int = 256

    # Generation
    seed: int | None = field(
        default_factory=lambda: int(os.environ["TRELLIS_SEED"]) if os.getenv("TRELLIS_SEED") else 42
    )
    timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("TRELLIS_TIMEOUT", "420"))
    )
    retry_attempts: int = field(default_factory=lambda: int(os.getenv("TRELLIS_RETRIES", "2")))
    retry_backoff_seconds: float = 4.0

    # Pipeline switches
    enable_background_removal: bool = field(
        default_factory=lambda: os.getenv("TRELLIS_BG_REMOVE", "true").lower() == "true"
    )
    enable_postprocess: bool = field(
        default_factory=lambda: os.getenv("TRELLIS_POSTPROCESS", "true").lower() == "true"
    )

    # Output format matrix
    export_formats: tuple[str, ...] = ("glb",)
    export_usdz_for_ios: bool = field(
        default_factory=lambda: os.getenv("TRELLIS_EXPORT_USDZ", "true").lower() == "true"
    )

    @classmethod
    def from_env(cls) -> TrellisConfig:
        """Build the config from environment variables (recommended)."""
        return cls()

    @property
    def sampling(self) -> TrellisSamplingParams:
        """Sampling params for the selected quality preset."""
        return TrellisSamplingParams.for_preset(self.quality)

    def ensure_dirs(self) -> None:
        """Create output / cache directories if missing."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)


__all__ = [
    "TrellisBackend",
    "TrellisQualityPreset",
    "TrellisSamplingParams",
    "TrellisConfig",
]
