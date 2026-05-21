"""CLI entry point for the clothing 3D pipeline.

Usage:
    python -m pipelines.clothing_3d.cli generate \\
        --image path/to/hoodie.jpg \\
        --product "Black Rose Hoodie" \\
        --collection black_rose \\
        --garment-type hoodie \\
        --quality production

    python -m pipelines.clothing_3d.cli generate \\
        --prompt "luxury silver chrome bomber jacket" \\
        --collection black_rose \\
        --quality standard

    python -m pipelines.clothing_3d.cli batch ./catalog.jsonl

    python -m pipelines.clothing_3d.cli health
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from pipelines.clothing_3d.models import (
    PipelineRequest,
    PipelineStatus,
)
from pipelines.clothing_3d.pipeline import ClothingPipeline, run_clothing_pipeline
from services.three_d.trellis.config import (
    TrellisBackend,
    TrellisConfig,
    TrellisQualityPreset,
)
from services.three_d.trellis.provider import TrellisProvider, make_stub_provider

logger = logging.getLogger("clothing_3d.cli")


# =============================================================================
# Parser
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clothing_3d",
        description="End-to-end TRELLIS-backed clothing 3D pipeline.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")

    sub = parser.add_subparsers(dest="command", required=True)

    # generate -------------------------------------------------------------
    gen = sub.add_parser("generate", help="Generate a single 3D model")
    src = gen.add_mutually_exclusive_group(required=True)
    src.add_argument("--image", help="Local image path", default=None)
    src.add_argument("--image-url", help="Public image URL", default=None)
    src.add_argument("--prompt", help="Text prompt", default=None)
    gen.add_argument("--product", help="Product name", default=None)
    gen.add_argument("--sku", help="Product SKU", default=None)
    gen.add_argument("--collection", default=None)
    gen.add_argument("--garment-type", default=None)
    gen.add_argument(
        "--quality",
        choices=[q.value for q in TrellisQualityPreset],
        default=TrellisQualityPreset.STANDARD.value,
    )
    gen.add_argument(
        "--backend",
        choices=[b.value for b in TrellisBackend],
        default=None,
        help="Force a TRELLIS backend",
    )
    gen.add_argument("--dry-run", action="store_true", help="Use the stub backend")
    gen.add_argument("--skip-qc", action="store_true")
    gen.add_argument("--out", help="Where to write the JSON result", default=None)

    # batch ----------------------------------------------------------------
    batch = sub.add_parser("batch", help="Process a JSONL of requests")
    batch.add_argument("jsonl", help="Path to JSONL with one PipelineRequest per line")
    batch.add_argument(
        "--quality",
        choices=[q.value for q in TrellisQualityPreset],
        default=TrellisQualityPreset.STANDARD.value,
    )
    batch.add_argument("--max-concurrent", type=int, default=2)
    batch.add_argument("--out", help="Where to write results JSONL", default="-")
    batch.add_argument("--dry-run", action="store_true")

    # health ---------------------------------------------------------------
    sub.add_parser("health", help="Run provider health check")

    return parser


# =============================================================================
# Commands
# =============================================================================


async def cmd_generate(args: argparse.Namespace) -> int:
    config = _build_config(args)
    provider = _build_provider(config, dry_run=args.dry_run)
    pipeline = ClothingPipeline(config=config, provider=provider)

    try:
        request = PipelineRequest(
            image_path=args.image,
            image_url=args.image_url,
            prompt=args.prompt,
            product_name=args.product,
            product_sku=args.sku,
            collection=args.collection,
            garment_type=args.garment_type,
            quality=TrellisQualityPreset(args.quality),
            skip_qc=args.skip_qc,
        )
        result = await pipeline.run(request)
    finally:
        await pipeline.close()

    payload = result.model_dump(mode="json")
    _emit_result(payload, args.out)
    return 0 if result.status == PipelineStatus.SUCCEEDED else 1


async def cmd_batch(args: argparse.Namespace) -> int:
    config = _build_config(args)
    provider = _build_provider(config, dry_run=args.dry_run)
    pipeline = ClothingPipeline(config=config, provider=provider)

    sem = asyncio.Semaphore(max(1, args.max_concurrent))
    requests = _load_jsonl(args.jsonl, default_quality=args.quality)
    results: list[dict[str, Any]] = []

    async def _one(req: PipelineRequest) -> None:
        async with sem:
            res = await pipeline.run(req)
            results.append(res.model_dump(mode="json"))

    try:
        await asyncio.gather(*(_one(r) for r in requests))
    finally:
        await pipeline.close()

    if args.out == "-":
        for r in results:
            print(json.dumps(r, default=str))
    else:
        Path(args.out).write_text(
            "\n".join(json.dumps(r, default=str) for r in results) + "\n",
            encoding="utf-8",
        )

    failed = sum(1 for r in results if r["status"] != "succeeded")
    logger.info("batch complete: %d ok, %d failed", len(results) - failed, failed)
    return 0 if failed == 0 else 1


async def cmd_health(_args: argparse.Namespace) -> int:
    config = TrellisConfig.from_env()
    provider = TrellisProvider(config)
    try:
        health = await provider.health_check()
    finally:
        await provider.close()

    print(json.dumps(health.model_dump(mode="json"), indent=2, default=str))
    return 0 if health.is_available else 1


# =============================================================================
# Helpers
# =============================================================================


def _build_config(args: argparse.Namespace) -> TrellisConfig:
    config = TrellisConfig.from_env()
    config.quality = TrellisQualityPreset(getattr(args, "quality", config.quality.value))
    backend = getattr(args, "backend", None)
    if backend:
        config.backend = TrellisBackend(backend)
    config.ensure_dirs()
    return config


def _build_provider(config: TrellisConfig, *, dry_run: bool) -> TrellisProvider:
    if dry_run or os.getenv("TRELLIS_DRY_RUN") == "1":
        logger.info("dry-run: using stub backend")
        return make_stub_provider(config)
    return TrellisProvider(config)


def _load_jsonl(path: str, *, default_quality: str) -> list[PipelineRequest]:
    requests: list[PipelineRequest] = []
    text = Path(path).read_text(encoding="utf-8")
    for line_no, raw in enumerate(text.splitlines(), start=1):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no} invalid JSON — {exc}") from exc
        payload.setdefault("quality", default_quality)
        requests.append(PipelineRequest.model_validate(payload))
    return requests


def _emit_result(payload: dict[str, Any], out: str | None) -> None:
    text = json.dumps(payload, indent=2, default=str)
    if not out or out == "-":
        print(text)
    else:
        Path(out).write_text(text + "\n", encoding="utf-8")


# =============================================================================
# Entry
# =============================================================================


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    coro_map = {
        "generate": cmd_generate,
        "batch": cmd_batch,
        "health": cmd_health,
    }
    coro = coro_map[args.command]
    return asyncio.run(coro(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
