"""
Dynamic Agent and Tool Counter
===============================

Provides accurate, real-time counts of agents and tools in the DevSkyy platform.

This module replaces hardcoded agent counts with dynamic discovery by:
- Counting MCP server tools from devskyy_mcp.py
- Scanning SuperAgent files in agent_sdk/super_agents/
- Optionally counting legacy agents in agents/

The health endpoint uses this to report accurate system capacity.

Architecture Note:
    DevSkyy consolidated 54+ specialized agents into 6 SuperAgents.
    Total AI capabilities: 21 MCP tools + 6 SuperAgents = 27 total

Usage:
    from orchestration.agent_counter import count_active_agents

    counts = await count_active_agents()
    # Returns: {
    #     "mcp_tools": 21,
    #     "super_agents": 6,
    #     "legacy_agents": 15,
    #     "total": 27,
    #     "active": 27
    # }
"""

import logging
from pathlib import Path

from utils.ralph_wiggums import ErrorCategory, ralph_wiggums_execute

logger = logging.getLogger(__name__)


async def count_active_agents() -> dict[str, int]:
    """
    Dynamically count all agents and tools in the system with Ralph-Wiggums error handling.

    Returns:
        dict: Agent counts including:
            - mcp_tools: Number of MCP server tools
            - super_agents: Number of SuperAgent classes
            - legacy_agents: Number of legacy agent classes
            - total: mcp_tools + super_agents
            - active: Same as total (assumes all are operational)
    """

    async def attempt_count() -> dict[str, int]:
        """Inner counting logic with error handling."""
        try:
            # Get project root
            project_root = Path(__file__).parent.parent

            # Count MCP tools from devskyy_mcp.py
            mcp_file = project_root / "devskyy_mcp.py"
            mcp_tools_count = 0

            if mcp_file.exists():
                content = mcp_file.read_text()
                # Count @mcp.tool decorators
                mcp_tools_count = content.count("@mcp.tool")
                logger.debug(f"Found {mcp_tools_count} MCP tools in devskyy_mcp.py")
            else:
                logger.warning(f"MCP file not found: {mcp_file}")

            # Count SuperAgents in agent_sdk/super_agents/
            super_agents_dir = project_root / "agent_sdk" / "super_agents"
            super_agents_count = 0

            if super_agents_dir.exists():
                super_agent_files = [
                    f for f in super_agents_dir.glob("*_agent.py") if f.stem != "__init__"
                ]
                super_agents_count = len(super_agent_files)
                logger.debug(f"Found {super_agents_count} SuperAgents in {super_agents_dir}")
            else:
                logger.warning(f"SuperAgents directory not found: {super_agents_dir}")

            # Count legacy agents in agents/
            legacy_agents_dir = project_root / "agents"
            legacy_agents_count = 0

            if legacy_agents_dir.exists():
                legacy_agent_files = [
                    f
                    for f in legacy_agents_dir.glob("*_agent.py")
                    if f.stem not in ["__init__", "base_super_agent"]
                ]
                legacy_agents_count = len(legacy_agent_files)
                logger.debug(f"Found {legacy_agents_count} legacy agents in {legacy_agents_dir}")
            else:
                logger.warning(f"Legacy agents directory not found: {legacy_agents_dir}")

            # Calculate totals
            total = mcp_tools_count + super_agents_count

            return {
                "mcp_tools": mcp_tools_count,
                "super_agents": super_agents_count,
                "legacy_agents": legacy_agents_count,
                "total": total,
                "active": total,  # Assume all discovered agents are active
            }

        except Exception as e:
            logger.error(f"Error counting agents: {e}")
            raise

    # Use Ralph-Wiggums loop for resilient counting
    success, result, error = await ralph_wiggums_execute(
        attempt_count,
        fallbacks=None,
        max_attempts=2,
        base_delay=0.5,
        max_delay=2.0,
        retry_categories=[
            ErrorCategory.NETWORK,
            ErrorCategory.SERVER_ERROR,
        ],
    )

    if not success:
        # Fallback to safe default counts if discovery fails
        logger.error(f"Agent counting failed after retries: {error}. Using default counts.")
        return {
            "mcp_tools": 21,
            "super_agents": 6,
            "legacy_agents": 15,
            "total": 27,
            "active": 27,
        }

    logger.info(
        f"Agent count: {result['mcp_tools']} MCP tools + "
        f"{result['super_agents']} SuperAgents = {result['total']} total"
    )

    return result


def count_active_agents_sync() -> dict[str, int]:
    """
    Synchronous version of count_active_agents for non-async contexts.

    Note: This performs file system operations without async benefits.
    Prefer the async version when possible.

    Returns:
        dict: Agent counts
    """
    try:
        # Get project root
        project_root = Path(__file__).parent.parent

        # Count MCP tools
        mcp_file = project_root / "devskyy_mcp.py"
        mcp_tools_count = 0
        if mcp_file.exists():
            content = mcp_file.read_text()
            mcp_tools_count = content.count("@mcp.tool")

        # Count SuperAgents
        super_agents_dir = project_root / "agent_sdk" / "super_agents"
        super_agents_count = 0
        if super_agents_dir.exists():
            super_agent_files = [
                f for f in super_agents_dir.glob("*_agent.py") if f.stem != "__init__"
            ]
            super_agents_count = len(super_agent_files)

        # Count legacy agents
        legacy_agents_dir = project_root / "agents"
        legacy_agents_count = 0
        if legacy_agents_dir.exists():
            legacy_agent_files = [
                f
                for f in legacy_agents_dir.glob("*_agent.py")
                if f.stem not in ["__init__", "base_super_agent"]
            ]
            legacy_agents_count = len(legacy_agent_files)

        total = mcp_tools_count + super_agents_count

        return {
            "mcp_tools": mcp_tools_count,
            "super_agents": super_agents_count,
            "legacy_agents": legacy_agents_count,
            "total": total,
            "active": total,
        }

    except Exception as e:
        logger.error(f"Sync agent counting failed: {e}. Using defaults.")
        return {
            "mcp_tools": 21,
            "super_agents": 6,
            "legacy_agents": 15,
            "total": 27,
            "active": 27,
        }


__all__ = ["count_active_agents", "count_active_agents_sync"]
