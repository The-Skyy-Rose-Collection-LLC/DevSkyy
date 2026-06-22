"""Phase 18 — Batch WooCommerce upload of approved ghost-mannequin images.

Pure library + Protocol-based WC client adapter. The CLI in
scripts/upload_approved.py owns the STOP AND SHOW gate; this module owns
manifest construction, async preview, batch upload, and verification.

Public surface:
    build_manifest(*, root=None, catalog_rows=None) -> UploadManifest
    preview_manifest(client, manifest) -> list[PreviewRow]            # async, READ-ONLY
    upload_batch(client, manifest, *, dry_run=False) -> list[UploadResult]  # async, WRITES
    format_manifest_table(rows) -> str
    format_results_table(results) -> str
    WCClient (Protocol)
    WooCommerceUploader  # production adapter wrapping wordpress.products.WooCommerceProducts
    StopAndShowError, UploadError
"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.parse import urlparse

# Repo-root import shim so this module works whether the caller is the CLI
# (which sets sys.path) or pytest (which uses installed package mode).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402

GHOST_REL = "renders/ghost-mannequin"
APPROVED_SUBDIR = "approved"
GHOST_FILENAME_FMT = "{sku}-ghost-front.webp"
SKIPPED_JSON = "SKIPPED.json"
UPLOAD_LOG_JSON = "upload_log.json"
APPROVED_PUBLIC_PREFIX = "renders/ghost-mannequin/approved"  # CSV-stored value root

# Defense-in-depth: Phase 17 review.py enforces this same regex on what lands
# in approved/, but this module must independently validate so a corrupted CSV
# or a manually-placed file can never reach the WC API.
_SKU_RE = re.compile(r"^[a-z]{2,4}-\d{3}$")

# Strict filename allowlist for Content-Disposition header to prevent
# quote-boundary breakout and CRLF injection.
_FILENAME_SAFE_RE = re.compile(r"^[A-Za-z0-9._-]+$")

# WC writes only ever go to hosts on this list. Misconfigured env vars or
# typos cannot exfiltrate consumer_key/secret to an unintended host.
_SITE_URL_ALLOWLIST = frozenset({"skyyrose.co", "www.skyyrose.co", "public-api.wordpress.com"})

# Patterns to scrub from WC error bodies before they enter logs or the audit
# trail. WC plugins in debug mode sometimes echo request metadata back to the
# client, including credentials. Two regexes are needed because
# "Authorization: Bearer <jwt>" carries the secret in the SECOND token, not
# the first.
_AUTH_SCRUB_RE = re.compile(r"authorization[=:\s]+(?:bearer\s+)?\S+", re.IGNORECASE)
_CREDENTIAL_SCRUB_RE = re.compile(
    r"(consumer_key|consumer_secret|password)[=:\s]+\S+", re.IGNORECASE
)

ReadyStatus = Literal["READY", "ALREADY_SYNCED", "PRODUCT_NOT_FOUND"]
UploadStatus = Literal[
    "UPLOADED",
    "ALREADY_SYNCED",
    "FAILED",
    "DRY_RUN",
    "SKIPPED",
    "PRODUCT_NOT_FOUND",
    "VERIFICATION_FAILED",
]

_log = logging.getLogger(__name__)


# ─────────────────────────── exceptions ──────────────────────────────────────


class StopAndShowError(Exception):
    """Raised when the manifest is empty or the user declines confirmation."""


class UploadError(Exception):
    """Raised on unrecoverable WC REST failure for a single SKU."""


def _image_basename_matches(current_url: str, expected_basename: str) -> bool:
    """True iff the WC media URL's path ends with our expected filename.

    Parses the URL so a cache-busting query string (?v=2, ?ts=…) does not
    cause a re-upload of an already-correct image. Uses path-aware match
    (not substring) to reject crafted URLs where our basename is a fragment.
    """
    if not current_url:
        return False
    try:
        parsed_path = urlparse(current_url).path
    except ValueError:
        return False
    return Path(parsed_path).name == expected_basename


def _scrub_credentials(text: str) -> str:
    """Strip credential-like tokens from a WC error body before logging.

    Defense against a debug-mode WC plugin echoing consumer_key/secret in
    its error response, which would otherwise be persisted to upload_log.json.
    Handles both single-token (`password=hunter2`) and two-token Authorization
    headers (`Authorization: Bearer <jwt>`).
    """
    text = _AUTH_SCRUB_RE.sub("Authorization=***", text)
    text = _CREDENTIAL_SCRUB_RE.sub(r"\1=***", text)
    return text


def _validate_site_url(site_url: str) -> None:
    """Reject misconfigured WC site_url before any HTTP call carries credentials.

    Raises UploadError on: empty string, non-HTTPS scheme, missing host,
    host not in the production allowlist, embedded credentials, or explicit
    non-default port. Set SKYYROSE_SITE_URL_ALLOWLIST env var (comma-separated)
    to extend the list at runtime if needed.
    """
    if not site_url:
        raise UploadError("site_url is empty — set WORDPRESS_URL / WP_SITE_URL env")
    parsed = urlparse(site_url)
    if parsed.scheme != "https":
        raise UploadError(f"site_url must use https:// scheme; got {site_url!r}")
    if parsed.username or parsed.password:
        raise UploadError("site_url must not embed user:pass@ credentials")
    if parsed.port is not None:
        raise UploadError(f"site_url must not specify a non-default port; got :{parsed.port}")
    host = (parsed.hostname or "").lower()
    if not host:
        raise UploadError(f"site_url is missing host: {site_url!r}")
    extra = os.environ.get("SKYYROSE_SITE_URL_ALLOWLIST", "")
    allowed = _SITE_URL_ALLOWLIST | {h.strip().lower() for h in extra.split(",") if h.strip()}
    if host not in allowed:
        raise UploadError(
            f"site_url host {host!r} not in allowlist {sorted(allowed)}; "
            "extend via SKYYROSE_SITE_URL_ALLOWLIST env (comma-separated)"
        )


# ─────────────────────────── data contracts ──────────────────────────────────


@dataclass(frozen=True)
class UploadEntry:
    sku: str
    source_path: Path


@dataclass(frozen=True)
class SkippedEntry:
    sku: str
    reason: str


@dataclass(frozen=True)
class UploadManifest:
    entries: list[UploadEntry]
    skipped: list[SkippedEntry]
    generated_at: str


@dataclass(frozen=True)
class PreviewRow:
    sku: str
    source_path: Path
    product_id: int | None
    current_image_url: str | None
    status: ReadyStatus


@dataclass(frozen=True)
class UploadResult:
    sku: str
    product_id: int | None
    media_id: int | None
    source_url: str | None
    status: UploadStatus
    verified: bool
    error: str | None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


# ─────────────────────────── WC client protocol ──────────────────────────────


class WCClient(Protocol):
    """Minimum surface Phase 18 needs from a WooCommerce client.

    The production adapter is `WooCommerceUploader` below. Tests inject a
    fake that implements these four methods.
    """

    async def find_product_id_by_sku(self, sku: str) -> int | None: ...

    async def get_product_images(self, product_id: int) -> list[dict[str, Any]]: ...

    async def upload_media(self, file_path: Path, alt_text: str = "") -> dict[str, Any]: ...

    async def set_product_image(
        self, product_id: int, media_id: int, source_url: str
    ) -> dict[str, Any]: ...


# ─────────────────────────── manifest builder (pure) ─────────────────────────


def _resolve_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    return _REPO_ROOT


def _load_skipped_set(approved_dir: Path) -> set[str]:
    """Read SKIPPED.json from renders/ghost-mannequin/ if present.

    Returns the set of out-of-scope SKUs (e.g. sg-007, lh-005) that Phase 14
    preflight flagged as accessories. Empty set if file is missing or malformed.
    """
    skipped_path = approved_dir.parent / SKIPPED_JSON
    if not skipped_path.exists():
        return set()
    try:
        with skipped_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        _log.warning("could not read %s (%s); treating as empty", skipped_path, exc)
        return set()
    if not isinstance(data, dict):
        return set()
    skipped_list = data.get("skipped", [])
    if not isinstance(skipped_list, list):
        return set()
    out: set[str] = set()
    for item in skipped_list:
        if isinstance(item, dict) and isinstance(item.get("sku"), str):
            out.add(item["sku"])
    return out


def _classify_sku(
    sku: str,
    row: dict[str, str],
    approved_dir: Path,
    out_of_scope: set[str],
) -> UploadEntry | SkippedEntry:
    """Per-SKU classifier — pure, no I/O beyond the single is_file() check.

    Returns an UploadEntry if the SKU is upload-eligible, else a
    SkippedEntry with the first reason that fails.
    """
    if not _SKU_RE.fullmatch(sku):
        return SkippedEntry(sku=sku, reason=f"invalid SKU format (rejected by {_SKU_RE.pattern})")
    if sku in out_of_scope:
        return SkippedEntry(sku=sku, reason="in SKIPPED.json (out-of-scope)")
    if row.get("published", "").strip() != "1":
        return SkippedEntry(sku=sku, reason="published != 1")
    candidate = approved_dir / GHOST_FILENAME_FMT.format(sku=sku)
    if not candidate.is_file():
        return SkippedEntry(sku=sku, reason="no approved file")
    return UploadEntry(sku=sku, source_path=candidate)


def build_manifest(
    *,
    root: Path | str | None = None,
    catalog_rows: list[dict[str, str]] | None = None,
) -> UploadManifest:
    """Scan approved/ + cross-reference catalog; return manifest of upload-eligible SKUs.

    Pure — no network. A SKU is included iff:
      1. `approved/{sku}-ghost-front.webp` exists
      2. CSV row has matching sku
      3. CSV row.published == "1"
      4. SKU is not in SKIPPED.json
    """
    base = _resolve_root(root)
    approved_dir = base / GHOST_REL / APPROVED_SUBDIR
    rows = catalog_rows if catalog_rows is not None else _read_catalog_safe(base)
    rows_by_sku: dict[str, dict[str, str]] = {r["sku"]: r for r in rows if r.get("sku")}
    out_of_scope = _load_skipped_set(approved_dir)

    if not approved_dir.is_dir():
        return UploadManifest(
            entries=[],
            skipped=[SkippedEntry(sku=sku, reason="no approved/ directory") for sku in rows_by_sku],
            generated_at=datetime.now(UTC).isoformat(),
        )

    entries: list[UploadEntry] = []
    skipped: list[SkippedEntry] = []
    for sku, row in rows_by_sku.items():
        result = _classify_sku(sku, row, approved_dir, out_of_scope)
        (entries if isinstance(result, UploadEntry) else skipped).append(result)  # type: ignore[arg-type]

    return UploadManifest(
        entries=sorted(entries, key=lambda e: e.sku),
        skipped=sorted(skipped, key=lambda s: s.sku),
        generated_at=datetime.now(UTC).isoformat(),
    )


def _read_catalog_safe(root: Path) -> list[dict[str, str]]:
    """Wrap read_catalog_rows() so a missing catalog yields [] rather than raising.

    The CLI should still treat empty manifest as an error, but the library
    layer must not raise on read so dry-run can show a useful message.
    """
    try:
        return read_catalog_rows()
    except FileNotFoundError:
        return []
    except Exception as exc:
        _log.warning("catalog read failed: %s", exc)
        return []


# ─────────────────────────── async preview (read-only) ───────────────────────


# Read-only preview concurrency cap. WC enforces ~25 req/sec; 5 leaves headroom.
_PREVIEW_CONCURRENCY = 5


def _preview_not_found(entry: UploadEntry) -> PreviewRow:
    return PreviewRow(
        sku=entry.sku,
        source_path=entry.source_path,
        product_id=None,
        current_image_url=None,
        status="PRODUCT_NOT_FOUND",
    )


async def _resolve_preview_row(
    client: WCClient, entry: UploadEntry, semaphore: asyncio.Semaphore
) -> PreviewRow:
    """Async per-entry preview resolver — read-only WC calls. Extracted from
    preview_manifest to keep that function under 50 lines."""
    async with semaphore:
        try:
            product_id = await client.find_product_id_by_sku(entry.sku)
        except Exception as exc:
            _log.warning("preview: SKU lookup failed for %s: %s", entry.sku, exc)
            return _preview_not_found(entry)
        if product_id is None:
            return _preview_not_found(entry)
        try:
            images = await client.get_product_images(product_id)
        except Exception as exc:
            _log.warning("preview: image fetch failed for %s: %s", entry.sku, exc)
            images = []
        current = images[0].get("src") if images else None
        # URL-path-aware match (not substring) so a crafted URL cannot inject
        # our basename as a fragment, and so cache-busting query strings
        # don't cause spurious re-uploads.
        status: ReadyStatus = (
            "ALREADY_SYNCED"
            if current and _image_basename_matches(current, entry.source_path.name)
            else "READY"
        )
        return PreviewRow(
            sku=entry.sku,
            source_path=entry.source_path,
            product_id=product_id,
            current_image_url=current,
            status=status,
        )


async def preview_manifest(client: WCClient, manifest: UploadManifest) -> list[PreviewRow]:
    """Resolve SKU → product_id and fetch current image. Read-only, gated BEFORE writes.

    Concurrency bounded by `_PREVIEW_CONCURRENCY` so a 28-SKU run doesn't
    hammer the WC API.
    """
    semaphore = asyncio.Semaphore(_PREVIEW_CONCURRENCY)
    return await asyncio.gather(
        *(_resolve_preview_row(client, e, semaphore) for e in manifest.entries)
    )


# ─────────────────────────── upload batch (writes) ───────────────────────────


async def upload_batch(
    client: WCClient,
    manifest: UploadManifest,
    *,
    dry_run: bool = False,
) -> list[UploadResult]:
    """Upload approved/ files to WC. Per-SKU atomic: POST media → PUT product → GET verify.

    Failures collected, not raised — the result list contains one entry per
    manifest SKU with explicit status. Sequential to keep audit log ordered
    and avoid WC rate limits during multi-step per-SKU operations.
    """
    results: list[UploadResult] = []
    for entry in manifest.entries:
        if dry_run:
            results.append(
                UploadResult(
                    sku=entry.sku,
                    product_id=None,
                    media_id=None,
                    source_url=None,
                    status="DRY_RUN",
                    verified=False,
                    error=None,
                )
            )
            continue
        results.append(await _upload_one(client, entry))
    return results


def _validate_source(entry: UploadEntry, product_id: int) -> UploadResult | None:
    """Per-file safety gates: existence, symlink refusal, structural containment.

    Returns a FAILED UploadResult if any check rejects the source. Returns
    None if the file is safe to upload. Extracted from _upload_one to keep
    that function under the 50-line guideline and to enable direct testing.

    Containment is checked by structural directory naming: resolved path's
    last two directory components must be `ghost-mannequin/approved`. This
    is independent of root and not tautological with `parent.resolve()`.
    """
    if not entry.source_path.is_file():
        return _failed(entry.sku, product_id=product_id, error="source file vanished")
    if entry.source_path.is_symlink():
        return _failed(
            entry.sku,
            product_id=product_id,
            error="source is a symlink — refused for safety",
        )
    resolved = entry.source_path.resolve()
    if resolved.parent.name != APPROVED_SUBDIR or resolved.parent.parent.name != "ghost-mannequin":
        return _failed(
            entry.sku,
            product_id=product_id,
            error=f"source not inside renders/ghost-mannequin/approved/: {resolved}",
        )
    return None


async def _resolve_product_id(client: WCClient, sku: str) -> tuple[int | None, UploadResult | None]:
    """Look up product_id by SKU. Returns (id, None) on success;
    (None, UploadResult) if the SKU is missing or the call raised."""
    try:
        product_id = await client.find_product_id_by_sku(sku)
    except Exception as exc:
        return None, _failed(sku, error=f"sku lookup failed: {exc}")
    if product_id is None:
        return None, UploadResult(
            sku=sku,
            product_id=None,
            media_id=None,
            source_url=None,
            status="PRODUCT_NOT_FOUND",
            verified=False,
            error=f"sku {sku!r} not found in WC",
        )
    return product_id, None


async def _check_idempotency(
    client: WCClient, entry: UploadEntry, product_id: int
) -> UploadResult | None:
    """Return ALREADY_SYNCED result if WC already has our image; None otherwise.
    Also returns FAILED on image-fetch exception (caller propagates)."""
    try:
        images = await client.get_product_images(product_id)
    except Exception as exc:
        return _failed(entry.sku, product_id=product_id, error=f"image fetch failed: {exc}")
    if images and _image_basename_matches(images[0].get("src") or "", entry.source_path.name):
        return UploadResult(
            sku=entry.sku,
            product_id=product_id,
            media_id=images[0].get("id"),
            source_url=images[0].get("src"),
            status="ALREADY_SYNCED",
            verified=True,
            error=None,
        )
    return None


async def _post_media_and_extract(
    client: WCClient, entry: UploadEntry, product_id: int
) -> tuple[int | None, str | None, UploadResult | None]:
    """POST file to WC media library; return (media_id, source_url, None) on
    success, (None, None, FAILED) on upload exception or malformed response."""
    try:
        media = await client.upload_media(
            entry.source_path, alt_text=f"{entry.sku} ghost mannequin"
        )
    except Exception as exc:
        return (
            None,
            None,
            _failed(entry.sku, product_id=product_id, error=f"media upload failed: {exc}"),
        )
    media_id = media.get("id")
    source_url = media.get("source_url") or media.get("src")
    if not isinstance(media_id, int) or not source_url:
        return (
            None,
            None,
            _failed(
                entry.sku,
                product_id=product_id,
                error=f"media response missing id/source_url: {media!r}",
            ),
        )
    return media_id, source_url, None


async def _upload_one(client: WCClient, entry: UploadEntry) -> UploadResult:
    sku = entry.sku
    product_id, fail = await _resolve_product_id(client, sku)
    if fail is not None:
        return fail
    assert product_id is not None  # narrowing for mypy

    if synced := await _check_idempotency(client, entry, product_id):
        return synced

    if failure := _validate_source(entry, product_id):
        return failure

    media_id, source_url, post_fail = await _post_media_and_extract(client, entry, product_id)
    if post_fail is not None:
        return post_fail
    assert media_id is not None and source_url is not None

    try:
        await client.set_product_image(product_id, media_id, source_url)
    except Exception as exc:
        return _failed(
            sku,
            product_id=product_id,
            media_id=media_id,
            source_url=source_url,
            error=f"product update failed: {exc}",
        )

    return await _verify_after_upload(client, sku, product_id, media_id, source_url)


async def _verify_after_upload(
    client: WCClient,
    sku: str,
    product_id: int,
    media_id: int,
    source_url: str,
) -> UploadResult:
    """Post-write verification: GET product, confirm images[0].src matches.

    Returns UPLOADED on match, VERIFICATION_FAILED otherwise. Extracted from
    _upload_one to keep that function under the 50-line guideline.
    """
    try:
        post_images = await client.get_product_images(product_id)
    except Exception as exc:
        return UploadResult(
            sku=sku,
            product_id=product_id,
            media_id=media_id,
            source_url=source_url,
            status="VERIFICATION_FAILED",
            verified=False,
            error=f"verification GET failed: {exc}",
        )
    actual = post_images[0].get("src") if post_images else None
    if actual != source_url:
        return UploadResult(
            sku=sku,
            product_id=product_id,
            media_id=media_id,
            source_url=source_url,
            status="VERIFICATION_FAILED",
            verified=False,
            error=f"images[0].src mismatch: got {actual!r}",
        )
    return UploadResult(
        sku=sku,
        product_id=product_id,
        media_id=media_id,
        source_url=source_url,
        status="UPLOADED",
        verified=True,
        error=None,
    )


def _failed(
    sku: str,
    *,
    product_id: int | None = None,
    media_id: int | None = None,
    source_url: str | None = None,
    error: str,
) -> UploadResult:
    return UploadResult(
        sku=sku,
        product_id=product_id,
        media_id=media_id,
        source_url=source_url,
        status="FAILED",
        verified=False,
        error=error,
    )


# ─────────────────────────── rendering ───────────────────────────────────────


def format_manifest_table(rows: list[PreviewRow]) -> str:
    """Format the STOP AND SHOW preview as a fixed-width text table."""
    if not rows:
        return "(empty manifest)"
    header = f"  {'SKU':<10} {'PRODUCT_ID':<12} {'STATUS':<18} {'CURRENT_IMAGE'}"
    lines = [header, "  " + "-" * (len(header) - 2)]
    for r in rows:
        pid = str(r.product_id) if r.product_id is not None else "—"
        current = r.current_image_url or "(none)"
        if len(current) > 60:
            current = current[:57] + "..."
        lines.append(f"  {r.sku:<10} {pid:<12} {r.status:<18} {current}")
    return "\n".join(lines)


def format_results_table(results: list[UploadResult]) -> str:
    if not results:
        return "(no results)"
    header = f"  {'SKU':<10} {'PRODUCT_ID':<12} {'STATUS':<22} {'VERIFIED':<9} ERROR"
    lines = [header, "  " + "-" * (len(header) - 2)]
    for r in results:
        pid = str(r.product_id) if r.product_id is not None else "—"
        ver = "yes" if r.verified else "no"
        err = (r.error or "")[:60]
        lines.append(f"  {r.sku:<10} {pid:<12} {r.status:<22} {ver:<9} {err}")
    return "\n".join(lines)


def append_upload_log(results: list[UploadResult], *, root: Path | str | None = None) -> Path:
    """Best-effort append to upload_log.json. Returns the log path."""
    base = _resolve_root(root)
    log_path = base / GHOST_REL / UPLOAD_LOG_JSON
    log_path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if log_path.exists():
        try:
            with log_path.open(encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
        except (OSError, json.JSONDecodeError):
            existing = []
    existing.extend(asdict(r) for r in results)
    try:
        tmp = log_path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, default=str)
            f.write("\n")
        os.replace(tmp, log_path)
    except OSError as exc:
        _log.warning("upload log write failed: %s", exc)
    return log_path


# ─────────────────────────── production WC adapter ───────────────────────────


class WooCommerceUploader:  # pragma: no cover
    """Production adapter — wraps wordpress.products.WooCommerceProducts + adds
    /wp/v2/media POST that the WC client doesn't expose.

    Constructed lazily so tests that don't need the live client don't trigger
    the env-var lookup.

    Excluded from coverage because the entire class is aiohttp + WC REST
    integration that can only be properly tested against a live WC instance.
    Business logic is fully covered via the WCClient Protocol + FakeWCClient
    in tests/test_upload.py.
    """

    def __init__(self, config: Any | None = None) -> None:
        from wordpress.products import WooCommerceConfig, WooCommerceProducts

        self._config_cls = WooCommerceConfig
        self._products_cls = WooCommerceProducts
        self._config = config or WooCommerceConfig.from_env()
        self._products: Any = None
        self._aiohttp: Any = None

    async def __aenter__(self) -> WooCommerceUploader:
        import aiohttp

        # CRITICAL: validate BEFORE any network call. find_product_id_by_sku,
        # smoke_test, and get_product_images all send Basic Auth to whatever
        # host site_url resolves to. Validating only inside upload_media would
        # let credentials leak to a misconfigured host on the earlier calls.
        _validate_site_url(self._config.site_url)
        self._products = self._products_cls(self._config)
        await self._products.connect()
        self._aiohttp = aiohttp
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._products is not None:
            await self._products.close()

    async def smoke_test(self) -> None:
        """Lightweight reachability + auth probe — raises on failure."""
        await self._products.list(per_page=1)

    async def find_product_id_by_sku(self, sku: str) -> int | None:
        results = await self._products.list(per_page=1, sku=sku)
        if not isinstance(results, list) or not results:
            return None
        first = results[0]
        pid = first.get("id")
        return int(pid) if isinstance(pid, int) else None

    async def get_product_images(self, product_id: int) -> list[dict[str, Any]]:
        product = await self._products.get(product_id)
        images = product.get("images")
        return images if isinstance(images, list) else []

    async def upload_media(self, file_path: Path, alt_text: str = "") -> dict[str, Any]:
        """POST file to /wp/v2/media (different namespace than WC).

        Reuses the WC auth (consumer_key/secret as Basic) — works on WordPress.com
        for sites where the WC application user has upload_files capability.
        """
        _validate_site_url(self._config.site_url)
        if not _FILENAME_SAFE_RE.fullmatch(file_path.name):
            raise UploadError(
                f"unsafe upload filename rejected: {file_path.name!r} "
                f"(must match {_FILENAME_SAFE_RE.pattern})"
            )
        wp_base = f"{self._config.site_url}/wp-json/wp/v2/media"
        mime, _ = mimetypes.guess_type(str(file_path))
        mime = mime or "application/octet-stream"
        headers = {
            "Content-Disposition": f'attachment; filename="{file_path.name}"',
            "Content-Type": mime,
        }
        auth = self._aiohttp.BasicAuth(self._config.consumer_key, self._config.consumer_secret)
        # Bounded timeouts so a stalled WC connection cannot wedge the whole
        # batch. total covers handshake + body upload; sock_read covers chunked
        # response streaming.
        timeout = self._aiohttp.ClientTimeout(total=60, connect=10, sock_read=30)
        with file_path.open("rb") as fh:
            data = fh.read()
        async with self._aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
            async with session.post(wp_base, data=data, headers=headers) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    raise UploadError(f"media POST {resp.status}: {_scrub_credentials(text)[:200]}")
                payload = await resp.json()
        if alt_text and isinstance(payload.get("id"), int):
            # Best-effort alt-text patch — non-fatal on failure.
            try:
                async with self._aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                    async with session.post(
                        f"{wp_base}/{payload['id']}",
                        json={"alt_text": alt_text},
                    ) as resp:
                        await resp.read()
            except Exception:
                _log.debug("alt-text patch failed for media %s", payload["id"], exc_info=True)
        return payload

    async def set_product_image(
        self, product_id: int, media_id: int, source_url: str
    ) -> dict[str, Any]:
        from wordpress.products import ProductUpdate

        update = ProductUpdate(images=[{"id": media_id, "src": source_url, "position": 0}])
        return await self._products.update(product_id, update)
