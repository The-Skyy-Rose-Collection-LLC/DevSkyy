"""
CLI entry point for the SkyyRose Multi-Agent System.

Usage:
    # Full orchestrator (Opus decides what to delegate)
    python -m skyyrose.multi_agent "Audit the theme and check product catalog"

    # Single agent mode
    python -m skyyrose.multi_agent --agent brand-writer "Write copy for br-001"
    python -m skyyrose.multi_agent --agent theme-auditor "Check CSS architecture"
    python -m skyyrose.multi_agent --agent product-analyst "Find products missing images"
    python -m skyyrose.multi_agent --agent deploy-manager "Check deployment status"
    python -m skyyrose.multi_agent --agent qa-inspector "Run regression checks"

    # Interactive multi-turn conversation
    python -m skyyrose.multi_agent --interactive "Let's review the platform"

    # List available agents
    python -m skyyrose.multi_agent --list-agents

    # Budget control
    python -m skyyrose.multi_agent --budget 2.0 "Quick check on fonts"
"""

from __future__ import annotations

import argparse
import sys

import anyio

from .agents import AGENT_DEFINITIONS
from .orchestrator import run_orchestrator, run_single_agent


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="SkyyRose Multi-Agent System — Claude Agent SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Audit the WordPress theme for a11y issues"
  %(prog)s --agent brand-writer "Write Instagram captions for Black Rose"
  %(prog)s --agent qa-inspector "Check for regression on font sizes"
  %(prog)s --interactive "Let's review everything"
  %(prog)s --list-agents
        """,
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Task prompt for the orchestrator or agent",
    )
    parser.add_argument(
        "--agent",
        "-a",
        choices=list(AGENT_DEFINITIONS.keys()),
        help="Run a specific subagent directly (bypasses orchestrator)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive multi-turn conversation mode",
    )
    parser.add_argument(
        "--budget",
        "-b",
        type=float,
        default=5.0,
        help="Maximum budget in USD (default: $5.00)",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all available subagents and exit",
    )

    args = parser.parse_args(argv)

    # List agents
    if args.list_agents:
        print("\nSkyyRose Multi-Agent System")
        print("=" * 50)
        for name, defn in AGENT_DEFINITIONS.items():
            print(f"\n  {name}")
            print(f"    {defn.description}")
        print()
        return

    # Require prompt
    if not args.prompt:
        parser.print_help()
        sys.exit(1)

    # Banner
    print()
    print("=" * 60)
    print("  SKYYROSE MULTI-AGENT SYSTEM")
    if args.agent:
        print(f"  Agent: {args.agent}")
    else:
        print("  Mode: Orchestrator (Opus 4.6)")
    print(f"  Budget: ${args.budget:.2f}")
    print("=" * 60)
    print()

    # Run
    if args.agent:
        anyio.run(
            run_single_agent,
            args.agent,
            args.prompt,
            args.budget,
        )
    else:
        anyio.run(
            run_orchestrator,
            args.prompt,
            args.interactive,
            args.budget,
        )


if __name__ == "__main__":
    main()
