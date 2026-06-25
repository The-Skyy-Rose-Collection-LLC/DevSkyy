"""CLI for the Video & Animation venture.

Subcommands:
    info     — print the venture manifest as JSON
    agents   — list bound agents and their wiring status
    status   — one-line status summary
    smoke    — run the compiled pipeline against a synthetic SKU
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections.abc import Sequence

from .pipeline import MANIFEST, VideoPipeline


def _manifest_dict() -> dict[str, object]:
    raw = dataclasses.asdict(MANIFEST)
    raw["status"] = MANIFEST.status.value
    raw["agent_bindings"] = [dataclasses.asdict(b) for b in MANIFEST.agent_bindings]
    return raw


def cmd_info(_: argparse.Namespace) -> int:
    print(json.dumps(_manifest_dict(), indent=2, default=str))
    return 0


def cmd_agents(_: argparse.Namespace) -> int:
    for binding in MANIFEST.agent_bindings:
        wiring = "READY" if binding.ready else "registered"
        print(f"  [{wiring:>10}] {binding.role:<18} {binding.name:<24} {binding.import_path}")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    ready = sum(1 for b in MANIFEST.agent_bindings if b.ready)
    total = len(MANIFEST.agent_bindings)
    print(
        f"{MANIFEST.slug}: {MANIFEST.status.value} "
        f"({ready}/{total} agents wired) — {MANIFEST.title}"
    )
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    pipeline = VideoPipeline()
    result = pipeline.run_smoke(sku=args.sku)
    print(json.dumps(dataclasses.asdict(result), indent=2, default=str))
    return 0 if result.status == "initialized" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skyyrose.elite_studio.ventures.video",
        description="Video & Animation venture — Elite Studio.",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    subparsers.add_parser("info", help="Print the venture manifest as JSON.").set_defaults(
        func=cmd_info
    )
    subparsers.add_parser("agents", help="List bound agents.").set_defaults(func=cmd_agents)
    subparsers.add_parser("status", help="One-line venture status.").set_defaults(func=cmd_status)

    smoke = subparsers.add_parser("smoke", help="Run the compiled pipeline against a SKU.")
    smoke.add_argument("--sku", default="smoke-001", help="Synthetic SKU to feed the pipeline.")
    smoke.set_defaults(func=cmd_smoke)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
