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
    """
    Retrieve the product requirements document (PRD) text from parsed CLI arguments.
    
    If args.file is provided, read and return its contents; if the file does not exist, print an error to stderr and exit with code 1. Otherwise return the inline PRD string from args.prd.
    
    Parameters:
        args (argparse.Namespace): Parsed CLI arguments. Expected attributes:
            file (pathlib.Path | None): Optional path to a PRD file.
            prd (str): Inline PRD text provided on the command line.
    
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
    Orchestrates the CLI workflow to plan or execute a product requirement document (PRD).
    
    Performs these high-level steps based on the parsed CLI arguments:
    - Loads PRD text from args (inline or file).
    - Constructs a Director configured with args.max_stories and optional routing config.
    - If args.dry_run is true, produces and prints a planned story breakdown; on planning failure prints an error to stderr and returns a failure code.
    - If not a dry run, executes the PRD via the Director and prints a human-readable report.
    
    Parameters:
        args (argparse.Namespace): Parsed CLI arguments. Expected attributes include:
            - prd or file: PRD text or path to a PRD file.
            - dry_run (bool): If true, perform planning only.
            - config (Path|str|None): Optional routing config path.
            - max_stories (int): Maximum number of stories to generate.
    
    Returns:
        int: Exit code — `0` when planning succeeds (dry run) or when execution completes with all stories succeeded; `1` otherwise.
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
    """
    Start the CLI: parse command-line arguments, run the async workflow, and exit with its result code.
    
    Parses argv using the module parser, executes the coroutine that plans or runs the PRD, and terminates the process with the returned exit code.
    """
    parser = _build_parser()
    args = parser.parse_args()
    exit_code = asyncio.run(_run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()