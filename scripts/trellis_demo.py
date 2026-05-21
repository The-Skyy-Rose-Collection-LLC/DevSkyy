#!/usr/bin/env python
"""End-to-end demo for the clothing 3D pipeline.

Runs against the stub backend by default so you can validate orchestration
without burning a GPU or hitting the HF Space. Pass ``--backend hf_space``
once you've confirmed your gradio_client install is healthy.

Examples:
    # Stub run
    python scripts/trellis_demo.py

    # HuggingFace Space (no GPU required, slow cold-start)
    python scripts/trellis_demo.py --backend hf_space --image path/to/hoodie.jpg

    # Local GPU (requires scripts/setup_trellis.sh + weights)
    python scripts/trellis_demo.py --backend local --image path/to/hoodie.jpg --quality production
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import tempfile
from pathlib import Path

# Allow ``python scripts/trellis_demo.py`` from the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipelines.clothing_3d.models import PipelineRequest  # noqa: E402
from pipelines.clothing_3d.pipeline import ClothingPipeline  # noqa: E402
from services.three_d.trellis.config import (  # noqa: E402
    TrellisBackend,
    TrellisConfig,
    TrellisQualityPreset,
)
from services.three_d.trellis.provider import TrellisProvider, make_stub_provider  # noqa: E402

logger = logging.getLogger("trellis_demo")


def _make_synthetic_image() -> str:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (800, 1000), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([200, 200, 600, 850], fill=(20, 20, 28))
    draw.rectangle([350, 220, 450, 280], fill=(245, 245, 245))  # hood opening
    tmp = Path(tempfile.mkdtemp(prefix="trellis_demo_")) / "synthetic_hoodie.png"
    img.save(tmp)
    return str(tmp)


async def run_demo(args: argparse.Namespace) -> int:
    config = TrellisConfig.from_env()
    is_stub = args.backend == "stub" or args.dry_run
    if not is_stub:
        config.backend = TrellisBackend(args.backend)
    config.quality = TrellisQualityPreset(args.quality)
    config.ensure_dirs()

    if is_stub:
        provider = make_stub_provider(config)
    else:
        provider = TrellisProvider(config)

    pipeline = ClothingPipeline(config=config, provider=provider)

    try:
        image_path = args.image or _make_synthetic_image()
        logger.info("input image: %s", image_path)

        request = PipelineRequest(
            image_path=image_path,
            product_name=args.product,
            collection=args.collection,
            garment_type=args.garment_type,
            quality=TrellisQualityPreset(args.quality),
        )
        result = await pipeline.run(request)
    finally:
        await pipeline.close()

    print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))
    return 0 if result.succeeded else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=[*[b.value for b in TrellisBackend], "stub"],
        default="stub",
    )
    parser.add_argument(
        "--quality",
        choices=[q.value for q in TrellisQualityPreset],
        default=TrellisQualityPreset.DRAFT.value,
    )
    parser.add_argument("--image", default=None, help="Override the synthetic input")
    parser.add_argument("--product", default="Demo Black Rose Hoodie")
    parser.add_argument("--collection", default="black_rose")
    parser.add_argument("--garment-type", default="hoodie")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    return asyncio.run(run_demo(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
