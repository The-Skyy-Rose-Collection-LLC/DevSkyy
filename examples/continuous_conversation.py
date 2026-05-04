"""
Continuous Conversation Example

Demonstrates maintaining context across multiple exchanges using ClaudeSDKClient.
"""

import asyncio
import os

from agent_sdk.custom_tools import create_devskyy_tools
from agent_sdk.super_agents import MarketingAgent
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    TextBlock,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def interactive_conversation():
    """
    Interactive conversation with context persistence.

    Demonstrates how Claude remembers previous messages in the session.
    """
    print("=" * 60)
    print("Continuous Conversation Example")
    print("=" * 60)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set!")
        return

    # Set up Marketing Agent with custom tools
    mcp_server = create_devskyy_tools()
    options = MarketingAgent.get_standalone_options()
    options.mcp_servers = {"devskyy": mcp_server}
    options.permission_mode = "bypassPermissions"

    async with ClaudeSDKClient(options=options) as client:
        print("\n💬 Starting conversation with Marketing Agent")
        print("-" * 60)

        # Turn 1: Initial request
        print("\n[Turn 1] User: Create a Valentine's Day email subject line")
        await client.query("Create a Valentine's Day email subject line for SkyyRose")

        response_1 = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_1.append(block.text)

        print(f"\n[Turn 1] Agent:\n{''.join(response_1)}")

        # Turn 2: Follow-up (Claude remembers the subject line from Turn 1)
        print("\n" + "-" * 60)
        print("\n[Turn 2] User: Make it more romantic and add urgency")
        await client.query("Make it more romantic and add a sense of urgency")

        response_2 = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_2.append(block.text)

        print(f"\n[Turn 2] Agent:\n{''.join(response_2)}")

        # Turn 3: Another follow-up (Claude still remembers context)
        print("\n" + "-" * 60)
        print("\n[Turn 3] User: Now write the email body to match that subject")
        await client.query("Now write a compelling email body that matches that subject line")

        response_3 = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_3.append(block.text)

        print(f"\n[Turn 3] Agent:\n{''.join(response_3)}")


async def multi_turn_analysis():
    """
    Multi-turn analytical conversation.

    Demonstrates building analysis across multiple exchanges.
    """
    print("\n" + "=" * 60)
    print("Multi-Turn Analysis Example")
    print("=" * 60)

    from agent_sdk.super_agents import AnalyticsAgent

    mcp_server = create_devskyy_tools()
    options = AnalyticsAgent.get_standalone_options()
    options.mcp_servers = {"devskyy": mcp_server}

    async with ClaudeSDKClient(options=options) as client:
        print("\n📊 Starting analytical conversation")
        print("-" * 60)

        # Turn 1: Set context
        print("\n[Turn 1] User: Define customer lifetime value")
        await client.query("Explain customer lifetime value (CLV) for an e-commerce business")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"\n[Turn 1] Agent:\n{block.text}")

        # Turn 2: Build on that knowledge
        print("\n" + "-" * 60)
        print("\n[Turn 2] User: How do we calculate it?")
        await client.query("How do we calculate CLV for SkyyRose customers?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"\n[Turn 2] Agent:\n{block.text}")

        # Turn 3: Apply it
        print("\n" + "-" * 60)
        print("\n[Turn 3] User: Create action plan")
        await client.query(
            "Based on that calculation, what strategies should we implement to increase CLV?"
        )

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"\n[Turn 3] Agent:\n{block.text}")


async def collaborative_workflow():
    """
    Demonstrate collaborative back-and-forth workflow.

    Shows how to use conversation for iterative refinement.
    """
    print("\n" + "=" * 60)
    print("Collaborative Workflow Example")
    print("=" * 60)

    from agent_sdk.super_agents import CreativeAgent

    mcp_server = create_devskyy_tools()
    options = CreativeAgent.get_standalone_options()
    options.mcp_servers = {"devskyy": mcp_server}

    async with ClaudeSDKClient(options=options) as client:
        print("\n🎨 Iterative creative workflow")
        print("-" * 60)

        # Initial brief
        print("\n[Brief] Create 3D product concept")
        await client.query(
            "I need a 3D concept for a new engagement ring. It should be elegant and modern."
        )

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"\n[Agent]:\n{block.text}")

        # Refinement 1
        print("\n" + "-" * 60)
        print("\n[Feedback] Add more romantic elements")
        await client.query(
            "That's good, but add more romantic elements - maybe heart-shaped details"
        )

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"\n[Agent]:\n{block.text}")

        # Refinement 2
        print("\n" + "-" * 60)
        print("\n[Feedback] Adjust for brand")
        await client.query("Perfect! Now make sure it aligns with SkyyRose's rose gold aesthetic")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"\n[Agent]:\n{block.text}")


async def main():
    """Run all continuous conversation examples."""
    try:
        # Interactive marketing conversation
        await interactive_conversation()

        # Multi-turn analysis
        await multi_turn_analysis()

        # Collaborative creative workflow
        await collaborative_workflow()

        print("\n" + "=" * 60)
        print("✅ All conversation examples completed!")
        print("=" * 60)
        print("\n💡 Key Takeaway: The agent remembers all context within a session,")
        print("   enabling natural, iterative conversations.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
