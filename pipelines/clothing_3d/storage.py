"""Artifact storage for the clothing 3D pipeline.

A pipeline run can emit several files (GLB, USDZ, thumbnail, splat). The
storage layer takes that bundle, persists it somewhere durable, and returns
the URLs used by downstream consumers (web viewer, AR, analytics).

Two backends ship:

- :class:`LocalArtifactStore` — copies into ``./assets/3d-models-generated``
  and serves them via the existing FastAPI static mount. Default for dev.
- :class:`S3ArtifactStore` — uploads to S3-compatible object storage and
  returns signed URLs. Lazy-imports :mod:`boto3` so dev doesn't need it.
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# =============================================================================
# Bundle
# =============================================================================


@dataclass(slots=True)
class ArtifactBundle:
    """Files associated with a single pipeline run."""

    artifact_id: str
    glb_path: str
    usdz_path: str | None = None
    thumbnail_path: str | None = None
    splat_path: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class StoredArtifact:
    """Result of persisting a bundle."""

    artifact_id: str
    glb_url: str
    glb_path: str
    usdz_url: str | None = None
    usdz_path: str | None = None
    thumbnail_url: str | None = None
    thumbnail_path: str | None = None
    stored_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Protocol
# =============================================================================


@runtime_checkable
class ArtifactStore(Protocol):
    """Where pipeline artifacts go to live."""

    async def store(self, bundle: ArtifactBundle) -> StoredArtifact: ...


# =============================================================================
# Local store
# =============================================================================


class LocalArtifactStore:
    """Stores artifacts on the local filesystem and exposes URL-style paths.

    Files are already written to ``config.output_dir`` by the postprocessor;
    this store just records them and synthesizes URLs that match the FastAPI
    ``/assets/3d-models-generated`` static mount.

    Args:
        base_dir: Directory containing the artifacts. Defaults to
            ``$THREE_D_OUTPUT_DIR`` or ``./assets/3d-models-generated``.
        public_prefix: URL prefix where ``base_dir`` is mounted.
    """

    def __init__(
        self,
        *,
        base_dir: str | None = None,
        public_prefix: str = "/assets/3d-models-generated",
    ) -> None:
        self.base_dir = Path(
            base_dir or os.getenv("THREE_D_OUTPUT_DIR", "./assets/3d-models-generated")
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.public_prefix = public_prefix.rstrip("/")

    async def store(self, bundle: ArtifactBundle) -> StoredArtifact:
        glb_dst = self._move_into_base(
            bundle.glb_path, suffix=".glb", artifact_id=bundle.artifact_id
        )
        usdz_dst = (
            self._move_into_base(bundle.usdz_path, suffix=".usdz", artifact_id=bundle.artifact_id)
            if bundle.usdz_path
            else None
        )
        thumb_dst = (
            self._move_into_base(
                bundle.thumbnail_path, suffix=".png", artifact_id=f"{bundle.artifact_id}_preview"
            )
            if bundle.thumbnail_path
            else None
        )

        return StoredArtifact(
            artifact_id=bundle.artifact_id,
            glb_path=str(glb_dst),
            glb_url=self._public_url(glb_dst),
            usdz_path=str(usdz_dst) if usdz_dst else None,
            usdz_url=self._public_url(usdz_dst) if usdz_dst else None,
            thumbnail_path=str(thumb_dst) if thumb_dst else None,
            thumbnail_url=self._public_url(thumb_dst) if thumb_dst else None,
            metadata={"store": "local", "extra": bundle.extra},
        )

    def _move_into_base(self, src: str, *, suffix: str, artifact_id: str) -> Path:
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(src)

        # Already inside base_dir → no-op.
        try:
            src_path.resolve().relative_to(self.base_dir.resolve())
            return src_path
        except ValueError:
            pass

        dst = self.base_dir / f"{artifact_id}{suffix}"
        shutil.copy2(src_path, dst)
        return dst

    def _public_url(self, path: Path) -> str:
        return f"{self.public_prefix}/{path.name}"


# =============================================================================
# S3 store
# =============================================================================


class S3ArtifactStore:
    """S3 / S3-compatible object storage backend.

    Designed for CloudFlare R2, AWS S3, Cloudfront-fronted buckets, etc.

    Args:
        bucket: Bucket name.
        prefix: Key prefix (e.g. ``"3d/garments"``).
        public_base_url: If the bucket has a public CDN URL, signed URLs are
            replaced with this prefix; otherwise a presigned GET URL is used.
        signed_url_ttl_seconds: How long presigned URLs live (only when there
            is no ``public_base_url``).
    """

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str = "3d/garments",
        public_base_url: str | None = None,
        signed_url_ttl_seconds: int = 3600,
        region: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.public_base_url = public_base_url.rstrip("/") if public_base_url else None
        self.signed_url_ttl_seconds = signed_url_ttl_seconds
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import boto3  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError("S3ArtifactStore requires boto3 — pip install boto3") from e
        self._client = boto3.client("s3", region_name=self.region)
        return self._client

    async def store(self, bundle: ArtifactBundle) -> StoredArtifact:
        import asyncio

        return await asyncio.to_thread(self._store_sync, bundle)

    def _store_sync(self, bundle: ArtifactBundle) -> StoredArtifact:
        glb_key = self._upload(bundle.glb_path, f"{bundle.artifact_id}.glb", "model/gltf-binary")
        usdz_key = (
            self._upload(bundle.usdz_path, f"{bundle.artifact_id}.usdz", "model/vnd.usdz+zip")
            if bundle.usdz_path
            else None
        )
        thumb_key = (
            self._upload(
                bundle.thumbnail_path,
                f"{bundle.artifact_id}_preview.png",
                "image/png",
            )
            if bundle.thumbnail_path
            else None
        )

        return StoredArtifact(
            artifact_id=bundle.artifact_id,
            glb_path=bundle.glb_path,
            glb_url=self._url_for(glb_key),
            usdz_path=bundle.usdz_path,
            usdz_url=self._url_for(usdz_key) if usdz_key else None,
            thumbnail_path=bundle.thumbnail_path,
            thumbnail_url=self._url_for(thumb_key) if thumb_key else None,
            metadata={"store": "s3", "bucket": self.bucket, "prefix": self.prefix},
        )

    def _upload(self, path: str, name: str, content_type: str) -> str:
        client = self._get_client()
        key = f"{self.prefix}/{name}"
        client.upload_file(
            path,
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type, "CacheControl": "public,max-age=31536000"},
        )
        return key

    def _url_for(self, key: str) -> str:
        if self.public_base_url:
            return f"{self.public_base_url}/{key}"

        client = self._get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self.signed_url_ttl_seconds,
        )


__all__ = [
    "ArtifactBundle",
    "ArtifactStore",
    "LocalArtifactStore",
    "S3ArtifactStore",
    "StoredArtifact",
]
