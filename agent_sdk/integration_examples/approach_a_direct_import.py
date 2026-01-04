"""
Approach A: Direct Import and Async Call

PROS:
✅ Simplest implementation
✅ Lowest latency - no network or queue overhead
✅ Easy debugging - direct stack traces
✅ Type safety - IDE autocomplete and type checking
✅ Transaction consistency - all or nothing

CONS:
❌ Tight coupling - changes to tripo_agent affect this code
❌ Single process - can't scale horizontally easily
❌ Blocking - long operations block the agent
❌ Resource sharing - competes for CPU/memory with agent
❌ Deployment coupling - must deploy together

BEST FOR:
- Small to medium workloads
- Development and testing
- When low latency is critical
- Single-server deployments
"""

from typing import Any

from claude_agent_sdk import tool

from agents.analytics_agent import AnalyticsAgent
from agents.commerce_agent import CommerceAgent

# Direct imports from existing DevSkyy agents
from agents.tripo_agent import Tripo3DAgent


@tool(
    "generate_3d_model",
    "Generate a 3D model from text description or image using Tripo3D",
    {
        "prompt": str,
        "image_url": str,  # Optional
        "style": str,  # Optional: realistic, cartoon, low-poly
    },
)
async def generate_3d_model(args: dict[str, Any]) -> dict[str, Any]:
    """
    Direct integration with Tripo3DAgent.

    Flow:
    1. Instantiate Tripo3DAgent
    2. Call its generate method directly
    3. Handle errors and return formatted response
    """
    try:
        prompt = args.get("prompt", "")
        image_url = args.get("image_url")
        style = args.get("style", "realistic")

        # Direct instantiation and call
        agent = Tripo3DAgent()

        if image_url:
            # Generate from image
            result = await agent.generate_from_image(
                image_url=image_url, prompt=prompt, style=style
            )
        else:
            # Generate from text
            result = await agent.generate_from_text(prompt=prompt, style=style)

        # Extract relevant data from agent's response
        model_url = result.get("model_url")
        task_id = result.get("task_id")
        status = result.get("status")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""3D Model Generated Successfully!

Model URL: {model_url}
Task ID: {task_id}
Status: {status}
Style: {style}

The model has been generated and is ready for download or integration.""",
                }
            ]
        }

    except Exception as e:
        # Detailed error handling
        error_type = type(e).__name__
        error_msg = str(e)

        return {
            "content": [
                {"type": "text", "text": f"Error generating 3D model: {error_type} - {error_msg}"}
            ],
            "is_error": True,
        }


@tool(
    "manage_product",
    "Create, update, or retrieve WooCommerce products",
    {
        "action": str,  # create, update, get, list
        "product_data": dict,  # Product details
        "product_id": int,  # Optional, for update/get
    },
)
async def manage_product(args: dict[str, Any]) -> dict[str, Any]:
    """
    Direct integration with CommerceAgent.

    Assumes CommerceAgent has methods like:
    - create_product(product_data)
    - update_product(product_id, product_data)
    - get_product(product_id)
    - list_products(filters)
    """
    try:
        action = args.get("action", "list")
        product_data = args.get("product_data", {})
        product_id = args.get("product_id")

        # Direct instantiation
        agent = CommerceAgent()

        # Route to appropriate method based on action
        if action == "create":
            result = await agent.create_product(product_data)
            product_id = result.get("id")
            product_name = result.get("name")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Product created successfully!\n\nID: {product_id}\nName: {product_name}\nURL: {result.get('permalink')}",
                    }
                ]
            }

        elif action == "update":
            if not product_id:
                raise ValueError("product_id required for update action")

            result = await agent.update_product(product_id, product_data)

            return {
                "content": [{"type": "text", "text": f"Product {product_id} updated successfully!"}]
            }

        elif action == "get":
            if not product_id:
                raise ValueError("product_id required for get action")

            result = await agent.get_product(product_id)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Product Details:\n\nName: {result.get('name')}\nPrice: ${result.get('price')}\nStock: {result.get('stock_quantity')}\nStatus: {result.get('status')}",
                    }
                ]
            }

        elif action == "list":
            filters = product_data  # Use product_data as filters for list
            result = await agent.list_products(filters)

            products = result.get("products", [])
            product_summary = "\n".join(
                [
                    f"- {p.get('name')} (${p.get('price')}) - ID: {p.get('id')}"
                    for p in products[:10]  # Limit to 10
                ]
            )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Found {len(products)} products:\n\n{product_summary}",
                    }
                ]
            }

        else:
            raise ValueError(f"Unknown action: {action}")

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error managing product: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "analyze_data",
    "Analyze business data and generate insights",
    {
        "data_source": str,  # sales, traffic, customers
        "time_range": str,  # last_7_days, last_month, etc.
        "metrics": list,  # List of metrics to analyze
    },
)
async def analyze_data(args: dict[str, Any]) -> dict[str, Any]:
    """
    Direct integration with AnalyticsAgent.

    The agent does the heavy lifting of:
    - Connecting to data sources
    - Running queries
    - Computing statistics
    - Generating insights
    """
    try:
        data_source = args.get("data_source", "sales")
        time_range = args.get("time_range", "last_7_days")
        metrics = args.get("metrics", [])

        # Direct call to analytics agent
        agent = AnalyticsAgent()

        result = await agent.analyze(source=data_source, time_range=time_range, metrics=metrics)

        # Format the analysis results
        summary = result.get("summary", "")
        key_metrics = result.get("metrics", {})
        insights = result.get("insights", [])
        recommendations = result.get("recommendations", [])

        metrics_text = "\n".join([f"- {k}: {v}" for k, v in key_metrics.items()])

        insights_text = "\n".join([f"• {insight}" for insight in insights])

        recommendations_text = "\n".join([f"→ {rec}" for rec in recommendations])

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Data Analysis Complete

📊 Summary:
{summary}

📈 Key Metrics:
{metrics_text}

💡 Insights:
{insights_text}

🎯 Recommendations:
{recommendations_text}""",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error analyzing data: {str(e)}"}],
            "is_error": True,
        }


# Example: How to use these tools in the SDK
if __name__ == "__main__":

    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, create_sdk_mcp_server

    async def demo():
        """Demonstrate direct import approach."""

        # Create MCP server with directly integrated tools
        server = create_sdk_mcp_server(
            name="devskyy_direct",
            version="1.0.0",
            tools=[
                generate_3d_model,
                manage_product,
                analyze_data,
            ],
        )

        # Configure agent with the server
        options = ClaudeAgentOptions(
            mcp_servers={"devskyy": server},
            allowed_tools=[
                "mcp__devskyy__generate_3d_model",
                "mcp__devskyy__manage_product",
                "mcp__devskyy__analyze_data",
            ],
            permission_mode="acceptEdits",
        )

        # Use the agent
        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                "Generate a 3D engagement ring model and create a WooCommerce product for it"
            )

            async for message in client.receive_response():
                print(message)

    # asyncio.run(demo())
    print("✅ Approach A: Direct Import - Example complete")
    print("\nTo test, ensure agents/ module is importable and run:")
    print("  python agent_sdk/integration_examples/approach_a_direct_import.py")
