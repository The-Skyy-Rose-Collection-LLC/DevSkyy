# services/storage/ — Asset Storage & Versioning

**Cloudflare R2 (S3-compatible, zero egress) + asset versioning with retention policies (US-023).** Canonical asset store for all generated imagery + 3D assets.

## Public Surface (`services/storage/__init__.py`)

| Group | Symbols | Source |
|-------|---------|--------|
| R2 client | `R2Client`, `R2Config`, `R2Error`, `R2NotFoundError`, `R2Object`, `R2UploadResult`, `AssetCategory` | `r2_client.py` |
| Versioning schemas | `AssetInfo`, `CleanupResult`, `CreateVersionRequest`, `RetentionPolicy`, `RevertVersionRequest`, `UpdateRetentionRequest`, `VersionInfo`, `VersionListResponse`, `VersionStatus` | `schemas.py` |
| Version manager | `AssetVersionManager`, `AssetNotFoundError`, `VersioningError`, `VersionNotFoundError` | `version_manager.py` |

## Hard Rules

- **R2 only** for generated assets (zero egress fees beat S3 at our scale). Do not bypass R2 by writing directly to local disk in production
- `AssetCategory` enum gates the bucket prefix — never store a "product" asset under "internal" prefix or version manager loses it
- Cloudflare R2 is S3-compatible — credentials via `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ACCOUNT_ID` env vars
- **Versioning is mandatory** for catalog imagery — every write through `AssetVersionManager.create_version()`, never raw `R2Client.put()` for product assets
- `RetentionPolicy` drives cleanup — versions older than policy + not marked `PROTECTED` are eligible for deletion. Run cleanup as background job
- `revert_version()` is a **soft revert** — older version becomes current, original is preserved unless retention policy expires
- All R2 operations are async — never wrap in `asyncio.run()` from inside an event loop

## Consumers

- `services/ml/pipeline_orchestrator.py` — writes pipeline outputs via version manager
- `api/v1/clothing_3d/*` — async 3D job results stored here
- `skyyrose/elite_studio/*` — canonical imagery destination
- `api/v1/assets` — admin asset management surface
