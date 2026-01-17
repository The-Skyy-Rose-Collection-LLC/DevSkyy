#!/usr/bin/env python3
"""
Claude Agent SDK Demo - Build autonomous AI agents
Docs: https://platform.claude.com/docs/en/agent-sdk/overview
"""

import asyncio

from claude_agent_sdk import query


async def basic_query_demo():
    """Simple query example."""
    print("=" * 70)
    print("Claude Agent SDK - Basic Query Demo")
    print("=" * 70)

    async for message in query(prompt="What is 2 + 2? Explain step by step."):
        print(message, end="", flush=True)
    print("\n")


async def code_execution_demo():
    """Agent that can read files and execute commands."""
    print("=" * 70)
    print("Claude Agent SDK - Code Execution Demo")
    print("=" * 70)

    prompt = """
    Analyze the DevSkyy project structure:
    1. Read the main README.md file
    2. List all Python files in the agents/ directory
    3. Count total lines of Python code

    Use bash commands and file reading tools.
    """

    async for message in query(prompt=prompt):
        print(message, end="", flush=True)
    print("\n")


async def main():
    """Run demos."""
    # Uncomment to run demos:

    # Demo 1: Basic query
    # await basic_query_demo()

    # Demo 2: Code execution (requires ANTHROPIC_API_KEY)
    # await code_execution_demo()

    print("✅ Claude Agent SDK demos ready")
    print("\nUsage:")
    print("  1. Set ANTHROPIC_API_KEY environment variable")
    print("  2. Uncomment demo functions in examples/claude_agent_sdk_demo.py")
    print("  3. Run: python3 examples/claude_agent_sdk_demo.py")
    print("\nDocs: https://platform.claude.com/docs/en/agent-sdk/overview")


if __name__ == "__main__":
    asyncio.run(main())
