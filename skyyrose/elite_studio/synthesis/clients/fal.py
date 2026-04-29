"""Thin async wrapper around ``fal_client`` with retry, timeout, structured logging.

Uses the ``AsyncClient.subscribe`` pattern so we get queue progress events
during the long-running FLUX calls. Exponential-backoff retry for transient
HTTP/timeout errors only — validation errors fail fast.

The compositor script (``scripts/run_compositor_pipeline.py``) uses the
synchronous ``fal_client.run`` pattern. This wrapper is async-first so we
can run multiple SKUs concurrently in a batch via ``asyncio.gather``.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Defer the fal_client import to runtime — keeps unit tests fast and lets us
# mock the module cleanly without an import-time hard dep.
_FAL = None


def _fal():
    """Lazy import of fal_client. Raises ImportError if package missing."""
    global _FAL
    if _FAL is None:
        import fal_client  # type: ignore[import-not-found]

        _FAL = fal_client
    return _FAL


class FalError(RuntimeError):
    """Raised when a fal.ai call fails terminally (after retries)."""


@dataclass
class FalResult:
    """Normalized fal.ai response."""

    images: list[str]  # output URLs
    seed: int | None = None
    raw: dict[str, Any] | None = None

    @property
    def primary_url(self) -> str:
        if not self.images:
            raise FalError("fal response contained no images")
        return self.images[0]


class FalClient:
    """Async fal.ai client with retry + timeout.

    Usage:
        client = FalClient()
        url = await client.upload(Path("techflat.jpg"))
        result = await client.subscribe(
            "fal-ai/flux-pro/kontext",
            arguments={"input_image": url, "prompt": "..."},
        )
    """

    DEFAULT_TIMEOUT_S = 300.0
    MAX_RETRIES = 3

    def __init__(
        self,
        *,
        timeout_s: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.timeout_s = timeout_s or self.DEFAULT_TIMEOUT_S
        self.max_retries = max_retries or self.MAX_RETRIES
        self._validate_credentials()

    @staticmethod
    def _validate_credentials() -> None:
        """fal_client reads FAL_KEY at runtime; warn early if missing."""
        if not os.environ.get("FAL_KEY") and not os.environ.get("FAL_KEY_ID"):
            logger.warning(
                "FAL_KEY not set in environment — fal.ai calls will fail. "
                "Set FAL_KEY in .env or export it before running."
            )

    async def upload(self, path: str | Path) -> str:
        """Upload a local file to fal CDN, return its URL.

        fal_client.upload_file is sync — wrap in to_thread so we don't block
        the event loop during what can be a multi-MB upload.
        """
        path = Path(path)
        if not path.is_file():
            raise FalError(f"upload source not found: {path}")
        try:
            url = await asyncio.to_thread(_fal().upload_file, str(path))
        except Exception as exc:
            raise FalError(f"upload of {path} failed: {exc}") from exc
        logger.debug("uploaded %s -> %s", path, url)
        return url

    async def upload_bytes(self, data: bytes, content_type: str = "image/png") -> str:
        """Upload raw bytes to fal CDN."""
        try:
            url = await asyncio.to_thread(_fal().upload, data, content_type=content_type)
        except Exception as exc:
            raise FalError(f"upload bytes failed: {exc}") from exc
        return url

    async def subscribe(
        self,
        endpoint: str,
        *,
        arguments: dict[str, Any],
        with_logs: bool = True,
    ) -> FalResult:
        """Submit a request and wait for the result, with retry on transient errors.

        ``subscribe`` is fal_client's queue-aware path — we get progress events
        and the final result without manually polling.
        """
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self._subscribe_once(endpoint, arguments, with_logs, attempt),
                    timeout=self.timeout_s,
                )
            except TimeoutError as exc:
                last_exc = exc
                logger.warning(
                    "fal call timed out (attempt %d/%d, endpoint=%s)",
                    attempt,
                    self.max_retries,
                    endpoint,
                )
            except FalError as exc:
                last_exc = exc
                # Validation / 4xx / content-policy errors don't get retried.
                if not _is_retryable(exc):
                    raise
                logger.warning(
                    "fal call failed transiently (attempt %d/%d, endpoint=%s): %s",
                    attempt,
                    self.max_retries,
                    endpoint,
                    exc,
                )
            except Exception as exc:  # pragma: no cover - safety net
                last_exc = exc
                logger.exception("unexpected fal client error")
                if not _is_retryable(exc):
                    raise FalError(f"non-retryable fal error: {exc}") from exc

            if attempt < self.max_retries:
                backoff = 2.0 * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        raise FalError(
            f"fal call failed after {self.max_retries} attempts: {last_exc}"
        ) from last_exc

    async def _subscribe_once(
        self,
        endpoint: str,
        arguments: dict[str, Any],
        with_logs: bool,
        attempt: int,
    ) -> FalResult:
        client = _fal().AsyncClient()

        def _on_update(status: Any) -> None:
            # Cheap structured log; subscribed events arrive as fal_client
            # status objects.
            logger.debug("fal queue update [%s attempt=%d]: %s", endpoint, attempt, status)

        try:
            raw = await client.subscribe(
                endpoint,
                arguments=arguments,
                with_logs=with_logs,
                on_queue_update=_on_update,
            )
        except Exception as exc:
            # Wrap fal_client errors uniformly so callers can branch on FalError.
            raise FalError(f"fal subscribe error on {endpoint}: {exc}") from exc

        return _normalize_response(raw)


def _is_retryable(exc: BaseException) -> bool:
    """Decide whether a fal exception should be retried.

    fal_client raises a small zoo of error classes. We treat HTTP 5xx,
    timeouts, and connection errors as retryable; everything else is fatal.
    """
    msg = str(exc).lower()
    if "timeout" in msg or "timed out" in msg:
        return True
    if "5" in msg and any(code in msg for code in ("500", "502", "503", "504")):
        return True
    return "connection" in msg or "network" in msg


def _normalize_response(raw: Any) -> FalResult:
    """Pull URLs + seed out of the fal response shape.

    Different endpoints return slightly different shapes (some have ``image``
    singular, some ``images`` plural, some include ``seed`` and some don't).
    Normalize to a single FalResult.
    """
    if not isinstance(raw, dict):
        raise FalError(f"unexpected fal response type: {type(raw).__name__}")

    urls: list[str] = []
    if "images" in raw and isinstance(raw["images"], list):
        for item in raw["images"]:
            if isinstance(item, dict) and "url" in item:
                urls.append(item["url"])
            elif isinstance(item, str):
                urls.append(item)
    elif "image" in raw:
        item = raw["image"]
        if isinstance(item, dict) and "url" in item:
            urls.append(item["url"])
        elif isinstance(item, str):
            urls.append(item)

    if not urls:
        raise FalError(f"fal response had no image URLs: keys={list(raw.keys())}")

    seed = raw.get("seed")
    if not isinstance(seed, int):
        seed = None

    return FalResult(images=urls, seed=seed, raw=raw)


def encode_image_to_data_url(image_bytes: bytes, mime: str = "image/png") -> str:
    """Inline-encode an image as a data URL (for endpoints that prefer base64)."""
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{b64}"
