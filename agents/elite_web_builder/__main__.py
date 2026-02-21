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
    """
    Create an ArgumentParser configured for the elite_web_builder command-line interface.
    
    The parser enforces a required mutually exclusive PRD input (either an inline positional `prd` or `--file` path).
    It also defines:
    - `--dry-run`: plan stories only without executing.
    - `--config`: path to a JSON routing override.
    - `--max-stories`: maximum number of stories to generate (default 50).
    
    Returns:
        argparse.ArgumentParser: Configured parser for the CLI.
    """
    parser = argparse.ArgumentParser(
        prog="elite_web_builder",
        description="Elite Web Builder — Full-stack AI web development agency",
    )

    parser.add_argument(
        "prd",
        nargs="?",
        default=None,
        help="Inline PRD text",
    )
    parser.add_argument(
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
    """
    Load and return the product requirements document (PRD) text from parsed CLI arguments.
    
    If args.file is provided, the function reads and returns the file's contents; otherwise it returns the inline PRD string from args.prd.
    
    Parameters:
        args (argparse.Namespace): Parsed CLI arguments. Expected attributes:
            - file (pathlib.Path | None): Optional path to a PRD file.
            - prd (str): Inline PRD text provided on the command line.
    
    Returns:
        str: The PRD text to be processed.
    """
    if args.file:
        if not args.file.exists():
            print(f"Error: PRD file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        return args.file.read_text()
    return args.prd


def _print_report(report: object) -> None:
    """
    Print a human-readable project report to stdout.
    
    Prints a header, a summary (stories count, status summary, `all_green`, elapsed milliseconds, and instincts learned), an optional failures list, and detailed lines for each story showing a status icon, story id, title, and status value.
    
    Parameters:
        report (object): Project report object expected to provide:
            - stories: iterable of story objects with `id`, `title`, and `status` (enum with a `value`).
            - status_summary: str
            - all_green: bool
            - elapsed_ms: number (milliseconds)
            - instincts_learned: int
            - failures: iterable of failure messages (may be empty)
    """
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
    """
    Orchestrates the CLI workflow: load PRD text, construct the Director, and perform either a dry-run planning pass or full execution.
    
    When args.dry_run is set, prints a planned story breakdown and returns 0 on success or 1 if planning fails. In full execution mode, runs the director, prints the resulting report, and returns 0 if the report indicates all stories succeeded, otherwise 1.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
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