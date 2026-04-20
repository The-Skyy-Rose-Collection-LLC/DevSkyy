#!/usr/bin/env python3
"""Index the canonical SkyyRose catalog into the semantic vector store.

This script is the commit path for the "live-and-breathe-the-collection"
feature. It reads the canonical CSV, embeds each SKU's content via
Sentence Transformers (local, zero API cost), and upserts into ChromaDB
by default. Default mode is --dry-run so no index mutation happens unless
you explicitly pass --commit.

Usage:
    # Preview what would be indexed (safe, no writes):
    python scripts/index_skyyrose_catalog.py

    # Actually write to the vector store:
    python scripts/index_skyyrose_catalog.py --commit

    # Index into a named collection:
    python scripts/index_skyyrose_catalog.py --commit --collection skyyrose-v2

Output:
    logs/catalog-index-<ts>.json — manifest with total_skus, indexed_ids,
    sample_ids. Always written (including dry-run) so the run leaves a trail.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.catalog_retriever import CatalogRetriever  # noqa: E402

logger = logging.getLogger("index_skyyrose_catalog")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index the SkyyRose canonical catalog into the semantic vector store.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write to the vector store. Default is dry-run.",
    )
    parser.add_argument(
        "--collection",
        default=CatalogRetriever.DEFAULT_COLLECTION,
        help=f"Vector store collection name (default: {CatalogRetriever.DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
    )
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> int:
    retriever = CatalogRetriever(collection_name=args.collection)
    await retriever.initialize()
    try:
        manifest = await retriever.index_catalog(dry_run=not args.commit)
    finally:
        await retriever.close()

    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    manifest_path = logs_dir / f"catalog-index-{ts}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    logger.info("Wrote manifest: %s", manifest_path)
    logger.info(
        "Total SKUs: %d | dry_run=%s | indexed=%d",
        manifest["total_skus"],
        manifest["dry_run"],
        len(manifest["indexed_ids"]),
    )
    return 0 if manifest["total_skus"] > 0 else 1


def main() -> int:
    args = _parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    if not args.commit:
        logger.warning("DRY-RUN mode. Pass --commit to actually write to the vector store.")
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
