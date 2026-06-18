"""TRELLIS provider — :class:`I3DProvider` implementation.

Wires together:

- :class:`~services.three_d.trellis.preprocess.TrellisPreprocessor`
- :class:`~services.three_d.trellis.client.TrellisBackendClient`
- :class:`~services.three_d.trellis.postprocess.MeshPostprocessor`
- :func:`~services.three_d.trellis.garment_aware.build_clothing_prompt`

into a single async surface that the
:class:`~services.three_d.provider_factory.ThreeDProviderFactory` can register
alongside the existing Tripo / Replicate / HuggingFace adapters.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from services.three_d.provider_interface import (
    OutputFormat,
    ProviderHealth,
    ProviderStatus,
    ThreeDCapability,
    ThreeDGenerationError,
    ThreeDProviderError,
    ThreeDRequest,
    ThreeDResponse,
    ThreeDTimeoutError,
)
from services.three_d.trellis.client import (
    BackendResult,
    BackendUnavailable,
    StubClient,
    TrellisBackendClient,
    build_backend,
)
from services.three_d.trellis.config import (
    TrellisBackend,
    TrellisConfig,
    TrellisQualityPreset,
)
from services.three_d.trellis.garment_aware import (
    GarmentCategory,
    build_garment_prompt_bundle,
)
from services.three_d.trellis.postprocess import MeshPostprocessor, PostprocessResult
from services.three_d.trellis.preprocess import PreprocessResult, TrellisPreprocessor

logger = logging.getLogger(__name__)


class TrellisProvider:
    """TRELLIS-backed 3D provider, conforming to :class:`I3DProvider`.

    The provider is opinionated for clothing imagery — it auto-classifies the
    garment category, builds a clothing-aware prompt, runs background removal,
    and decimates the mesh into a category-appropriate polycount.

    Lifecycle:
        provider = TrellisProvider(TrellisConfig.from_env())
        try:
            resp = await provider.generate_from_image(request)
        finally:
            await provider.close()
    """

    def __init__(
        self,
        config: TrellisConfig | None = None,
        *,
        backend: TrellisBackendClient | None = None,
        preprocessor: TrellisPreprocessor | None = None,
        postprocessor: MeshPostprocessor | None = None,
    ) -> None:
        self.config = config or TrellisConfig.from_env()
        self.config.ensure_dirs()
        self._backend = backend or build_backend(self.config)
        self._preprocessor = preprocessor or TrellisPreprocessor(self.config)
        self._postprocessor = postprocessor or MeshPostprocessor(self.config)

    # ---------------------------------------------------------------------
    # Identity
    # ---------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "trellis"

    @property
    def capabilities(self) -> list[ThreeDCapability]:
        caps = [ThreeDCapability.IMAGE_TO_3D, ThreeDCapability.TEXTURE_GENERATION]
        if self.config.backend == TrellisBackend.LOCAL:
            # text-to-3D requires the TRELLIS-text-large checkpoint;
            # advertise it conditionally so the factory routes correctly.
            caps.append(ThreeDCapability.TEXT_TO_3D)
        return caps

    # ---------------------------------------------------------------------
    # I3DProvider — text
    # ---------------------------------------------------------------------

    async def generate_from_text(self, request: ThreeDRequest) -> ThreeDResponse:
        correlation_id = request.correlation_id or str(uuid.uuid4())
        start = time.time()

        if not request.prompt:
            raise ThreeDProviderError(
                "TRELLIS text-to-3D requires a non-empty prompt",
                provider=self.name,
                correlation_id=correlation_id,
            )

        bundle = build_garment_prompt_bundle(
            product_name=request.product_name,
            declared_category=request.garment_type,
            collection=request.collection,
            user_prompt=request.prompt,
        )

        sampling = self._resolve_sampling(request)
        task_id = f"trellis_txt_{uuid.uuid4().hex[:12]}"
        logger.info(
            "TRELLIS text-to-3D",
            extra={
                "correlation_id": correlation_id,
                "category": bundle.category.value,
                "backend": self._backend.backend_name,
            },
        )

        try:
            backend_result = await self._call_backend_text(
                bundle.prompt,
                sampling_steps=sampling,
                seed=request.metadata.get("seed") or self.config.seed,
                correlation_id=correlation_id,
            )
        except BackendUnavailable as exc:
            raise ThreeDProviderError(
                str(exc),
                provider=self.name,
                correlation_id=correlation_id,
                retryable=False,
            ) from exc

        post = await self._postprocess(
            backend_result,
            category=bundle.category,
            request=request,
            correlation_id=correlation_id,
        )

        return self._build_response(
            task_id=task_id,
            request=request,
            backend_result=backend_result,
            post=post,
            extra_metadata={
                "garment_category": bundle.category.value,
                "prompt_used": bundle.prompt,
                "preprocess": None,
            },
            duration=time.time() - start,
            correlation_id=correlation_id,
        )

    # ---------------------------------------------------------------------
    # I3DProvider — image
    # ---------------------------------------------------------------------

    async def generate_from_image(self, request: ThreeDRequest) -> ThreeDResponse:
        correlation_id = request.correlation_id or str(uuid.uuid4())
        start = time.time()

        image_source = request.get_image_source()
        if not image_source:
            raise ThreeDProviderError(
                "TRELLIS image-to-3D requires image_url or image_path",
                provider=self.name,
                correlation_id=correlation_id,
            )

        local_image = await self._ensure_local_image(image_source, correlation_id)
        preprocess = await self._preprocess(local_image, correlation_id)

        bundle = build_garment_prompt_bundle(
            image_path=preprocess.image.path,
            image_size=(preprocess.image.width, preprocess.image.height),
            product_name=request.product_name,
            declared_category=request.garment_type,
            collection=request.collection,
            user_prompt=request.prompt,
        )

        sampling = self._resolve_sampling(request)
        task_id = f"trellis_img_{uuid.uuid4().hex[:12]}"

        logger.info(
            "TRELLIS image-to-3D",
            extra={
                "correlation_id": correlation_id,
                "category": bundle.category.value,
                "preprocess_quality": preprocess.quality_score,
                "backend": self._backend.backend_name,
            },
        )

        try:
            backend_result = await self._call_backend_image(
                preprocess.image.path,
                sampling=sampling,
                prompt_hint=bundle.prompt,
                seed=request.metadata.get("seed") or self.config.seed,
                correlation_id=correlation_id,
            )
        except BackendUnavailable as exc:
            raise ThreeDProviderError(
                str(exc),
                provider=self.name,
                correlation_id=correlation_id,
                retryable=False,
            ) from exc

        post = await self._postprocess(
            backend_result,
            category=bundle.category,
            request=request,
            correlation_id=correlation_id,
        )

        return self._build_response(
            task_id=task_id,
            request=request,
            backend_result=backend_result,
            post=post,
            extra_metadata={
                "garment_category": bundle.category.value,
                "prompt_hint": bundle.prompt,
                "preprocess": {
                    "quality_score": preprocess.quality_score,
                    "sharpness": preprocess.sharpness,
                    "background_removed": preprocess.image.background_removed,
                    "warnings": preprocess.warnings,
                },
                "post_warnings": post.warnings,
            },
            duration=time.time() - start,
            correlation_id=correlation_id,
        )

    # ---------------------------------------------------------------------
    # I3DProvider — health
    # ---------------------------------------------------------------------

    async def health_check(self) -> ProviderHealth:
        start = time.time()
        try:
            healthy, error = await self._backend.healthy()
        except Exception as exc:  # noqa: BLE001 — broad to satisfy contract
            healthy, error = False, str(exc)

        latency = (time.time() - start) * 1000
        return ProviderHealth(
            provider=self.name,
            status=ProviderStatus.AVAILABLE if healthy else ProviderStatus.UNAVAILABLE,
            capabilities=self.capabilities,
            latency_ms=latency,
            last_check=datetime.now(UTC),
            error_message=error,
        )

    async def close(self) -> None:
        await self._backend.close()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _resolve_sampling(self, request: ThreeDRequest):
        # Allow per-request override; default to config preset.
        preset = request.metadata.get("quality")
        if preset:
            try:
                return TrellisConfig(
                    backend=self.config.backend,
                    quality=TrellisQualityPreset(preset),
                ).sampling
            except ValueError:
                logger.warning("Unknown quality preset %s — using config default", preset)
        return self.config.sampling

    async def _preprocess(
        self,
        image_path: str,
        correlation_id: str,
    ) -> PreprocessResult:
        try:
            return await asyncio.to_thread(self._preprocessor.prepare, image_path)
        except Exception as exc:  # noqa: BLE001
            raise ThreeDProviderError(
                f"Preprocessing failed: {exc}",
                provider=self.name,
                correlation_id=correlation_id,
                retryable=False,
                cause=exc,
            ) from exc

    async def _postprocess(
        self,
        backend_result: BackendResult,
        *,
        category: GarmentCategory,
        request: ThreeDRequest,
        correlation_id: str,
    ) -> PostprocessResult:
        artifact_id = (
            request.metadata.get("artifact_id")
            or request.correlation_id
            or correlation_id[:12]
        )
        sampling = self._resolve_sampling(request)
        try:
            return await asyncio.to_thread(
                self._postprocessor.process,
                raw_glb=backend_result.glb_path,
                category=category,
                sampling=sampling,
                artifact_id=str(artifact_id),
            )
        except FileNotFoundError as exc:
            raise ThreeDGenerationError(
                f"Postprocess missing raw GLB: {exc}",
                provider=self.name,
                correlation_id=correlation_id,
            ) from exc

    async def _call_backend_image(
        self,
        image_path: str,
        *,
        sampling,
        prompt_hint: str,
        seed: int | None,
        correlation_id: str,
    ) -> BackendResult:
        attempts = self.config.retry_attempts
        delay = self.config.retry_backoff_seconds
        last_exc: Exception | None = None
        for attempt in range(attempts + 1):
            try:
                return await self._backend.generate_from_image(
                    image_path,
                    sampling=sampling,
                    prompt_hint=prompt_hint,
                    seed=seed,
                )
            except TimeoutError as exc:
                raise ThreeDTimeoutError(
                    f"TRELLIS timed out after {self.config.timeout_seconds}s",
                    provider=self.name,
                    timeout_seconds=self.config.timeout_seconds,
                    correlation_id=correlation_id,
                ) from exc
            except BackendUnavailable:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < attempts:
                    logger.warning(
                        "TRELLIS attempt %s failed: %s — retrying in %.1fs",
                        attempt + 1,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    delay *= 2

        raise ThreeDGenerationError(
            f"TRELLIS image-to-3D failed after {attempts + 1} attempts: {last_exc}",
            provider=self.name,
            correlation_id=correlation_id,
        ) from last_exc

    async def _call_backend_text(
        self,
        prompt: str,
        *,
        sampling_steps,
        seed: int | None,
        correlation_id: str,
    ) -> BackendResult:
        try:
            return await self._backend.generate_from_text(
                prompt,
                sampling=sampling_steps,
                seed=seed,
            )
        except TimeoutError as exc:
            raise ThreeDTimeoutError(
                "TRELLIS text-to-3D timed out",
                provider=self.name,
                timeout_seconds=self.config.timeout_seconds,
                correlation_id=correlation_id,
            ) from exc

    async def _ensure_local_image(
        self,
        image_source: str,
        correlation_id: str,
    ) -> str:
        """If the caller gave us a URL, download it; otherwise return the path."""
        if image_source.startswith(("http://", "https://")):
            return await asyncio.to_thread(
                _download_image,
                image_source,
                self.config.cache_dir,
            )
        if not Path(image_source).exists():
            raise ThreeDProviderError(
                f"Image not found: {image_source}",
                provider=self.name,
                correlation_id=correlation_id,
            )
        return image_source

    def _build_response(
        self,
        *,
        task_id: str,
        request: ThreeDRequest,
        backend_result: BackendResult,
        post: PostprocessResult,
        extra_metadata: dict,
        duration: float,
        correlation_id: str,
    ) -> ThreeDResponse:
        glb_path = Path(post.glb_path)
        relative_url = (
            f"/assets/3d-models-generated/{glb_path.name}"
            if "3d-models-generated" in str(glb_path)
            else None
        )

        metadata = {
            "backend": backend_result.backend,
            "backend_duration": backend_result.duration_seconds,
            "seed": backend_result.seed,
            "usdz_path": post.usdz_path,
            "thumbnail_path": post.thumbnail_path,
            "splat_path": backend_result.splat_path,
            "preview_path": backend_result.preview_path,
        }
        metadata.update(extra_metadata)
        metadata.update(backend_result.metadata)

        return ThreeDResponse(
            success=True,
            task_id=task_id,
            status="completed",
            model_url=relative_url,
            model_path=str(glb_path),
            thumbnail_url=(
                f"/assets/3d-models-generated/{Path(post.thumbnail_path).name}"
                if post.thumbnail_path
                else None
            ),
            output_format=OutputFormat.GLB,
            provider=self.name,
            duration_seconds=duration,
            polycount=post.polycount,
            file_size_bytes=post.file_size_bytes,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            correlation_id=correlation_id,
            metadata=metadata,
        )


# =============================================================================
# Helpers
# =============================================================================


def _download_image(url: str, cache_dir: str) -> str:
    import hashlib
    import urllib.request

    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    suffix = Path(url.split("?")[0]).suffix or ".jpg"
    dst = Path(cache_dir) / f"download_{digest}{suffix}"
    if dst.exists():
        return str(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as src, open(dst, "wb") as out:  # noqa: S310
        out.write(src.read())
    return str(dst)


# =============================================================================
# Test helper
# =============================================================================


def make_stub_provider(config: TrellisConfig | None = None) -> TrellisProvider:
    """Build a TrellisProvider wired to the deterministic stub backend."""
    cfg = config or TrellisConfig()
    cfg.ensure_dirs()
    return TrellisProvider(cfg, backend=StubClient(cfg))


__all__ = [
    "TrellisProvider",
    "make_stub_provider",
]
