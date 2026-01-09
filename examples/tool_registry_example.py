"""
Tool Registry Example
=====================

Demonstrates the complete Tool Registry pattern with governance features.

Features demonstrated:
1. Tool registration with specs
2. Agent using tools via use_tool() method
3. Rate limiting enforcement
4. Permission checking
5. Export to multiple formats
"""

import asyncio

from adk.base import AgentConfig
from agents.commerce_agent import CommerceAgent
from core.runtime.tool_registry import (
    ToolCallContext,
    ToolCategory,
    ToolSeverity,
    get_tool_registry,
)
from tools.commerce_tools import register_commerce_tools


async def main():
    """Run tool registry examples."""

    print("=" * 80)
    print("Tool Registry Example - Full Governance Pattern")
    print("=" * 80)

    # Step 1: Get the global registry
    print("\n1. Getting global ToolRegistry instance...")
    registry = get_tool_registry()
    print(f"   Registry created: {registry}")

    # Step 2: Register commerce tools
    print("\n2. Registering commerce tools...")
    register_commerce_tools(registry)
    print(f"   Registered {len(registry._tools)} tools:")
    for name, spec in registry._tools.items():
        print(
            f"   - {name}: {spec.category.value} | {spec.severity.value} | "
            f"rate_limit={spec.rate_limit}/min"
        )

    # Step 3: Create agent with tool registry
    print("\n3. Creating CommerceAgent with ToolRegistry...")
    config = AgentConfig(
        name="commerce_demo",
        model="gpt-4o-mini",
        temperature=0.3,
    )
    agent = CommerceAgent(config)
    agent._correlation_id = "demo-001"
    agent._permissions = {"commerce:write", "products:create", "pricing:update"}
    print(f"   Agent created with permissions: {agent._permissions}")

    # Step 4: Use tool through agent
    print("\n4. Creating product via agent.use_tool()...")
    try:
        result = await agent.use_tool(
            "commerce_create_product",
            {
                "name": "Heart aRose Bomber Jacket",
                "price": 299.99,
                "description": "Premium bomber with rose gold accents",
                "collection": "BLACK_ROSE",
                "sizes": ["S", "M", "L", "XL"],
            },
            user_id="demo_user",
        )
        print(f"   Product created: {result}")
    except Exception as e:
        print(f"   Error: {e}")

    # Step 5: Demonstrate rate limiting
    print("\n5. Testing rate limiting (5 rapid calls to rate-limited tool)...")
    for i in range(5):
        try:
            result = await agent.use_tool(
                "commerce_update_pricing",
                {"product_id": 123, "regular_price": 199.99 + i},
                user_id="demo_user",
            )
            print(f"   Call {i + 1}: SUCCESS - {result}")
        except RuntimeError as e:
            print(f"   Call {i + 1}: RATE LIMITED - {e}")

    # Step 6: Demonstrate permission checking
    print("\n6. Testing permission checking (missing permissions)...")
    agent_limited = CommerceAgent(config)
    agent_limited._correlation_id = "demo-002"
    agent_limited._permissions = {"commerce:read"}  # Missing write permissions
    try:
        await agent_limited.use_tool(
            "commerce_process_order",
            {"order_id": 789, "action": "fulfill", "notes": "Test"},
            user_id="limited_user",
        )
    except RuntimeError as e:
        print(f"   Permission denied: {e}")

    # Step 7: Export to multiple formats
    print("\n7. Exporting tools to multiple formats...")

    # OpenAI Functions
    openai_functions = registry.to_openai_functions()
    print(f"\n   OpenAI Functions format ({len(openai_functions)} tools):")
    print(f"   Sample: {openai_functions[0]['name']}")

    # Anthropic Tools
    anthropic_tools = registry.to_anthropic_tools()
    print(f"\n   Anthropic Tools format ({len(anthropic_tools)} tools):")
    print(f"   Sample: {anthropic_tools[0]['name']}")
    if "defer_loading" in anthropic_tools[0]:
        print(
            f"   - Advanced Tool Use enabled: defer_loading={anthropic_tools[0]['defer_loading']}"
        )

    # MCP Tools
    mcp_tools = registry.to_mcp_tools()
    print(f"\n   MCP Tools format ({len(mcp_tools)} tools):")
    print(f"   Sample: {mcp_tools[0]['name']}")
    if "annotations" in mcp_tools[0]:
        print(f"   - Annotations: {mcp_tools[0]['annotations']}")

    # Step 8: Get registry statistics
    print("\n8. Registry Statistics...")
    schema = registry.export_schema()
    print(f"   Total tools: {schema['total_tools']}")
    print(f"   Categories: {schema['categories']}")
    print(f"   Severities: {schema['severities']}")

    # Step 9: Direct execution via registry
    print("\n9. Direct execution via registry.execute()...")
    context = ToolCallContext(
        correlation_id="demo-003",
        agent_id="commerce",
        user_id="direct_user",
        permissions={"commerce:read", "inventory:read"},
    )
    result = await registry.execute("commerce_get_inventory", {"product_id": 123}, context)
    print(f"   Execution result: success={result.success}, duration={result.duration_seconds:.3f}s")
    if result.success:
        print(f"   Inventory: {result.result}")

    # Step 10: Get tools by category and severity
    print("\n10. Filtering tools...")
    commerce_tools = registry.get_by_category(ToolCategory.COMMERCE)
    print(f"   Commerce tools: {len(commerce_tools)}")

    read_only_tools = registry.get_by_severity(ToolSeverity.READ_ONLY)
    print(f"   Read-only tools: {len(read_only_tools)}")
    for tool in read_only_tools:
        print(f"   - {tool.name}: cacheable={tool.cacheable}, rate_limit={tool.rate_limit}/min")

    print("\n" + "=" * 80)
    print("Tool Registry Example Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
