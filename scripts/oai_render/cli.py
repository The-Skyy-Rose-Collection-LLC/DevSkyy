"""Executable CLI for the gpt-image-2 render pipeline.

  dry-run  — resolve references + prompts + cost manifest, ZERO API calls (default-safe)
  generate — same, then render. Gated: prints the manifest, enforces the hard
             cost cap, and refuses to spend without an explicit --yes.

Examples:
  python scripts/oai-render-run.py dry-run --sku br-010
  python scripts/oai-render-run.py dry-run --all
  python scripts/oai-render-run.py generate --sku br-010 --yes
"""

from __future__ import annotations

import argparse
import logging

from . import config, cost, pipeline
from .prompt import PRESENTATIONS
from .references import build_dossier_index, load_catalog


def _add_target_args(p: argparse.ArgumentParser) -> None:
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--sku", help="Render a single SKU (e.g. br-010).")
    grp.add_argument(
        "--skus", help="Render a comma-separated SKU list (e.g. br-010,sg-015,br-001)."
    )
    grp.add_argument("--collection", help="Render a collection slug (e.g. black-rose).")
    grp.add_argument("--all", action="store_true", help="Render the entire catalog.")
    p.add_argument(
        "--style",
        default="ghost,on-model",
        help=(
            "Comma-separated presentation styles per SKU "
            f"({', '.join(PRESENTATIONS)}). Default: ghost,on-model."
        ),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oai-render", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    _add_target_args(sub.add_parser("dry-run", help="Plan + manifest, no API calls."))
    gen = sub.add_parser("generate", help="Render (paid; requires --yes).")
    _add_target_args(gen)
    gen.add_argument(
        "--yes", action="store_true", help="Confirm paid generation after the manifest."
    )
    gen.add_argument(
        "--skip-asset-verify",
        action="store_true",
        help="Skip the pre-flight asset-manifest integrity check (NOT recommended).",
    )
    return parser


def _print_skips(plans) -> None:
    for plan in plans:
        if not plan.renderable:
            print(f"  SKIP {plan.sku}: {plan.error}")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_parser().parse_args(argv)

    catalog = load_catalog()
    dossier_index = build_dossier_index()

    try:
        skus_arg = getattr(args, "skus", None)
        targets = pipeline.resolve_targets(
            catalog,
            sku=getattr(args, "sku", None),
            skus=[s.strip() for s in skus_arg.split(",") if s.strip()] if skus_arg else None,
            collection=getattr(args, "collection", None),
            all_skus=getattr(args, "all", False),
        )
    except KeyError as exc:
        print(f"ERROR: {exc}")
        return 1
    if not targets:
        print("No SKUs matched. Use --sku / --collection / --all.")
        return 1

    styles = [s.strip() for s in args.style.split(",") if s.strip()]
    bad = [s for s in styles if s not in PRESENTATIONS]
    if bad or not styles:
        print(f"ERROR: invalid --style {bad or '(empty)'}. Choose from: {', '.join(PRESENTATIONS)}")
        return 1

    # Always plan first (no API) and show the manifest.
    dry = pipeline.run(targets, catalog, dossier_index, styles=styles, dry_run=True)
    manifest = dry["manifest"]
    print(cost.format_manifest(manifest))
    _print_skips(dry["plans"])

    if args.command == "dry-run":
        print(f"\nDRY RUN — no API calls. OPENAI_API_KEY present: {config.api_key_present()}")
        return 0

    # generate
    try:
        cost.enforce_cap(manifest)
    except cost.CostCapExceeded as exc:
        print(f"\nABORT: {exc}")
        return 3

    renderable = [p for p in dry["plans"] if p.renderable]
    if not renderable:
        print("\nNothing renderable (all SKUs skipped). Resolve references first.")
        return 1

    if not args.yes:
        print("\nPaid generation is gated. Re-run with --yes to proceed.")
        return 2

    # Asset-integrity gate BEFORE constructing the client — so a drifted-source
    # run reports the actionable drift rather than a confusing "API key missing"
    # if the key happens to be absent. render_all re-runs the same gate for any
    # non-CLI caller; here we've already checked, so it renders with it off.
    if not args.skip_asset_verify:
        drift = pipeline.verify_plan_assets(dry["plans"])
        if drift:
            print("\nABORT: asset integrity check failed before paid generation.")
            print("  A source file changed or vanished since the manifest was committed —")
            print("  rendering against it risks the bug-119 wrong-product class. Findings:")
            for d in drift:
                print(f"    {d.sku:<14} {d.role:<13} {d.kind:<14} {d.path}")
            print(
                "\n  Resolve the file, regenerate with `python scripts/build_asset_manifest.py`,\n"
                "  confirm the change is intended, then re-run. Override with --skip-asset-verify."
            )
            return 4

    from .client import OAIImageClient

    client = OAIImageClient()  # validates the API key
    # Render the EXACT plans the manifest was built from (no re-plan → no TOCTOU).
    results = pipeline.render_all(dry["plans"], client, verify_assets=False)

    rendered = [r for r in results if r.status == "rendered"]
    errored = [r for r in results if r.status == "error"]
    skipped = [r for r in results if r.status == "skipped"]
    qc_failed = [r for r in results if r.status == "qc_failed"]
    print(
        f"\nDone — {len(rendered)} rendered, {len(skipped)} skipped, "
        f"{len(errored)} errored, {len(qc_failed)} QC-failed."
    )
    for r in rendered:
        print(f"  ✓ {r.sku} → {r.output_path}")
    for r in errored:
        print(f"  ✗ {r.sku}: {r.reason}")
    for r in qc_failed:
        print(f"  ⚠ {r.sku} QC-failed (quarantined in renders/oai/_rejected/): {r.reason}")
    return 0 if not (errored or qc_failed) else 4


if __name__ == "__main__":
    raise SystemExit(main())
