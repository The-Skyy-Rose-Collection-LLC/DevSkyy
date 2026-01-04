"""
DevSkyy Agent SDK Main Entry Point

Provides convenient access to all Agent SDK capabilities:
- SuperAgents (Commerce, Creative, Marketing, Support, Operations, Analytics)
- Multi-agent orchestration
- LLM Round Table competitions
- Custom MCP tools
"""

import asyncio
from typing import Any

from agent_sdk.orchestrator import AgentOrchestrator
from agent_sdk.round_table import RoundTableOrchestrator


class DevSkyy:
    """
    Main interface for DevSkyy Agent SDK.

    Usage:
        ```python
        from agent_sdk.main import DevSkyy

        async def main():
            devskyy = DevSkyy()

            # Execute with orchestrator
            result = await devskyy.execute("Create a 3D product model and add it to WooCommerce")

            # Query single agent
            result = await devskyy.query_agent("commerce", "List top 10 products")

            # Run Round Table
            result = await devskyy.round_table("Optimize our SEO strategy")

        asyncio.run(main())
        ```
    """

    def __init__(self):
        """Initialize DevSkyy with orchestrators."""
        self.orchestrator = AgentOrchestrator()
        self.round_table = RoundTableOrchestrator()

    async def execute(
        self,
        task: str,
        permission_mode: str = "default",
    ) -> dict[str, Any]:
        """
        Execute a task using the multi-agent orchestrator.

        The orchestrator will automatically determine which SuperAgents are
        needed and coordinate their execution.

        Args:
            task: The task to execute
            permission_mode: Permission mode (default, acceptEdits, bypassPermissions)

        Returns:
            Dict containing result, usage, cost, and metadata

        Example:
            ```python
            result = await devskyy.execute(
                "Create a Valentine's Day marketing campaign with 3D visuals",
                permission_mode="acceptEdits"
            )
            print(result["result"])
            ```
        """
        return await self.orchestrator.execute_workflow(task, permission_mode)

    async def query_agent(
        self,
        agent_name: str,
        task: str,
        permission_mode: str = "acceptEdits",
    ) -> dict[str, Any]:
        """
        Query a specific SuperAgent directly.

        Available agents:
        - commerce: E-commerce operations
        - creative: Visual content generation
        - marketing: Content and SEO
        - support: Customer service
        - operations: DevOps and deployments
        - analytics: Data analysis

        Args:
            agent_name: Name of the agent
            task: Task for the agent
            permission_mode: Permission mode

        Returns:
            Dict containing result, usage, and metadata

        Example:
            ```python
            result = await devskyy.query_agent(
                "creative",
                "Generate a 3D engagement ring model with diamond details"
            )
            ```
        """
        return await self.orchestrator.query_single_agent(agent_name, task, permission_mode)

    async def round_table(
        self,
        task: str,
        models: list | None = None,
    ) -> dict[str, Any]:
        """
        Execute task using LLM Round Table competition.

        Multiple Claude models compete to solve the task, with the best
        response selected through scoring and evaluation.

        Args:
            task: The task to solve
            models: List of models to compete (defaults to all available)

        Returns:
            Dict containing winner's result and competition stats

        Example:
            ```python
            result = await devskyy.round_table(
                "Design a comprehensive email campaign for holiday season"
            )
            print(f"Winner: {result['model']}")
            print(f"Result: {result['result']}")
            ```
        """
        return await self.round_table.execute_with_winner(task, models)


# Convenience functions for quick access
async def execute(task: str, permission_mode: str = "default") -> dict[str, Any]:
    """Quick execute without creating DevSkyy instance."""
    devskyy = DevSkyy()
    return await devskyy.execute(task, permission_mode)


async def query_agent(
    agent_name: str, task: str, permission_mode: str = "acceptEdits"
) -> dict[str, Any]:
    """Quick agent query without creating DevSkyy instance."""
    devskyy = DevSkyy()
    return await devskyy.query_agent(agent_name, task, permission_mode)


async def round_table(task: str, models: list | None = None) -> dict[str, Any]:
    """Quick Round Table without creating DevSkyy instance."""
    devskyy = DevSkyy()
    return await devskyy.round_table(task, models)


if __name__ == "__main__":
    # Example usage
    async def demo():
        devskyy = DevSkyy()

        print("=" * 60)
        print("DevSkyy Agent SDK Demo")
        print("=" * 60)

        # Example 1: Multi-agent workflow
        print("\n1. Multi-Agent Orchestration Example:")
        print("-" * 60)
        result = await devskyy.execute(
            "Analyze our best-selling products and create a social media campaign",
            permission_mode="bypassPermissions",
        )
        print(f"Result: {result['result'][:200]}...")

        # Example 2: Single agent query
        print("\n2. Single Agent Query Example:")
        print("-" * 60)
        result = await devskyy.query_agent(
            "analytics",
            "What are the key metrics I should track for an e-commerce store?",
        )
        print(f"Result: {result['result'][:200]}...")

        # Example 3: Round Table
        print("\n3. LLM Round Table Example:")
        print("-" * 60)
        result = await devskyy.round_table(
            "What's the best strategy for increasing customer lifetime value?"
        )
        print(f"Winner: {result['model']}")
        print(f"Result: {result['result'][:200]}...")

        print("\n" + "=" * 60)
        print("Demo Complete!")
        print("=" * 60)

    asyncio.run(demo())
