"""TRELLIS transport clients.

Backend transports for the TRELLIS model, all conforming to
:class:`TrellisBackendClient`. The provider picks one at runtime based on
:class:`~services.three_d.trellis.config.TrellisBackend`.

Currently implemented:
- :class:`HFSpaceClient` — calls ``JeffreyXiang/TRELLIS`` via ``gradio_client``
- :class:`LocalTrellisClient` — runs the vendored TRELLIS repo in-process
  (lazy-imports the heavy deps; requires CUDA + model weights)
- :class:`ReplicateClient` — hits the hosted Replicate endpoint
- :class:`StubClient` — deterministic fixture for tests / dry-runs

All clients return :class:`BackendResult` describing where to find the GLB
on local disk and any side-artifacts (preview MP4, gaussian splat .ply).

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from services.three_d.trellis.config import (
    TrellisBackend,
    TrellisConfig,
    TrellisSamplingParams,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Result model
# =============================================================================


@dataclass(slots=True)
class BackendResult:
    """Outcome of a TRELLIS backend call.

    Attributes:
        glb_path: Local filesystem path to the generated GLB.
        preview_path: Optional path to a preview MP4 / image strip.
        splat_path: Optional path to the raw Gaussian splat ``.ply``.
        seed: Seed used (echo back for reproducibility).
        backend: Which backend produced this result.
        duration_seconds: Wall-clock duration of the backend call.
        metadata: Free-form provider metadata.
    """

    glb_path: str
    preview_path: str | None = None
    splat_path: str | None = None
    seed: int | None = None
    backend: str = ""
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Protocol
# =============================================================================


@runtime_checkable
class TrellisBackendClient(Protocol):
    """Common interface for all TRELLIS transports."""

    backend_name: str

    async def generate_from_image(
        self,
        image_path: str,
        *,
        sampling: TrellisSamplingParams,
        prompt_hint: str | None = None,
        seed: int | None = None,
    ) -> BackendResult: ...

    async def generate_from_text(
        self,
        prompt: str,
        *,
        sampling: TrellisSamplingParams,
        seed: int | None = None,
    ) -> BackendResult: ...

    async def healthy(self) -> tuple[bool, str | None]: ...

    async def close(self) -> None: ...


# =============================================================================
# Errors
# =============================================================================


class BackendUnavailable(RuntimeError):
    """The configured backend cannot service the request right now."""


# =============================================================================
# HuggingFace Space backend
# =============================================================================


class HFSpaceClient:
    """Hits the public ``JeffreyXiang/TRELLIS`` Space via Gradio.

    Free, no GPU required client-side, but cold starts can be slow and the
    space occasionally rate-limits. Production deployments should consider
    Replicate or self-hosted Modal.
    """

    backend_name = TrellisBackend.HF_SPACE.value

    def __init__(self, config: TrellisConfig) -> None:
        self.config = config
        self._client: Any = None

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from gradio_client import Client
        except ImportError as e:
            raise BackendUnavailable(
                "gradio_client not installed — pip install gradio_client"
            ) from e

        def _build() -> Any:
            return Client(
                self.config.hf_space_id,
                hf_token=self.config.hf_token,
            )

        self._client = await asyncio.to_thread(_build)
        return self._client

    async def healthy(self) -> tuple[bool, str | None]:
        try:
            from gradio_client import Client  # noqa: F401
        except ImportError:
            return False, "gradio_client not installed"
        try:
            await self._get_client()
            return True, None
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    async def generate_from_image(
        self,
        image_path: str,
        *,
        sampling: TrellisSamplingParams,
        prompt_hint: str | None = None,
        seed: int | None = None,
    ) -> BackendResult:
        client = await self._get_client()
        seed_val = seed if seed is not None else (self.config.seed or 0)
        start = time.time()

        try:
            from gradio_client import handle_file
        except ImportError as e:
            raise BackendUnavailable("gradio_client missing handle_file") from e

        def _call() -> Any:
            return client.predict(
                image=handle_file(image_path),
                multiimages=[],
                seed=seed_val,
                ss_guidance_strength=sampling.ss_guidance_strength,
                ss_sampling_steps=sampling.ss_sampling_steps,
                slat_guidance_strength=sampling.slat_guidance_strength,
                slat_sampling_steps=sampling.slat_sampling_steps,
                multiimage_algo="stochastic",
                mesh_simplify=sampling.mesh_simplify,
                texture_size=sampling.texture_size,
                api_name="/generate_and_extract_glb",
            )

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(_call),
                timeout=self.config.timeout_seconds,
            )
        except asyncio.TimeoutError as e:
            raise TimeoutError(
                f"TRELLIS HF Space timed out after {self.config.timeout_seconds}s"
            ) from e

        # The space returns (video_info, glb_path, download_path)
        if not isinstance(result, (list, tuple)) or len(result) < 2:
            raise BackendUnavailable(f"Unexpected TRELLIS response shape: {type(result)}")

        video_info, glb_path = result[0], result[1]
        if not glb_path or not os.path.exists(glb_path):
            raise BackendUnavailable("TRELLIS HF Space returned no GLB")

        return BackendResult(
            glb_path=glb_path,
            preview_path=_extract_preview(video_info),
            seed=seed_val,
            backend=self.backend_name,
            duration_seconds=time.time() - start,
            metadata={"hf_space": self.config.hf_space_id, "prompt_hint": prompt_hint},
        )

    async def generate_from_text(
        self,
        prompt: str,
        *,
        sampling: TrellisSamplingParams,
        seed: int | None = None,
    ) -> BackendResult:
        raise BackendUnavailable(
            "TRELLIS HF Space does not expose text-to-3D — use image-to-3D or "
            "switch to LOCAL backend with TRELLIS-text-large weights"
        )

    async def close(self) -> None:
        self._client = None


def _extract_preview(video_info: Any) -> str | None:
    """Pull a usable preview path out of the HF Space's video payload."""
    if isinstance(video_info, str) and os.path.exists(video_info):
        return video_info
    if isinstance(video_info, dict) and "video" in video_info:
        candidate = video_info["video"]
        if isinstance(candidate, str) and os.path.exists(candidate):
            return candidate
    return None


# =============================================================================
# Local backend (vendored TRELLIS repo)
# =============================================================================


class LocalTrellisClient:
    """Runs TRELLIS in-process from the vendored repo at ``vendor/trellis``.

    Requires:
    - ``vendor/trellis/`` (cloned via ``scripts/setup_trellis.sh``)
    - CUDA-capable GPU with >=16 GB VRAM (image-large) or >=24 GB (text-large)
    - ``pip install -r requirements-trellis.txt``
    - Model weights cached under ``$TRELLIS_CACHE_DIR``

    The class lazy-imports the pipeline so importing this module on a
    GPU-less dev box doesn't blow up.
    """

    backend_name = TrellisBackend.LOCAL.value

    def __init__(self, config: TrellisConfig) -> None:
        self.config = config
        self._pipeline: Any = None
        self._pipeline_lock = asyncio.Lock()

    async def _get_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline
        async with self._pipeline_lock:
            if self._pipeline is not None:
                return self._pipeline
            self._pipeline = await asyncio.to_thread(self._build_pipeline)
            return self._pipeline

    def _build_pipeline(self) -> Any:
        repo_root = Path(self.config.local_repo_path).resolve()
        if not repo_root.exists():
            raise BackendUnavailable(
                f"Local TRELLIS repo not found at {repo_root}. "
                f"Run scripts/setup_trellis.sh first."
            )

        # Add the repo to sys.path so its `trellis` package is importable.
        import sys

        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        try:
            from trellis.pipelines import TrellisImageTo3DPipeline  # type: ignore[import-not-found]
        except ImportError as e:
            raise BackendUnavailable(
                "TRELLIS package not importable. Did you `pip install -e vendor/trellis`?"
            ) from e

        os.environ.setdefault("ATTN_BACKEND", "xformers")
        os.environ.setdefault("SPCONV_ALGO", "native")

        pipeline = TrellisImageTo3DPipeline.from_pretrained(self.config.local_model_name)
        if hasattr(pipeline, "cuda"):
            pipeline.cuda()
        return pipeline

    async def healthy(self) -> tuple[bool, str | None]:
        try:
            await self._get_pipeline()
            return True, None
        except BackendUnavailable as exc:
            return False, str(exc)
        except Exception as exc:  # noqa: BLE001
            return False, f"local backend init failed: {exc}"

    async def generate_from_image(
        self,
        image_path: str,
        *,
        sampling: TrellisSamplingParams,
        prompt_hint: str | None = None,
        seed: int | None = None,
    ) -> BackendResult:
        pipeline = await self._get_pipeline()
        seed_val = seed if seed is not None else (self.config.seed or 0)
        start = time.time()

        def _call() -> BackendResult:
            from PIL import Image  # local: already a dep when LOCAL backend is active

            image = Image.open(image_path).convert("RGB")

            outputs = pipeline.run(
                image,
                seed=seed_val,
                sparse_structure_sampler_params={
                    "steps": sampling.ss_sampling_steps,
                    "cfg_strength": sampling.ss_guidance_strength,
                },
                slat_sampler_params={
                    "steps": sampling.slat_sampling_steps,
                    "cfg_strength": sampling.slat_guidance_strength,
                },
            )

            return self._export_outputs(outputs, sampling, seed_val, start)

        return await asyncio.to_thread(_call)

    async def generate_from_text(
        self,
        prompt: str,
        *,
        sampling: TrellisSamplingParams,
        seed: int | None = None,
    ) -> BackendResult:
        # Text-to-3D in TRELLIS uses a separate checkpoint
        # (TRELLIS-text-large). We only wire up image-to-3D in v1; raise so
        # the factory falls back to e.g. HuggingFace SHAP-E.
        raise BackendUnavailable(
            "Local text-to-3D not wired up in v1 — see services/three_d/trellis/TODO_TEXT.md"
        )

    def _export_outputs(
        self,
        outputs: Any,
        sampling: TrellisSamplingParams,
        seed_val: int,
        start: float,
    ) -> BackendResult:
        from trellis.utils import postprocessing_utils  # type: ignore[import-not-found]

        tmpdir = Path(tempfile.mkdtemp(prefix="trellis_local_"))
        glb_path = tmpdir / "model.glb"
        gaussian = outputs["gaussian"][0]
        mesh = outputs["mesh"][0]

        glb = postprocessing_utils.to_glb(
            gaussian,
            mesh,
            simplify=sampling.mesh_simplify,
            texture_size=sampling.texture_size,
        )
        glb.export(str(glb_path))

        splat_path = tmpdir / "splat.ply"
        try:
            gaussian.save_ply(str(splat_path))
        except Exception:  # noqa: BLE001 — optional artifact
            splat_path = None  # type: ignore[assignment]

        return BackendResult(
            glb_path=str(glb_path),
            splat_path=str(splat_path) if splat_path else None,
            seed=seed_val,
            backend=self.backend_name,
            duration_seconds=time.time() - start,
            metadata={"model": self.config.local_model_name},
        )

    async def close(self) -> None:
        self._pipeline = None


# =============================================================================
# Replicate backend
# =============================================================================


class ReplicateClient:
    """Hosted TRELLIS via Replicate's REST API.

    Pros: no local GPU, ~30s warm latency, decent free credit allowance.
    Cons: paid past free tier; mesh fidelity slightly behind self-hosted.
    """

    backend_name = TrellisBackend.REPLICATE.value

    def __init__(self, config: TrellisConfig) -> None:
        self.config = config
        if not config.replicate_token:
            logger.debug("REPLICATE_API_TOKEN not set; client will fail health checks")

    async def healthy(self) -> tuple[bool, str | None]:
        if not self.config.replicate_token:
            return False, "REPLICATE_API_TOKEN not set"
        try:
            import replicate  # noqa: F401  # type: ignore[import-not-found]
        except ImportError:
            return False, "replicate SDK not installed"
        return True, None

    async def generate_from_image(
        self,
        image_path: str,
        *,
        sampling: TrellisSamplingParams,
        prompt_hint: str | None = None,
        seed: int | None = None,
    ) -> BackendResult:
        try:
            import replicate  # type: ignore[import-not-found]
        except ImportError as e:
            raise BackendUnavailable("replicate SDK not installed") from e

        if not self.config.replicate_token:
            raise BackendUnavailable("REPLICATE_API_TOKEN not set")

        os.environ["REPLICATE_API_TOKEN"] = self.config.replicate_token
        seed_val = seed if seed is not None else (self.config.seed or 0)
        start = time.time()

        def _call() -> str:
            with open(image_path, "rb") as fh:
                output = replicate.run(
                    self.config.replicate_model,
                    input={
                        "images": [fh],
                        "seed": seed_val,
                        "ss_guidance_strength": sampling.ss_guidance_strength,
                        "ss_sampling_steps": sampling.ss_sampling_steps,
                        "slat_guidance_strength": sampling.slat_guidance_strength,
                        "slat_sampling_steps": sampling.slat_sampling_steps,
                        "mesh_simplify": sampling.mesh_simplify,
                        "texture_size": sampling.texture_size,
                        "generate_model": True,
                    },
                )
            if isinstance(output, list):
                output = output[0] if output else ""
            if not output:
                raise BackendUnavailable("Replicate returned empty output")
            return str(output)

        try:
            model_url = await asyncio.wait_for(
                asyncio.to_thread(_call),
                timeout=self.config.timeout_seconds,
            )
        except asyncio.TimeoutError as e:
            raise TimeoutError("Replicate TRELLIS timed out") from e

        # Download the GLB locally so the rest of the pipeline can postprocess it.
        local_path = await asyncio.to_thread(_download_to_temp, model_url, ".glb")

        return BackendResult(
            glb_path=local_path,
            seed=seed_val,
            backend=self.backend_name,
            duration_seconds=time.time() - start,
            metadata={"model_url": model_url, "replicate_model": self.config.replicate_model},
        )

    async def generate_from_text(
        self,
        prompt: str,
        *,
        sampling: TrellisSamplingParams,
        seed: int | None = None,
    ) -> BackendResult:
        raise BackendUnavailable(
            "Replicate TRELLIS endpoint is image-to-3D only — use HF SHAP-E for text"
        )

    async def close(self) -> None:
        pass


def _download_to_temp(url: str, suffix: str) -> str:
    import urllib.request

    tmp = Path(tempfile.mkdtemp(prefix="trellis_replicate_")) / f"output{suffix}"
    with urllib.request.urlopen(url) as src, open(tmp, "wb") as dst:  # noqa: S310 — trusted URL
        shutil.copyfileobj(src, dst)
    return str(tmp)


# =============================================================================
# Stub backend (tests / dry-run)
# =============================================================================


class StubClient:
    """Deterministic fixture used by tests and the ``--dry-run`` CLI mode.

    Writes a tiny placeholder GLB and returns immediately. Lets the rest of
    the orchestration be exercised without burning credits or hitting a GPU.
    """

    backend_name = "stub"

    def __init__(self, config: TrellisConfig) -> None:
        self.config = config

    async def healthy(self) -> tuple[bool, str | None]:
        return True, None

    async def generate_from_image(
        self,
        image_path: str,
        *,
        sampling: TrellisSamplingParams,
        prompt_hint: str | None = None,
        seed: int | None = None,
    ) -> BackendResult:
        return self._fake_result(sampling, seed, source="image")

    async def generate_from_text(
        self,
        prompt: str,
        *,
        sampling: TrellisSamplingParams,
        seed: int | None = None,
    ) -> BackendResult:
        return self._fake_result(sampling, seed, source="text")

    async def close(self) -> None:
        pass

    def _fake_result(
        self,
        sampling: TrellisSamplingParams,
        seed: int | None,
        *,
        source: str,
    ) -> BackendResult:
        tmpdir = Path(tempfile.mkdtemp(prefix="trellis_stub_"))
        glb_path = tmpdir / "model.glb"
        # Minimal GLB header — not a valid GLB but small and detectable.
        glb_path.write_bytes(b"glTF\x02\x00\x00\x00" + b"\x00" * 64)
        return BackendResult(
            glb_path=str(glb_path),
            seed=seed if seed is not None else (self.config.seed or 0),
            backend=self.backend_name,
            duration_seconds=0.01,
            metadata={"stub": True, "source": source, "sampling": asdict(sampling)},
        )


# =============================================================================
# Factory
# =============================================================================


def build_backend(config: TrellisConfig) -> TrellisBackendClient:
    """Construct the backend client implied by ``config.backend``."""
    backend = config.backend
    if backend == TrellisBackend.HF_SPACE:
        return HFSpaceClient(config)
    if backend == TrellisBackend.LOCAL:
        return LocalTrellisClient(config)
    if backend == TrellisBackend.REPLICATE:
        return ReplicateClient(config)
    if backend == TrellisBackend.MODAL:
        # Modal backend deferred — fall back to HF Space with a warning.
        logger.warning("Modal backend not yet implemented — using HF Space")
        return HFSpaceClient(config)
    raise BackendUnavailable(f"Unknown TRELLIS backend: {backend}")


__all__ = [
    "BackendResult",
    "BackendUnavailable",
    "HFSpaceClient",
    "LocalTrellisClient",
    "ReplicateClient",
    "StubClient",
    "TrellisBackendClient",
    "build_backend",
]
