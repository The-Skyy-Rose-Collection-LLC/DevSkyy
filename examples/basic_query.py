"""
Basic Query Example

Demonstrates simple single-query usage of the Agent SDK.
"""

import asyncio
import os

from dotenv import load_dotenv

from agent_sdk.main import DevSkyy

# Load environment variables
load_dotenv()


async def basic_example():
    """Run a simple query using the DevSkyy orchestrator."""
    print("=" * 60)
    print("DevSkyy Agent SDK - Basic Query Example")
    print("=" * 60)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set!")
        print("Please set it in your .env file or environment.")
        return

    # Create DevSkyy instance
    devskyy = DevSkyy()

    # Example 1: Simple question
    print("\n📝 Example 1: Simple Question")
    print("-" * 60)
    task = "What are the key metrics for measuring e-commerce success?"

    result = await devskyy.execute(task, permission_mode="bypassPermissions")  # Safe for questions

    print(f"\nTask: {task}")
    print(f"\nResult:\n{result['result']}")
    print(f"\nCost: ${result.get('total_cost_usd', 0):.4f}")
    print(f"Duration: {result.get('duration_ms', 0)}ms")


async def single_agent_example():
    """Query a specific agent directly."""
    print("\n" + "=" * 60)
    print("Single Agent Query Example")
    print("=" * 60)

    devskyy = DevSkyy()

    # Query the Analytics agent directly
    print("\n📊 Querying Analytics Agent")
    print("-" * 60)

    result = await devskyy.query_agent(
        "analytics",
        "Explain the concept of customer lifetime value (CLV)",
        permission_mode="bypassPermissions",
    )

    print(f"\nAgent: {result['agent']}")
    print(f"\nResult:\n{result['result']}")
    print(f"\nCost: ${result.get('total_cost_usd', 0):.4f}")


async def main():
    """Run all basic examples."""
    try:
        await basic_example()
        await single_agent_example()

        print("\n" + "=" * 60)
        print("✅ Examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
