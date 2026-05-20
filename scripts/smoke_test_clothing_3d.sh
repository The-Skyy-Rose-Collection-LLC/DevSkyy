#!/usr/bin/env bash
# Smoke test for the clothing 3D pipeline.
#
# Exercises the full stack against the stub TRELLIS backend so it runs in
# under 5 seconds and needs no GPU, network, or paid API credits. Designed
# to drop into CI:
#
#   bash scripts/smoke_test_clothing_3d.sh
#
# Exit codes:
#   0  — all checks passed
#   1  — at least one check failed (specific failure printed)
#   2  — environment missing (python, etc.)
#
# Override the worker concurrency for the worker-roundtrip step:
#   SMOKE_CONCURRENCY=2 bash scripts/smoke_test_clothing_3d.sh
#
# Use a stub backend; force in-memory queue/store so we don't touch Redis.
set -euo pipefail

# Prefer Python ≥3.12 (project requirement) — the codebase uses 3.12 type-param syntax.
if [ -n "${PYTHON:-}" ]; then
  PY="$PYTHON"
elif command -v python3.12 >/dev/null 2>&1; then
  PY="$(command -v python3.12)"
elif command -v python3.13 >/dev/null 2>&1; then
  PY="$(command -v python3.13)"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
else
  echo "✗ no python interpreter on PATH" >&2
  exit 2
fi

# Sanity-check: the project requires Python ≥3.12.
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
  ver="$("$PY" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  echo "✗ Python $ver is too old — DevSkyy requires Python ≥3.12 (set PYTHON=/path/to/python3.12)" >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Fresh tmpdir; cleaned on exit.
TMPDIR="$(mktemp -d -t clothing3d-smoke-XXXXXX)"
trap 'rm -rf "$TMPDIR"' EXIT

export THREE_D_OUTPUT_DIR="$TMPDIR/out"
export TRELLIS_CACHE_DIR="$TMPDIR/cache"
export TRELLIS_BACKEND="hf_space"   # the worker won't actually call it; we use dry-run
export CLOTHING_3D_QUEUE="memory"
export CLOTHING_3D_JOB_STORE="memory"
export TRELLIS_DRY_RUN="1"

mkdir -p "$THREE_D_OUTPUT_DIR" "$TRELLIS_CACHE_DIR"

pass() { printf "✓ %s\n" "$1"; }
fail() { printf "✗ %s\n   %s\n" "$1" "${2:-}"; exit 1; }

# ─── 1. Imports ──────────────────────────────────────────────────────────
"$PY" - <<'PY' || fail "imports" "see traceback above"
from pipelines.clothing_3d import (
    ClothingPipeline, CostQuota, IdempotencyCache,
    InMemoryJobStore, InMemoryQueue, JobRecord,
    PipelineRequest, PipelineWorker, PipelineStatus,
    RetryPolicy, request_fingerprint, configure_logging, get_metrics,
)
PY
pass "imports"

# ─── 2. Garment classifier + prompt builder ─────────────────────────────
"$PY" - <<'PY' || fail "garment_aware" "classifier broken"
from services.three_d.trellis.garment_aware import classify_garment, build_clothing_prompt, GarmentCategory
assert classify_garment(declared_category="hoodie") is GarmentCategory.HOODIE
assert classify_garment(product_name="Long Dress") is GarmentCategory.DRESS
p = build_clothing_prompt(product_name="X", category=GarmentCategory.HOODIE, collection="black_rose")
assert "hood" in p.lower() and "chrome" in p.lower()
PY
pass "garment_aware"

# ─── 3. Pipeline end-to-end with stub backend ───────────────────────────
"$PY" - <<'PY' || fail "pipeline end-to-end" "stub run failed"
import asyncio, sys, tempfile, pathlib
from PIL import Image
from pipelines.clothing_3d import ClothingPipeline, PipelineRequest, PipelineStatus
from pipelines.clothing_3d.stages import QCThresholds
from services.three_d.trellis.config import TrellisConfig, TrellisQualityPreset
from services.three_d.trellis.provider import TrellisProvider
from services.three_d.trellis.client import StubClient

async def main():
    cfg = TrellisConfig(
        cache_dir=__import__("os").environ["TRELLIS_CACHE_DIR"],
        output_dir=__import__("os").environ["THREE_D_OUTPUT_DIR"],
        enable_background_removal=False,
        enable_postprocess=False,
        export_usdz_for_ios=False,
        quality=TrellisQualityPreset.DRAFT,
        retry_attempts=0,
    )
    cfg.ensure_dirs()
    img = pathlib.Path(cfg.cache_dir) / "smoke.png"
    Image.new("RGB", (600, 800), (220, 220, 220)).save(img)
    pipe = ClothingPipeline(
        config=cfg,
        provider=TrellisProvider(cfg, backend=StubClient(cfg)),
        thresholds=QCThresholds(min_polycount=0, max_polycount=10**9, min_file_kb=0, max_file_kb=10**9),
    )
    res = await pipe.run(PipelineRequest(image_path=str(img), product_name="Smoke", garment_type="tee", skip_qc=True))
    assert res.status is PipelineStatus.SUCCEEDED, f"expected SUCCEEDED, got {res.status}: {res.metadata}"
    assert res.glb_url and res.glb_url.startswith("/assets/3d-models-generated/")
    await pipe.close()

asyncio.run(main())
PY
pass "pipeline end-to-end"

# ─── 4. Idempotency cache hit ────────────────────────────────────────────
"$PY" - <<'PY' || fail "idempotency" "cache hit not detected"
import asyncio, os, pathlib, tempfile
from PIL import Image
from pipelines.clothing_3d import (
    ClothingPipeline, IdempotencyCache, PipelineRequest,
)
from pipelines.clothing_3d.stages import QCThresholds
from services.three_d.trellis.config import TrellisConfig, TrellisQualityPreset
from services.three_d.trellis.provider import TrellisProvider
from services.three_d.trellis.client import StubClient

async def main():
    cfg = TrellisConfig(
        cache_dir=os.environ["TRELLIS_CACHE_DIR"],
        output_dir=os.environ["THREE_D_OUTPUT_DIR"],
        enable_background_removal=False, enable_postprocess=False,
        export_usdz_for_ios=False, quality=TrellisQualityPreset.DRAFT,
    )
    cfg.ensure_dirs()
    img = pathlib.Path(cfg.cache_dir) / "smoke_idem.png"
    Image.new("RGB", (400, 500), (200, 200, 200)).save(img)
    pipe = ClothingPipeline(config=cfg, provider=TrellisProvider(cfg, backend=StubClient(cfg)),
                            thresholds=QCThresholds(min_polycount=0, max_polycount=10**9, min_file_kb=0, max_file_kb=10**9))
    cache = IdempotencyCache(ttl_seconds=60)
    req = PipelineRequest(image_path=str(img), product_name="Idem", garment_type="tee", skip_qc=True)
    r1, hit1 = await cache.get_or_run(req, runner=pipe.run)
    r2, hit2 = await cache.get_or_run(req, runner=pipe.run)
    assert not hit1, "first call should be a miss"
    assert hit2, "second call should be a hit"
    assert r1.glb_url == r2.glb_url
    await pipe.close()

asyncio.run(main())
PY
pass "idempotency cache"

# ─── 5. Cost quota ───────────────────────────────────────────────────────
"$PY" - <<'PY' || fail "cost quota" "QuotaExceededError not raised"
from pipelines.clothing_3d.reliability import CostQuota, QuotaExceededError
q = CostQuota(caps_usd={"replicate": 0.10})
q.charge("replicate"); q.charge("replicate")  # 2 calls @ $0.05 = $0.10
try:
    q.charge("replicate")  # would push over
except QuotaExceededError:
    pass
else:
    raise AssertionError("expected QuotaExceededError")
PY
pass "cost quota"

# ─── 6. Retry policy backoff ─────────────────────────────────────────────
"$PY" - <<'PY' || fail "retry policy" "did not retry correctly"
import asyncio
from pipelines.clothing_3d.reliability import RetryPolicy

calls = []
async def flaky():
    calls.append(1)
    if len(calls) < 3:
        raise TimeoutError("flake")
    return "ok"

policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.001, max_delay_seconds=0.01)
result = asyncio.run(policy.run(flaky))
assert result == "ok"
assert len(calls) == 3
PY
pass "retry policy"

# ─── 7. Queue + Worker round-trip ────────────────────────────────────────
"$PY" - <<'PY' || fail "worker round-trip" "worker did not finish job"
import asyncio, os, pathlib
from PIL import Image
from pipelines.clothing_3d import (
    ClothingPipeline, InMemoryJobStore, InMemoryQueue,
    JobRecord, PipelineRequest, PipelineStatus, PipelineWorker,
)
from pipelines.clothing_3d.stages import QCThresholds
from services.three_d.trellis.config import TrellisConfig, TrellisQualityPreset
from services.three_d.trellis.provider import TrellisProvider
from services.three_d.trellis.client import StubClient

async def main():
    cfg = TrellisConfig(
        cache_dir=os.environ["TRELLIS_CACHE_DIR"],
        output_dir=os.environ["THREE_D_OUTPUT_DIR"],
        enable_background_removal=False, enable_postprocess=False,
        export_usdz_for_ios=False, quality=TrellisQualityPreset.DRAFT,
        retry_attempts=0,
    )
    cfg.ensure_dirs()
    img = pathlib.Path(cfg.cache_dir) / "worker_smoke.png"
    Image.new("RGB", (500, 700), (210, 210, 210)).save(img)

    pipe = ClothingPipeline(
        config=cfg,
        provider=TrellisProvider(cfg, backend=StubClient(cfg)),
        thresholds=QCThresholds(min_polycount=0, max_polycount=10**9, min_file_kb=0, max_file_kb=10**9),
    )
    queue, store = InMemoryQueue(), InMemoryJobStore()
    worker = PipelineWorker(
        pipeline=pipe, queue=queue, store=store,
        concurrency=1, poll_block_seconds=0.5, reclaim_interval_seconds=5,
    )

    record = JobRecord(
        job_id="smoke-1",
        request=PipelineRequest(image_path=str(img), product_name="W", garment_type="tee", skip_qc=True),
    )
    await store.put(record)
    await queue.enqueue("smoke-1")

    task = asyncio.create_task(worker.run())
    for _ in range(80):  # up to 8 seconds
        await asyncio.sleep(0.1)
        latest = await store.get("smoke-1")
        if latest and latest.status in {PipelineStatus.SUCCEEDED, PipelineStatus.REJECTED, PipelineStatus.FAILED}:
            break
    else:
        await worker.shutdown()
        await task
        raise AssertionError(f"worker never finished job; final status = {(latest.status if latest else 'missing')}")

    await worker.shutdown()
    await task
    assert latest.status is PipelineStatus.SUCCEEDED, f"expected SUCCEEDED, got {latest.status} (err={latest.error})"
    assert latest.result is not None
    assert latest.result.glb_url

asyncio.run(main())
PY
pass "worker round-trip"

# ─── 8. One-call generate() entry point ──────────────────────────────────
"$PY" - <<'PY' || fail "generate()" "one-call entry point broken"
import asyncio, os, pathlib
from PIL import Image
from pipelines.clothing_3d import generate, preflight, reset_runtime, PipelineStatus

async def main():
    img = pathlib.Path(os.environ["TRELLIS_CACHE_DIR"]) / "smoke_runtime.png"
    Image.new("RGB", (520, 700), (210, 210, 210)).save(img)

    report = await preflight()
    assert "ready" in report, "preflight should expose ready key"
    assert "config" in report, "preflight should report config"

    r = await generate(
        image_path=str(img), product_name="Smoke Runtime",
        garment_type="tee", quality="draft", skip_qc=True,
    )
    assert r.status is PipelineStatus.SUCCEEDED, f"got {r.status}: {r.metadata}"
    assert r.glb_url

    # Identical input → cache hit (same artifact_id)
    r2 = await generate(
        image_path=str(img), product_name="Smoke Runtime",
        garment_type="tee", quality="draft", skip_qc=True,
    )
    assert r2.artifact_id == r.artifact_id, "expected cache hit on duplicate"

    await reset_runtime()

asyncio.run(main())
PY
pass "generate() one-call"

echo
echo "All clothing_3d smoke checks passed."
