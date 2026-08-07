#!/usr/bin/env python3
"""Safe, lazy entry point for the optional Elite Web Builder runtime.

Planning is the default and makes no provider calls. Live execution requires an
explicit PRD, routing file, and two approval flags. This runner never searches
for or loads repository ``.env`` files.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}")
    return value


def _read_prd(path: Path) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SystemExit(f"Unable to read PRD {path}: {exc}") from exc
    if not value:
        raise SystemExit(f"PRD is empty: {path}")
    return value


def _required_keys(routing: dict[str, Any]) -> set[str]:
    provider_keys = {
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "xai": "XAI_API_KEY",
    }
    providers: set[str] = set()
    for route in routing.get("routes", {}).values():
        if isinstance(route, dict) and isinstance(route.get("provider"), str):
            providers.add(route["provider"])
    return {provider_keys[p] for p in providers if p in provider_keys}


async def _execute(prd_text: str, routing: dict[str, Any]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    # Heavy SDK-backed runtime is imported only after explicit live approval.
    from director import Director

    report = await Director.from_config(routing_config=routing).execute_prd(prd_text)
    summary = {
        "all_green": report.all_green,
        "status_summary": report.status_summary,
        "elapsed_ms": report.elapsed_ms,
        "failures": report.failures,
        "instincts_learned": report.instincts_learned,
        "cost_usd": report.cost_usd,
        "cost_details": report.cost_details,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or explicitly execute the optional Elite Web Builder runtime",
    )
    parser.add_argument("--prd", type=Path, required=True, help="Canonical PRD path")
    parser.add_argument("--routing", type=Path, help="Explicit provider routing JSON")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Enable provider-backed execution; omitted means local planning preview",
    )
    parser.add_argument(
        "--approved-paid-providers",
        action="store_true",
        help="Confirms founder approval for provider calls and their cost",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    prd_text = _read_prd(args.prd)

    if not args.execute:
        print("PLAN_ONLY: no provider SDKs loaded and no external calls made")
        print(f"PRD: {args.prd.resolve()}")
        print(f"Characters: {len(prd_text)}")
        print(prd_text[:500])
        return

    if not args.approved_paid_providers:
        raise SystemExit("Live execution requires --approved-paid-providers")
    if args.routing is None:
        raise SystemExit("Live execution requires --routing with an approved routing file")

    routing = _load_json(args.routing)
    missing = sorted(key for key in _required_keys(routing) if not os.getenv(key))
    if missing:
        raise SystemExit("Missing required environment variables: " + ", ".join(missing))

    asyncio.run(_execute(prd_text, routing))


if __name__ == "__main__":
    main()
