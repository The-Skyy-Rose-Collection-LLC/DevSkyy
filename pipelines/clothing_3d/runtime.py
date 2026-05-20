"""One-call entry point for the clothing 3D pipeline.

Lets callers do this and have it work, from anywhere:

.. code-block:: python

    from pipelines.clothing_3d import generate

    result = await generate(
        image_path="hoodie.jpg",
        product_name="Black Rose Hoodie",
        garment_type="hoodie",
        collection="black_rose",
    )
    print(result.glb_url)

What this module does on your behalf:

- Lazy-builds a process-wide :class:`ClothingPipeline` singleton — first call
  pays the init cost; every subsequent call reuses it.
- Auto-resolves the TRELLIS backend when one isn't explicitly configured:
  walks a priority list (configured → HF Space → Replicate → Local → Stub)
  and picks the first one that passes :meth:`healthy`. Logs the choice.
- Wraps the run in the shared :class:`IdempotencyCache` + :class:`CostQuota`
  unless the caller opts out.
- Validates inputs before dispatching (file existence, URL shape, prompt
  presence) so you get a clear ``ValueError`` instead of a 30-second
  pipeline failure.
- Auto-creates the output / cache dirs.
- Registers an ``atexit`` hook to close the pipeline cleanly.

This module is the "happy path." If you need fine-grained control (custom
event bus, alternate stores, batch parallelism), use :class:`ClothingPipeline`
directly — :func:`generate` builds on top of it, never around it.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import atexit
import logging
import os
from pathlib import Path
from typing import Any

from pipelines.clothing_3d.models import (
    PipelineRequest,
    PipelineResult,
    PipelineStatus,
)
from pipelines.clothing_3d.observability import configure_logging, metrics_event_subscriber
from pipelines.clothing_3d.pipeline import ClothingPipeline
from pipelines.clothing_3d.reliability import (
    CostQuota,
    IdempotencyCache,
    QuotaExceededError,
)
from services.three_d.trellis.client import StubClient, build_backend
from services.three_d.trellis.config import (
    TrellisBackend,
    TrellisConfig,
    TrellisQualityPreset,
)
from services.three_d.trellis.provider import TrellisProvider

logger = logging.getLogger(__name__)


# =============================================================================
# Module-level state
# =============================================================================


_runtime: PipelineRuntime | None = None
_runtime_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _runtime_lock
    if _runtime_lock is None:
        _runtime_lock = asyncio.Lock()
    return _runtime_lock


# =============================================================================
# Backend auto-resolution
# =============================================================================


def _backend_explicitly_set() -> bool:
    return "TRELLIS_BACKEND" in os.environ


def _strict_mode() -> bool:
    """When true, never fall back from the configured backend.

    Production deploys should set ``CLOTHING_3D_STRICT=true`` so misconfig
    surfaces as a loud failure instead of a silent fallback to stub.
    """
    return os.getenv("CLOTHING_3D_STRICT", "false").lower() in {"true", "1", "yes"}


def _allow_stub_fallback() -> bool:
    """Whether the resolver may fall back to the deterministic Stub client.

    Defaults to ``True`` outside strict mode so dev/notebook/sandbox use
    "just works" without paying for a real backend. In strict mode this is
    forced off.
    """
    if _strict_mode():
        return False
    return os.getenv("CLOTHING_3D_ALLOW_STUB", "true").lower() in {"true", "1", "yes"}


def _fallback_order(preferred: TrellisBackend) -> list[TrellisBackend]:
    """Resolve the backend probe order.

    Always begins with the preferred backend (so the configured choice is
    tried first), then walks a sane fallback list, deduplicated.
    """
    chain: list[TrellisBackend] = [preferred]
    for b in (TrellisBackend.HF_SPACE, TrellisBackend.REPLICATE, TrellisBackend.LOCAL):
        if b not in chain:
            chain.append(b)
    return chain


async def _resolve_backend(config: TrellisConfig) -> tuple[Any, TrellisBackend, str | None]:
    """Probe backends; return ``(client, backend_enum, fallback_reason)``.

    If the configured backend is healthy, returns it. Otherwise walks the
    fallback list. ``fallback_reason`` is set whenever we land on something
    different from ``config.backend``.
    """
    preferred = config.backend
    explicit = _backend_explicitly_set()
    strict = _strict_mode()

    # Strict + explicit → no probing. Build and use as-is; surface any failures.
    if strict and explicit:
        client = build_backend(config)
        return client, preferred, None

    last_error: str | None = None
    for candidate in _fallback_order(preferred):
        candidate_config = _config_with_backend(config, candidate)
        try:
            client = build_backend(candidate_config)
        except Exception as exc:  # noqa: BLE001
            last_error = f"{candidate.value}: build failed — {exc}"
            logger.debug("backend.build_failed %s", last_error)
            continue
        try:
            healthy, err = await client.healthy()
        except Exception as exc:  # noqa: BLE001 — backend must not crash startup
            healthy, err = False, str(exc)
        if healthy:
            reason = None if candidate is preferred else (
                f"preferred backend '{preferred.value}' unavailable "
                f"({last_error or err or 'health check failed'}); using '{candidate.value}'"
            )
            return client, candidate, reason
        await client.close()
        last_error = f"{candidate.value}: {err}"
        logger.debug("backend.unhealthy %s", last_error)

    if _allow_stub_fallback():
        stub = StubClient(config)
        return stub, TrellisBackend.HF_SPACE, (
            f"no backend reachable ({last_error}); falling back to in-process Stub. "
            "Set CLOTHING_3D_STRICT=true to disable this fallback in production."
        )

    raise RuntimeError(
        f"clothing_3d: no TRELLIS backend reachable. Last error: {last_error}. "
        f"Install the backend client (`pip install gradio_client` for HF Space) "
        f"or set CLOTHING_3D_ALLOW_STUB=true to use the deterministic stub."
    )


def _config_with_backend(base: TrellisConfig, backend: TrellisBackend) -> TrellisConfig:
    """Return a shallow copy of ``base`` with ``backend`` swapped in.

    Avoids mutating the caller's config and avoids reading ``__dict__``
    (slotted dataclasses don't have one).
    """
    fields = {
        attr: getattr(base, attr)
        for attr in base.__slots__  # type: ignore[attr-defined]
    }
    fields["backend"] = backend
    return TrellisConfig(**fields)


# =============================================================================
# PipelineRuntime
# =============================================================================


class PipelineRuntime:
    """Process-wide pipeline manager.

    Holds the singleton :class:`ClothingPipeline`, the shared
    :class:`IdempotencyCache`, and the shared :class:`CostQuota`. Builds
    them lazily on first use; ``close()`` is registered with :mod:`atexit`.
    """

    def __init__(self) -> None:
        self._pipeline: ClothingPipeline | None = None
        self._cache: IdempotencyCache | None = None
        self._quota: CostQuota | None = None
        self._lock = asyncio.Lock()
        self._closed = False
        self._fallback_reason: str | None = None
        self._resolved_backend: TrellisBackend | None = None

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    async def get_pipeline(self) -> ClothingPipeline:
        if self._pipeline is not None and not self._closed:
            return self._pipeline
        async with self._lock:
            if self._pipeline is not None and not self._closed:
                return self._pipeline
            self._pipeline = await self._build_pipeline()
            self._closed = False
            return self._pipeline

    async def _build_pipeline(self) -> ClothingPipeline:
        config = TrellisConfig.from_env()
        config.ensure_dirs()

        client, resolved_backend, fallback_reason = await _resolve_backend(config)
        self._resolved_backend = resolved_backend
        self._fallback_reason = fallback_reason
        if fallback_reason:
            logger.warning("clothing_3d.backend.fallback %s", fallback_reason)
        else:
            logger.info(
                "clothing_3d.backend.resolved backend=%s quality=%s",
                resolved_backend.value,
                config.quality.value,
            )

        # Build provider with the resolved client (skips the factory's
        # second probe — we already did it).
        config_for_provider = _config_with_backend(config, resolved_backend)
        provider = TrellisProvider(config_for_provider, backend=client)

        pipeline = ClothingPipeline(config=config_for_provider, provider=provider)
        # Wire pipeline events into Prometheus metrics by default.
        pipeline.event_bus.subscribe(metrics_event_subscriber())
        return pipeline

    def get_idempotency_cache(self) -> IdempotencyCache:
        if self._cache is None:
            ttl = int(os.getenv("CLOTHING_3D_CACHE_TTL_SECONDS", "86400"))
            enabled = os.getenv("CLOTHING_3D_CACHE", "true").lower() in {"true", "1", "yes"}
            self._cache = IdempotencyCache(ttl_seconds=ttl, enabled=enabled)
        return self._cache

    def get_cost_quota(self) -> CostQuota:
        if self._quota is None:
            caps: dict[str, float] = {}
            for backend in ("replicate", "modal"):
                env_key = f"CLOTHING_3D_{backend.upper()}_USD_CAP"
                raw = os.getenv(env_key)
                if raw:
                    try:
                        caps[backend] = float(raw)
                    except ValueError:
                        logger.warning("ignoring non-numeric %s=%r", env_key, raw)
            self._quota = CostQuota(caps_usd=caps)
        return self._quota

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def resolved_backend(self) -> TrellisBackend | None:
        return self._resolved_backend

    @property
    def fallback_reason(self) -> str | None:
        return self._fallback_reason

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        if self._pipeline is None or self._closed:
            return
        await self._pipeline.close()
        self._closed = True


def get_runtime() -> PipelineRuntime:
    """Return the process-wide runtime singleton."""
    global _runtime
    if _runtime is None:
        _runtime = PipelineRuntime()
        atexit.register(_atexit_close)
    return _runtime


def _atexit_close() -> None:
    """Best-effort cleanup at interpreter exit."""
    if _runtime is None:
        return
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_runtime.close())
        loop.close()
    except Exception:  # noqa: BLE001
        pass


async def reset_runtime() -> None:
    """Discard the runtime singleton. Tests only."""
    global _runtime
    if _runtime is not None:
        await _runtime.close()
        _runtime = None


# =============================================================================
# Top-level entry point
# =============================================================================


async def generate(
    *,
    image_path: str | Path | None = None,
    image_url: str | None = None,
    prompt: str | None = None,
    product_name: str | None = None,
    product_sku: str | None = None,
    collection: str | None = None,
    garment_type: str | None = None,
    quality: TrellisQualityPreset | str = TrellisQualityPreset.STANDARD,
    skip_qc: bool = False,
    use_cache: bool = True,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> PipelineResult:
    """Run the clothing 3D pipeline. One call. No setup required.

    Args:
        image_path: Local image path. Mutually exclusive with ``image_url`` and ``prompt``.
        image_url: Public image URL. Mutually exclusive with ``image_path`` and ``prompt``.
        prompt: Text description (requires LOCAL backend with text-large weights).
        product_name: SKU display name (e.g. ``"Black Rose Hoodie"``).
        product_sku: Optional catalog SKU; used as artifact_id when present.
        collection: Brand collection slug (``signature`` | ``black_rose`` | ``love_hurts`` | ``kids_capsule``).
        garment_type: Override the auto-classifier. Strongly recommended when known.
        quality: ``draft`` | ``standard`` | ``production`` (string or enum).
        skip_qc: Bypass the QC gate (returns the artifact regardless of polycount/size).
        use_cache: When ``True`` and an identical request succeeded recently, return the cached result.
        correlation_id: Optional trace ID.
        metadata: Free-form extras propagated through stage reports.

    Returns:
        :class:`PipelineResult` with ``status``, ``glb_url``, ``usdz_url``,
        ``thumbnail_url``, per-stage timing, and full metadata.

    Raises:
        ValueError: when inputs are invalid (missing image / prompt, bad enum value).
        QuotaExceededError: when the configured backend cost cap is exhausted.
        RuntimeError: when no backend is reachable and stub fallback is disabled.
    """
    request = _build_request(
        image_path=image_path,
        image_url=image_url,
        prompt=prompt,
        product_name=product_name,
        product_sku=product_sku,
        collection=collection,
        garment_type=garment_type,
        quality=quality,
        skip_qc=skip_qc,
        correlation_id=correlation_id,
        metadata=metadata,
    )

    runtime = get_runtime()
    pipeline = await runtime.get_pipeline()
    quota = runtime.get_cost_quota()
    cache = runtime.get_idempotency_cache()

    # Cost guard runs BEFORE dispatch so a quota hit doesn't burn the backend call.
    backend = (runtime.resolved_backend or pipeline.provider.config.backend).value
    try:
        quota.charge(backend)
    except QuotaExceededError:
        raise

    if not use_cache:
        return await pipeline.run(request)

    result, _hit = await cache.get_or_run(request, runner=pipeline.run)
    return result


def _build_request(
    *,
    image_path: str | Path | None,
    image_url: str | None,
    prompt: str | None,
    product_name: str | None,
    product_sku: str | None,
    collection: str | None,
    garment_type: str | None,
    quality: TrellisQualityPreset | str,
    skip_qc: bool,
    correlation_id: str | None,
    metadata: dict[str, Any] | None,
) -> PipelineRequest:
    sources = sum(1 for x in (image_path, image_url, prompt) if x)
    if sources == 0:
        raise ValueError("generate() requires one of: image_path, image_url, prompt")
    if sources > 1:
        raise ValueError("generate() accepts only one of: image_path, image_url, prompt")

    if image_path is not None:
        p = Path(image_path)
        if not p.exists():
            raise ValueError(f"image_path not found: {image_path}")
        if not p.is_file():
            raise ValueError(f"image_path is not a regular file: {image_path}")
        image_path = str(p)

    if image_url is not None and not image_url.startswith(("http://", "https://")):
        raise ValueError(f"image_url must start with http:// or https://, got: {image_url[:64]}")

    quality_enum = (
        quality if isinstance(quality, TrellisQualityPreset) else TrellisQualityPreset(str(quality))
    )

    return PipelineRequest(
        image_path=image_path,
        image_url=image_url,
        prompt=prompt,
        product_name=product_name,
        product_sku=product_sku,
        collection=collection,
        garment_type=garment_type,
        quality=quality_enum,
        skip_qc=skip_qc,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )


# =============================================================================
# Preflight
# =============================================================================


async def preflight() -> dict[str, Any]:
    """Report what's installed, what backend will be used, what's missing.

    Call this from your service startup to surface misconfig BEFORE the
    first user request. Returns a dict suitable for JSON serialization;
    log it or emit it to your readiness endpoint.

    Example:
        >>> report = await preflight()
        >>> if not report["ready"]:
        ...     raise SystemExit(f"clothing_3d not ready: {report['issues']}")
    """
    issues: list[str] = []
    deps: dict[str, bool] = {
        "pillow": _module_present("PIL.Image"),
        "trimesh": _module_present("trimesh"),
        "rembg": _module_present("rembg"),
        "gradio_client": _module_present("gradio_client"),
        "redis": _module_present("redis"),
        "prometheus_client": _module_present("prometheus_client"),
        "boto3": _module_present("boto3"),
        "replicate": _module_present("replicate"),
    }

    if not deps["pillow"]:
        issues.append("pillow missing — required for input preprocessing")

    config = TrellisConfig.from_env()
    backend_health: dict[str, dict[str, Any]] = {}
    try:
        client, resolved, reason = await _resolve_backend(config)
        await client.close()
        if reason:
            issues.append(reason)
    except Exception as exc:  # noqa: BLE001
        issues.append(f"backend resolution failed: {exc}")
        resolved = None
        reason = None

    backend_health["configured"] = {"backend": config.backend.value}
    if resolved:
        backend_health["resolved"] = {"backend": resolved.value, "fallback_reason": reason}

    return {
        "ready": not any("missing" in i or "failed" in i for i in issues),
        "issues": issues,
        "config": {
            "backend": config.backend.value,
            "quality": config.quality.value,
            "output_dir": config.output_dir,
            "cache_dir": config.cache_dir,
            "export_usdz": config.export_usdz_for_ios,
            "strict_mode": _strict_mode(),
            "stub_fallback_allowed": _allow_stub_fallback(),
        },
        "dependencies": deps,
        "backends": backend_health,
    }


def _module_present(name: str) -> bool:
    import importlib.util

    try:
        return importlib.util.find_spec(name) is not None
    except Exception:  # noqa: BLE001 — defensive
        return False


# =============================================================================
# Convenience configuration
# =============================================================================


def configure(
    *,
    backend: TrellisBackend | str | None = None,
    quality: TrellisQualityPreset | str | None = None,
    output_dir: str | None = None,
    strict: bool | None = None,
    enable_json_logs: bool | None = None,
    log_level: str | None = None,
) -> None:
    """Set defaults at process start. Must be called BEFORE :func:`generate`.

    Equivalent to setting env vars then importing — provided so callers don't
    have to mutate ``os.environ`` themselves. Re-calling after :func:`generate`
    has run is a no-op (the singleton is already built).
    """
    if backend is not None:
        os.environ["TRELLIS_BACKEND"] = (
            backend.value if isinstance(backend, TrellisBackend) else str(backend)
        )
    if quality is not None:
        os.environ["TRELLIS_QUALITY"] = (
            quality.value if isinstance(quality, TrellisQualityPreset) else str(quality)
        )
    if output_dir is not None:
        os.environ["TRELLIS_OUTPUT_DIR"] = output_dir
        os.environ["THREE_D_OUTPUT_DIR"] = output_dir
    if strict is not None:
        os.environ["CLOTHING_3D_STRICT"] = "true" if strict else "false"
    if log_level is not None:
        configure_logging(level=log_level, json_format=enable_json_logs)
    elif enable_json_logs is not None:
        configure_logging(level=os.getenv("LOG_LEVEL", "INFO"), json_format=enable_json_logs)


__all__ = [
    "PipelineRuntime",
    "configure",
    "generate",
    "get_runtime",
    "preflight",
    "reset_runtime",
]
