#!/usr/bin/env python3
"""
Claude Agent SDK v0.1.9 Example
Demonstrates the new ClaudeAgentOptions API for managing settings
"""

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query


async def example_default_settings():
    """
    Example 1: Using default settings (no automatic loading)

    In v0.1.0+, settings are NOT loaded automatically by default.
    This gives you full control over what gets loaded.
    """

    async for _message in query(prompt="What is the capital of France?"):
        pass


async def example_with_all_settings():
    """
    Example 2: Load all settings (similar to v0.0.x behavior)

    To get the old v0.0.x behavior where all settings were loaded
    automatically, specify all setting sources.
    """

    options = ClaudeAgentOptions(setting_sources=["user", "project", "local"])

    async for _message in query(prompt="Explain quantum computing in simple terms", options=options):
        pass


async def example_with_project_only():
    """
    Example 3: Load only project settings

    For team collaboration, you might want only project-level
    settings without user-specific customizations.
    """

    options = ClaudeAgentOptions(setting_sources=["project"])  # Only .claude/settings.json

    async for _message in query(prompt="Write a Python function to calculate fibonacci numbers", options=options):
        pass


async def example_with_custom_model():
    """
    Example 4: Specify custom model and settings

    Combine settings sources with custom model selection.
    """

    options = ClaudeAgentOptions(setting_sources=["project"], model="claude-sonnet-4-5-20250929")  # Latest Sonnet 4.5

    async for _message in query(prompt="Explain the Observer pattern in software design", options=options):
        pass


async def example_streaming():
    """
    Example 5: Streaming responses with settings

    The query() function returns an async generator for streaming.
    """

    options = ClaudeAgentOptions(setting_sources=["project", "local"])

    async for _chunk in query(prompt="Count from 1 to 5", options=options):
        pass


async def main():
    """Run all examples"""

    try:
        # Run examples
        await example_default_settings()
        await example_with_all_settings()
        await example_with_project_only()
        await example_with_custom_model()
        await example_streaming()

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Note: Requires ANTHROPIC_API_KEY environment variable
    asyncio.run(main())
