"""
CLI entry point for Elite Web Builder.

Usage:
  python -m elite_web_builder "PRD text here"
  python -m elite_web_builder --file prd.md
  python -m elite_web_builder --file prd.md --dry-run
  python -m elite_web_builder --file prd.md --config routing.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .director import Director, DirectorConfig, StoryStatus


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="elite_web_builder",
        description="Elite Web Builder — Full-stack AI web development agency",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "prd",
        nargs="?",
        default=None,
        help="Inline PRD text",
    )
    group.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Path to PRD file (.md or .txt)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Plan stories only, do not execute",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to provider routing JSON override",
    )
    parser.add_argument(
        "--max-stories",
        type=int,
        default=50,
        help="Maximum number of stories to generate (default: 50)",
    )

    return parser


def _load_prd(args: argparse.Namespace) -> str:
    """Load PRD text from args."""
    if args.file:
        if not args.file.exists():
            print(f"Error: PRD file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        return args.file.read_text()
    return args.prd


def _print_report(report: object) -> None:
    """Print a ProjectReport to stdout."""
    print("\n" + "=" * 60)
    print("ELITE WEB BUILDER — PROJECT REPORT")
    print("=" * 60)

    print(f"\nStories: {len(report.stories)}")
    print(f"Status: {report.status_summary}")
    print(f"All Green: {report.all_green}")
    print(f"Elapsed: {report.elapsed_ms:.0f}ms")
    print(f"Instincts Learned: {report.instincts_learned}")

    if report.failures:
        print(f"\nFailures ({len(report.failures)}):")
        for failure in report.failures:
            print(f"  - {failure}")

    if report.stories:
        print("\nStory Details:")
        for story in report.stories:
            status_icon = "✓" if story.status == StoryStatus.GREEN else "✗"
            print(f"  {status_icon} {story.id}: {story.title} [{story.status.value}]")

    print("\n" + "=" * 60)


async def _run(args: argparse.Namespace) -> int:
    """Main async entry point."""
    prd_text = _load_prd(args)

    # Build config
    config = DirectorConfig(max_stories=args.max_stories)
    if args.config:
        config.routing_config_path = args.config

    director = Director(config=config)

    if args.dry_run:
        # Plan only
        print("DRY RUN — Planning stories only\n")
        try:
            breakdown = await director._plan_stories(prd_text)
        except Exception as exc:
            print(f"Planning failed: {exc}", file=sys.stderr)
            return 1

        print(f"Stories ({len(breakdown.stories)}):")
        for story in breakdown.stories:
            deps = ", ".join(story.depends_on) if story.depends_on else "none"
            print(f"  {story.id}: {story.title}")
            print(f"    Agent: {story.agent_role.value}")
            print(f"    Deps: {deps}")
            print()

        if breakdown.dependency_order:
            print(f"Execution Order: {' → '.join(breakdown.dependency_order)}")
        return 0

    # Full execution
    report = await director.execute_prd(prd_text)
    _print_report(report)
    return 0 if report.all_green else 1


def main() -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()
    exit_code = asyncio.run(_run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
