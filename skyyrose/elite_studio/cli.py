"""
CLI entry point for the Elite Studio.

Usage:
    python -m skyyrose.elite_studio produce br-001
    python -m skyyrose.elite_studio produce-batch --all
    python -m skyyrose.elite_studio produce-batch --remaining
    python -m skyyrose.elite_studio status
"""

from __future__ import annotations

import argparse
import sys

from .agents.generator_agent import GeneratorAgent
from .agents.quality_agent import QualityAgent
from .agents.vision_agent import VisionAgent
from .config import OUTPUT_DIR
from .coordinator import Coordinator
from .utils import discover_all_skus


def build_team() -> Coordinator:
    """Build the default agent team."""
    return Coordinator(
        vision=VisionAgent(),
        generator=GeneratorAgent(),
        quality=QualityAgent(),
    )


def cmd_produce(args: argparse.Namespace) -> None:
    """Produce a single product."""
    team = build_team()
    result = team.produce(args.sku, args.view)
    print(f"\nResult: {result.status}")
    if result.output_path:
        print(f"Output: {result.output_path}")
    if result.error:
        print(f"Error: {result.error}")


def cmd_batch(args: argparse.Namespace) -> None:
    """Produce batch of products."""
    team = build_team()

    skus = None
    if not args.all and args.sku:
        # Filter by prefix
        all_skus = discover_all_skus()
        skus = [s for s in all_skus if s.startswith(args.sku)]
    elif not args.all:
        skus = discover_all_skus()

    team.produce_batch(
        skus=skus,
        view=args.view,
        skip_existing=args.remaining,
    )


def cmd_status(args: argparse.Namespace) -> None:
    """Show status of generated images."""
    all_skus = discover_all_skus()
    generated = []
    missing = []

    for sku in all_skus:
        output = OUTPUT_DIR / sku / f"{sku}-model-front-gemini.jpg"
        if output.exists():
            generated.append(sku)
        else:
            missing.append(sku)

    print(f"\nElite Studio Status")
    print(f"{'='*40}")
    print(f"Total products: {len(all_skus)}")
    print(f"Generated:      {len(generated)}")
    print(f"Remaining:      {len(missing)}")
    print()

    if generated:
        print("Generated:")
        for sku in generated:
            print(f"  {sku}")

    if missing:
        print("\nRemaining:")
        for sku in missing:
            print(f"  {sku}")


def main(argv: list[str] | None = None) -> None:
    """CLI main entry point."""
    parser = argparse.ArgumentParser(
        description="SkyyRose Elite Production Studio — Multi-Agent Pipeline"
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # produce
    p_produce = sub.add_parser("produce", help="Produce single product")
    p_produce.add_argument("sku", help="Product SKU (e.g., br-001)")
    p_produce.add_argument(
        "--view", default="front", choices=["front", "back"], help="View angle"
    )

    # produce-batch
    p_batch = sub.add_parser("produce-batch", help="Produce batch of products")
    p_batch.add_argument("sku", nargs="?", help="SKU prefix filter (optional)")
    p_batch.add_argument(
        "--all", action="store_true", help="Process all products"
    )
    p_batch.add_argument(
        "--remaining",
        action="store_true",
        default=True,
        help="Skip already-generated products (default: True)",
    )
    p_batch.add_argument(
        "--view", default="front", choices=["front", "back"], help="View angle"
    )

    # status
    sub.add_parser("status", help="Show generation status")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "produce":
        cmd_produce(args)
    elif args.command == "produce-batch":
        cmd_batch(args)
    elif args.command == "status":
        cmd_status(args)
