"""CLI entry point for the SkyyRose rendering pipeline.

Usage:
    python -m renders sku br-001                              # Single product
    python -m renders sku br-001 --dry-run                    # Dry run
    python -m renders collection BLACK_ROSE --priority critical
    python -m renders all --priority critical                  # All critical
    python -m renders all --priority high --video              # With video
    python -m renders sync                                     # Sync WC IDs
    python -m renders credits                                  # Check FASHN balance
    python -m renders catalog                                  # Show loaded catalog
"""

from __future__ import annotations

import sys

from renders.config import PRODUCT_CATALOG
from renders.preflight import PreflightAborted, preflight_verify


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="SkyyRose Garment Rendering Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── sku ───────────────────────────────────────────────────────────────
    p_sku = sub.add_parser("sku", help="Render a single product by SKU")
    p_sku.add_argument("sku_id", help="Product SKU (e.g. br-001)")
    _add_render_opts(p_sku)

    # ── collection ────────────────────────────────────────────────────────
    p_col = sub.add_parser("collection", help="Render all products in a collection")
    p_col.add_argument(
        "collection_name",
        choices=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE", "KIDS_CAPSULE"],
    )
    _add_render_opts(p_col)
    p_col.add_argument("--max", type=int, default=None, help="Max products (for testing)")

    # ── all ───────────────────────────────────────────────────────────────
    p_all = sub.add_parser("all", help="Render all products across all collections")
    _add_render_opts(p_all)

    # ── sync ──────────────────────────────────────────────────────────────
    sub.add_parser("sync", help="Sync WooCommerce product IDs by SKU")

    # ── credits ───────────────────────────────────────────────────────────
    sub.add_parser("credits", help="Check FASHN API credit balance")

    # ── catalog ───────────────────────────────────────────────────────────
    sub.add_parser("catalog", help="Print the loaded product catalog")

    args = parser.parse_args()

    # ── Dispatch ──────────────────────────────────────────────────────────

    if args.command == "catalog":
        _print_catalog()
        return

    if args.command == "sync":
        _run_sync()
        return

    if args.command == "credits":
        _check_credits()
        return

    # Rendering commands need the agent
    from renders.pipeline import GarmentFidelityAgent

    dry_run = getattr(args, "dry_run", False)
    skip_pf = getattr(args, "skip_preflight", False)

    # ── PRE-FLIGHT: show source mapping before spending any credits ───────────
    if args.command == "sku":
        pf_products = [p for p in PRODUCT_CATALOG if p["sku"] == args.sku_id]
    elif args.command == "collection":
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        max_prio = priority_order.get(args.priority, 3) if args.priority else 3
        pf_products = [
            p
            for p in PRODUCT_CATALOG
            if p["collection"] == args.collection_name
            and priority_order.get(p.get("render_priority", "low"), 3) <= max_prio
        ]
        if getattr(args, "max", None):
            pf_products = pf_products[: args.max]
    else:  # all
        pf_products = PRODUCT_CATALOG

    try:
        preflight_verify(
            pf_products,
            include_bg_remove=not getattr(args, "no_bg_remove", False),
            include_video=getattr(args, "video", False),
            skip=skip_pf,
        )
    except PreflightAborted as e:
        print(f"  Preflight aborted: {e}")
        sys.exit(0)
    # ─────────────────────────────────────────────────────────────────────────

    agent = GarmentFidelityAgent(dry_run=dry_run)

    if args.command == "sku":
        result = agent.render_sku(
            args.sku_id,
            generate_video=args.video,
            clean_background=not args.no_bg_remove,
        )
        agent.save_run_log()
        if result.get("error"):
            sys.exit(1)

    elif args.command == "collection":
        agent.render_collection(
            collection_name=args.collection_name,
            priority_filter=args.priority,
            generate_video=args.video,
            max_products=args.max,
        )
        agent.save_run_log()

    elif args.command == "all":
        agent.render_all_products(
            priority_filter=args.priority or "critical",
            generate_video=args.video,
        )
        agent.save_run_log()


def _add_render_opts(parser: object) -> None:
    """Add common rendering options to a subparser."""
    parser.add_argument(  # type: ignore[union-attr]
        "--priority",
        choices=["critical", "high", "medium", "low"],
        default=None,
        help="Only process at this priority or higher",
    )
    parser.add_argument(  # type: ignore[union-attr]
        "--video",
        action="store_true",
        help="Also generate video clips from best renders",
    )
    parser.add_argument(  # type: ignore[union-attr]
        "--dry-run",
        action="store_true",
        help="Simulate without making API calls",
    )
    parser.add_argument(  # type: ignore[union-attr]
        "--no-bg-remove",
        action="store_true",
        help="Skip background removal step",
    )
    parser.add_argument(  # type: ignore[union-attr]
        "--skip-preflight",
        action="store_true",
        help="Skip source-photo confirmation (CI/automation only)",
    )


# ── Commands ─────────────────────────────────────────────────────────────────


def _run_sync() -> None:
    """Sync WooCommerce product IDs for all catalog items."""
    from renders.wc_client import WooCommerceClient

    wc = WooCommerceClient()
    wc.sync_sku_to_wc_id(PRODUCT_CATALOG)

    # Show results
    print(f"\n{'SKU':<18} {'WC ID':<8} {'Name'}")
    print("-" * 70)
    for p in PRODUCT_CATALOG:
        wc_id = p.get("wc_id") or "---"
        print(f"{p['sku']:<18} {str(wc_id):<8} {p['name']}")

    synced = sum(1 for p in PRODUCT_CATALOG if p.get("wc_id"))
    print(f"\nSynced: {synced}/{len(PRODUCT_CATALOG)} products")


def _check_credits() -> None:
    """Check FASHN API credit balance."""
    from renders.fashn_client import FASHNClient

    client = FASHNClient()
    result = client.get_credits()

    if "error" in result:
        print(f"Could not fetch credits: {result['error']}")
        if "hint" in result:
            print(f"Hint: {result['hint']}")
    else:
        print("FASHN API Credits:")
        for k, v in result.items():
            print(f"  {k}: {v}")

    client.close()


def _print_catalog() -> None:
    """Print the loaded product catalog."""
    print(f"\nSkyyRose Product Catalog ({len(PRODUCT_CATALOG)} products)")
    print("-" * 80)
    print(f"{'SKU':<18} {'Collection':<14} {'Priority':<10} {'Source':<6} {'Name'}")
    print("-" * 80)

    for p in PRODUCT_CATALOG:
        has_source = "YES" if p.get("existing_front") else "---"
        print(
            f"{p['sku']:<18} {p['collection']:<14} {p['render_priority']:<10} "
            f"{has_source:<6} {p['name']}"
        )

    by_collection: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    with_source = 0

    for p in PRODUCT_CATALOG:
        by_collection[p["collection"]] = by_collection.get(p["collection"], 0) + 1
        by_priority[p["render_priority"]] = by_priority.get(p["render_priority"], 0) + 1
        if p.get("existing_front"):
            with_source += 1

    print(f"\nCollections: {by_collection}")
    print(f"Priorities:  {by_priority}")
    print(f"With source: {with_source}/{len(PRODUCT_CATALOG)}")


if __name__ == "__main__":
    main()
