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

from .agents.compositor_agent import CompositorAgent
from .agents.generator_agent import GeneratorAgent
from .agents.quality_agent import QualityAgent
from .agents.vision_agent import VisionAgent
from .config import OUTPUT_DIR, PRODUCT_IMAGES_DIR
from .coordinator import Coordinator
from .utils import discover_all_skus, discover_scene_images


def _run_graph(
    sku: str,
    view: str,
    with_compositor: bool,
    with_tryon: bool = False,
    style: str = "flat_lay",
    with_3d: bool = False,
) -> None:
    """Run the LangGraph engine path and print result."""
    from .graph import GraphConfig, run_single

    config = GraphConfig(
        enable_compositor=with_compositor,
        enable_tryon=with_tryon,
        enable_ghost_mannequin_preflight=(style == "ghost_mannequin"),
        enable_ghost_mannequin_composite=(style == "ghost_mannequin"),
        enable_3d=with_3d,
    )
    result = run_single(sku=sku, view=view, style=style, config=config)
    print(f"\nResult: {result.status}")
    if result.output_path:
        print(f"Output: {result.output_path}")
    if result.compositing and result.compositing.success:
        print(f"Composited: {result.compositing.output_path}")
    if result.tryon and result.tryon.success:
        print(f"Try-on:     {result.tryon.output_path}")
    if result.error:
        print(f"Error: {result.error}")
    if result.quality:
        print(f"QC score: {result.quality.score:.2f}  [{result.quality.recommendation}]")


def build_team(with_compositor: bool = False) -> Coordinator:
    """Build the default agent team."""
    return Coordinator(
        vision=VisionAgent(),
        generator=GeneratorAgent(),
        quality=QualityAgent(),
        compositor=CompositorAgent() if with_compositor else None,
    )


def cmd_produce(args: argparse.Namespace) -> None:
    """Produce a single product."""
    if getattr(args, "graph", False):
        _run_graph(
            args.sku,
            args.view,
            with_compositor=getattr(args, "composite", False),
            with_tryon=getattr(args, "tryon", False),
            style=getattr(args, "style", "flat_lay"),
            with_3d=getattr(args, "three_d", False),
        )
        return
    team = build_team(with_compositor=getattr(args, "composite", False))
    result = team.produce(args.sku, args.view)
    print(f"\nResult: {result.status}")
    if result.output_path:
        print(f"Output: {result.output_path}")
    if result.compositing and result.compositing.success:
        print(f"Composited: {result.compositing.output_path}")
    if result.error:
        print(f"Error: {result.error}")


def _resolve_sku_filter(args: argparse.Namespace) -> list[str] | None:
    """Resolve --sku prefix into an explicit SKU list, or None for 'all'.

    Returns None when --all is set or no --sku prefix is given (callers that need
    an explicit list can fall back to discover_all_skus()). When --sku is set but
    matches zero SKUs, exits with a clear error rather than silently running on
    an empty batch.
    """
    if args.all or not args.sku:
        return None
    skus = [s for s in discover_all_skus() if s.startswith(args.sku)]
    if not skus:
        print(f"Error: no SKUs match prefix {args.sku!r}", file=sys.stderr)
        sys.exit(1)
    return skus


def cmd_batch(args: argparse.Namespace) -> None:
    """Produce batch of products."""
    if getattr(args, "graph", False):
        from .graph import GraphConfig, run_batch

        config = GraphConfig(
            enable_compositor=getattr(args, "composite", False),
            enable_tryon=getattr(args, "tryon", False),
            enable_ghost_mannequin_preflight=(
                getattr(args, "style", "flat_lay") == "ghost_mannequin"
            ),
            enable_ghost_mannequin_composite=(
                getattr(args, "style", "flat_lay") == "ghost_mannequin"
            ),
            enable_3d=getattr(args, "three_d", False),
        )

        skus = _resolve_sku_filter(args) or discover_all_skus()
        run_batch(
            skus=skus,
            view=args.view,
            style=getattr(args, "style", "flat_lay"),
            config=config,
            skip_existing=args.remaining,
        )
        return

    team = build_team()
    team.produce_batch(skus=_resolve_sku_filter(args), view=args.view, skip_existing=args.remaining)


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

    print("\nElite Studio Status")
    print(f"{'=' * 40}")
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


def cmd_composite(args: argparse.Namespace) -> None:
    """Run standalone scene compositing for a SKU."""
    from .agents.compositor_agent import SCENE_LOOKBOOK

    agent = CompositorAgent()
    scene_name = args.scene
    collection = args.collection or scene_name.rsplit("-", 2)[0]

    # Find model image
    model_image = args.model_image
    if not model_image:
        sku_map = SCENE_LOOKBOOK.get(scene_name, {})
        filename = sku_map.get(args.sku, "")
        if filename and filename != "lookbook":
            candidate = PRODUCT_IMAGES_DIR / collection / filename
            if candidate.exists():
                model_image = str(candidate)
        if not model_image:
            # Try glob
            candidates = sorted((PRODUCT_IMAGES_DIR / collection).glob(f"{args.sku}-*.*"))
            if candidates:
                model_image = str(candidates[0])

    if not model_image:
        print(f"Error: No model image found for {args.sku}")
        sys.exit(1)

    # Find scene image
    scene_image = args.scene_image
    if not scene_image:
        scenes = discover_scene_images(collection)
        if scenes:
            scene_image = str(scenes[0])

    if not scene_image:
        print(f"Error: No scene image found for {scene_name}")
        sys.exit(1)

    result = agent.composite(
        sku=args.sku,
        scene_image_path=scene_image,
        model_image_path=model_image,
        collection=collection,
        scene_name=scene_name,
    )

    print(f"\nResult: {'success' if result.success else 'failed'}")
    if result.output_path:
        print(f"Output: {result.output_path}")
    if result.qa_status:
        print(f"QA: {result.qa_status}")
    if result.error:
        print(f"Error: {result.error}")


def cmd_produce_async(args: argparse.Namespace) -> None:
    """Enqueue a SKU render job and return the job_id."""
    from .queue.producer import enqueue_produce

    job_id = enqueue_produce(
        sku=args.sku,
        view=args.view,
        priority=args.priority,
        enable_compositor=getattr(args, "composite", False),
    )
    print(f"Enqueued: {job_id}")


def cmd_create(args: argparse.Namespace) -> None:
    """Run a creative operation via the Creative Operations Hub."""
    import json

    from .creative.runner import run_creative

    params: dict = {}
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as exc:
            print(f"Error: --params must be valid JSON: {exc}")
            sys.exit(1)

    result = run_creative(
        intent=args.intent,
        params=params,
        sku=getattr(args, "sku", "") or "",
    )
    print(f"Operation: {result.get('operation_id', '')}")
    print(f"Status:    {result.get('status', 'unknown')}")
    if result.get("error"):
        print(f"Error:     {result['error']}")
    if result.get("render_result"):
        r = result["render_result"]
        print(f"Render:    {r.get('output_path', '')} [{r.get('status', '')}]")
    if result.get("design_result"):
        d = result["design_result"]
        print(f"Design:    {d.get('concept_name', '')} ({d.get('concept_id', '')})")
    if result.get("copy_result"):
        c = result["copy_result"]
        print(f"Copy:      {c.get('meta_title', '')}")


def cmd_job_status(args: argparse.Namespace) -> None:
    """Print the current status of a queued job."""
    import json
    import os

    import redis as sync_redis

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = sync_redis.from_url(redis_url, decode_responses=True)
        raw = r.get(f"elite_studio:result:{args.job_id}")
        if raw:
            data = json.loads(raw)
            print(f"Status:  {data.get('status', 'unknown')}")
            print(f"SKU:     {data.get('sku', '')}")
            print(f"Output:  {data.get('output_path', '')}")
            if data.get("error"):
                print(f"Error:   {data['error']}")
        else:
            print(f"Job {args.job_id!r} not found (may still be queued or expired).")
    except Exception as exc:
        print(f"Error connecting to Redis: {exc}")
        sys.exit(1)


def cmd_job_result(args: argparse.Namespace) -> None:
    """Print the full JSON result for a completed job."""
    import json
    import os

    import redis as sync_redis

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = sync_redis.from_url(redis_url, decode_responses=True)
        raw = r.get(f"elite_studio:result:{args.job_id}")
        if raw:
            print(json.dumps(json.loads(raw), indent=2))
        else:
            print(f"No result found for job {args.job_id!r}.")
    except Exception as exc:
        print(f"Error connecting to Redis: {exc}")
        sys.exit(1)


def cmd_dlq_list(args: argparse.Namespace) -> None:
    """List all entries in the Dead Letter Queue."""
    from .queue.dead_letter import DeadLetterQueue

    dlq = DeadLetterQueue()
    entries = dlq.list_failed()
    if not entries:
        print("DLQ is empty.")
        return
    print(f"DLQ entries: {len(entries)}")
    for entry in entries:
        print(f"  {entry.get('job_id')}  sku={entry.get('sku')}  failed={entry.get('failed_at')}")
        print(f"    error: {entry.get('error', '')[:100]}")


def cmd_dlq_retry(args: argparse.Namespace) -> None:
    """Retry a specific failed job from the DLQ."""
    from .queue.dead_letter import DeadLetterQueue

    dlq = DeadLetterQueue()
    try:
        new_job_id = dlq.retry(args.job_id)
        print(f"Retried: {args.job_id} -> new job {new_job_id}")
    except KeyError:
        print(f"Job {args.job_id!r} not found in DLQ.")
        sys.exit(1)
    except Exception as exc:
        print(f"Retry failed: {exc}")
        sys.exit(1)


def cmd_worker(args: argparse.Namespace) -> None:
    """Start the Elite Studio queue worker."""
    import logging

    from .queue.consumer import EliteStudioWorker

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    concurrency = getattr(args, "concurrency", 1)
    worker = EliteStudioWorker(concurrency=concurrency)
    worker.run_forever()


def main(argv: list[str] | None = None) -> None:
    """CLI main entry point."""
    parser = argparse.ArgumentParser(
        description="SkyyRose Elite Production Studio — Multi-Agent Pipeline"
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # produce
    p_produce = sub.add_parser("produce", help="Produce single product")
    p_produce.add_argument("sku", help="Product SKU (e.g., br-001)")
    p_produce.add_argument("--view", default="front", choices=["front", "back"], help="View angle")
    p_produce.add_argument(
        "--style",
        default="flat_lay",
        choices=["flat_lay", "ghost_mannequin"],
        help="Photography style (requires --graph)",
    )
    p_produce.add_argument(
        "--3d",
        dest="three_d",
        action="store_true",
        help="Enable 3D replica generation (requires --graph)",
    )

    # produce-batch
    p_batch = sub.add_parser("produce-batch", help="Produce batch of products")
    p_batch.add_argument("sku", nargs="?", help="SKU prefix filter (optional)")
    p_batch.add_argument("--all", action="store_true", help="Process all products")
    p_batch.add_argument(
        "--remaining",
        action="store_true",
        default=False,
        help="Skip already-generated products (default: False)",
    )
    p_batch.add_argument("--view", default="front", choices=["front", "back"], help="View angle")
    p_batch.add_argument(
        "--composite",
        action="store_true",
        help="Run scene compositing after generation",
    )
    p_batch.add_argument(
        "--graph",
        action="store_true",
        help="Use LangGraph engine instead of legacy Coordinator",
    )
    p_batch.add_argument(
        "--style",
        default="flat_lay",
        choices=["flat_lay", "ghost_mannequin"],
        help="Photography style (requires --graph)",
    )
    p_batch.add_argument(
        "--3d",
        dest="three_d",
        action="store_true",
        help="Enable 3D replica generation (requires --graph)",
    )
    p_batch.add_argument(
        "--tryon",
        action="store_true",
        help="Run virtual try-on after generation (requires --graph; uses FASHN_API_KEY)",
    )

    # status
    sub.add_parser("status", help="Show generation status")

    # composite (standalone)
    p_composite = sub.add_parser("composite", help="Composite a SKU into a scene")
    p_composite.add_argument("sku", help="Product SKU (e.g., br-001)")
    p_composite.add_argument(
        "--scene", required=True, help="Scene name (e.g., black-rose-rooftop-garden)"
    )
    p_composite.add_argument("--scene-image", help="Path to scene background image")
    p_composite.add_argument("--model-image", help="Path to model/product image")
    p_composite.add_argument("--collection", help="Collection name (auto-detected from scene)")

    # Add --composite flag to produce
    p_produce.add_argument(
        "--composite",
        action="store_true",
        help="Run scene compositing after generation",
    )
    # Add --graph flag to produce (opts into LangGraph engine)
    p_produce.add_argument(
        "--graph",
        action="store_true",
        help="Use LangGraph engine instead of legacy Coordinator",
    )
    # Add --tryon flag to produce (requires --graph)
    p_produce.add_argument(
        "--tryon",
        action="store_true",
        help="Run virtual try-on after generation (requires --graph; uses FASHN_API_KEY)",
    )

    # produce-async
    p_produce_async = sub.add_parser(
        "produce-async", help="Enqueue a single SKU render job (async)"
    )
    p_produce_async.add_argument("sku", help="Product SKU (e.g., br-001)")
    p_produce_async.add_argument(
        "--view", default="front", choices=["front", "back"], help="View angle"
    )
    p_produce_async.add_argument("--priority", type=int, default=5, help="Job priority 1-10")
    p_produce_async.add_argument(
        "--composite", action="store_true", help="Enable scene compositing"
    )

    # job-status
    p_job_status = sub.add_parser("job-status", help="Check status of a queued job")
    p_job_status.add_argument("job_id", help="Job ID returned by produce-async")

    # job-result
    p_job_result = sub.add_parser("job-result", help="Print full JSON result of a completed job")
    p_job_result.add_argument("job_id", help="Job ID returned by produce-async")

    # dlq-list
    sub.add_parser("dlq-list", help="List all entries in the Dead Letter Queue")

    # dlq-retry
    p_dlq_retry = sub.add_parser("dlq-retry", help="Retry a failed job from the DLQ")
    p_dlq_retry.add_argument("job_id", help="Job ID to retry")

    # worker
    p_worker = sub.add_parser("worker", help="Start the Elite Studio queue worker")
    p_worker.add_argument(
        "--concurrency", type=int, default=1, help="Number of concurrent jobs (default: 1)"
    )

    # create (Creative Operations Hub)
    p_create = sub.add_parser(
        "create", help="Run a creative operation via the Creative Operations Hub"
    )
    p_create.add_argument(
        "--intent",
        required=True,
        help=(
            "Creative intent: product-render, social-pack, product-copy, design-ideation, "
            "collection-plan, tech-pack, moodboard, colorway-explore, 3d-model, "
            "character-sheet, scene-composite, virtual-tryon, full-product-launch, mockup"
        ),
    )
    p_create.add_argument("--sku", default="", help="Product SKU (e.g. br-001)")
    p_create.add_argument(
        "--params",
        default="",
        help='JSON string of additional parameters (e.g. \'{"collection": "black-rose"}\')',
    )

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
    elif args.command == "composite":
        cmd_composite(args)
    elif args.command == "produce-async":
        cmd_produce_async(args)
    elif args.command == "job-status":
        cmd_job_status(args)
    elif args.command == "job-result":
        cmd_job_result(args)
    elif args.command == "dlq-list":
        cmd_dlq_list(args)
    elif args.command == "dlq-retry":
        cmd_dlq_retry(args)
    elif args.command == "worker":
        cmd_worker(args)
    elif args.command == "create":
        cmd_create(args)
