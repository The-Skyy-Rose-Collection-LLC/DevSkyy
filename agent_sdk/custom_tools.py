"""
Custom MCP Tools for DevSkyy Agent SDK

Integrates existing DevSkyy capabilities as MCP tools for the Agent SDK.
Uses Approach A (Direct Import) for simple, low-latency integration.
"""

import json
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

# Message Queue imports (Approach B)
from agent_sdk.task_queue import TaskPriority, get_task_queue
from agents.commerce_agent import CommerceAgent
from agents.operations_agent import OperationsAgent
from agents.support_agent import SupportAgent

# Direct imports from existing DevSkyy agents (Approach A)


@tool(
    "generate_3d_model",
    "Generate a 3D model from text description or image using Tripo3D (queued)",
    {
        "prompt": str,
        "image_url": str,  # Optional, will be None if not provided
        "style": str,  # Optional: realistic, cartoon, low-poly
        "wait_for_completion": bool,  # NEW: async vs sync mode
    },
)
async def generate_3d_model(args: dict[str, Any]) -> dict[str, Any]:
    """
    Generate 3D models using message queue (Approach B).

    Enqueues task to Redis, workers process in background.
    Supports both async (return task_id) and sync (wait for result) modes.
    """
    try:
        prompt = args.get("prompt", "")
        image_url = args.get("image_url")
        style = args.get("style", "realistic")
        wait = args.get("wait_for_completion", True)

        # Get queue instance
        queue = get_task_queue()
        await queue.connect()

        # Enqueue task
        task_id = await queue.enqueue(
            task_type="generate_3d",
            task_data={"prompt": prompt, "image_url": image_url, "style": style},
            priority=TaskPriority.HIGH,  # 3D is high priority
            timeout=300,  # 5 minutes
        )

        # Async mode - return immediately
        if not wait:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""3D Generation Task Queued

Task ID: {task_id}
Status: Processing in background

Use check_task_status tool to poll for completion.""",
                    }
                ]
            }

        # Sync mode - wait for result
        result = await queue.get_result(task_id, timeout=300)

        if result.get("status") == "completed":
            model_data = result.get("result", {})
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""3D Model Generated Successfully!

Model Path: {model_data.get("model_path")}
Task ID: {task_id}
Style: {style}
Collection: {model_data.get("metadata", {}).get("collection", "N/A")}

The model is ready for download or integration.""",
                    }
                ]
            }
        elif result.get("status") == "timeout":
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""Task Still Processing

Task ID: {task_id}

The 3D generation is taking longer than expected.
Use check_task_status to poll for completion.""",
                    }
                ]
            }
        else:
            return {
                "content": [
                    {"type": "text", "text": f"Error: {result.get('error', 'Unknown error')}"}
                ],
                "is_error": True,
            }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error queueing 3D generation: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "virtual_tryon",
    "Virtual try-on for garments (STUB - not yet integrated)",
    {
        "model_image": str,
        "garment_image": str,
        "category": str,
        "wait_for_completion": bool,
    },
)
async def virtual_tryon(args: dict[str, Any]) -> dict[str, Any]:
    """
    Virtual try-on using message queue (Approach B - STUB).

    Infrastructure queues task, but worker returns stub result.
    Marked clearly as not yet implemented.
    """
    try:
        queue = get_task_queue()
        await queue.connect()

        task_id = await queue.enqueue(
            task_type="fashn_tryon",
            task_data={
                "model_image": args.get("model_image"),
                "garment_image": args.get("garment_image"),
                "category": args.get("category", "tops"),
            },
            priority=TaskPriority.NORMAL,
            timeout=120,
        )

        # Wait for stub result
        result = await queue.get_result(task_id, timeout=120)

        integration_steps = result.get("integration_steps", [])
        steps_text = "\n".join(integration_steps)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""⚠️  Virtual Try-On (STUB)

{result.get("message", "Not yet implemented")}

Task ID: {task_id}
Status: {result.get("status")}

Integration Steps:
{steps_text}""",
                }
            ],
            "is_error": result.get("stub", False),
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "is_error": True}


@tool(
    "check_task_status",
    "Check the status of a queued task by task_id",
    {
        "task_id": str,
    },
)
async def check_task_status(args: dict[str, Any]) -> dict[str, Any]:
    """Check status of background task."""
    try:
        task_id = args.get("task_id", "")
        if not task_id:
            raise ValueError("task_id is required")

        queue = get_task_queue()
        await queue.connect()

        status = await queue.get_task_status(task_id)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Task Status: {task_id}

Status: {status.get("status", "unknown")}
Created: {status.get("created_at", "N/A")}
Priority: {status.get("priority", "N/A")}

{json.dumps(status, indent=2)}""",
                }
            ]
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "is_error": True}


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
    """Manage WooCommerce products via direct agent integration."""
    try:
        action = args.get("action", "list")
        product_data = args.get("product_data", {})
        product_id = args.get("product_id")

        # Direct instantiation and call to CommerceAgent
        agent = CommerceAgent()

        # Build prompt based on action
        if action == "create":
            prompt = f"Create a new WooCommerce product with the following data: {product_data}"
        elif action == "update":
            if not product_id:
                raise ValueError("product_id required for update action")
            prompt = f"Update WooCommerce product {product_id} with: {product_data}"
        elif action == "get":
            if not product_id:
                raise ValueError("product_id required for get action")
            prompt = f"Get details for WooCommerce product {product_id}"
        elif action == "list":
            filters = product_data
            prompt = f"List WooCommerce products with filters: {filters}"
        else:
            raise ValueError(f"Unknown action: {action}")

        # Execute via agent
        result = await agent.execute(prompt)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Product {action.title()} Operation Completed

Status: {result.status.value}
Agent: {result.agent_name}

Result:
{result.content}""",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error managing product: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "analyze_data",
    "Analyze business data and generate insights (STUB - HTTP API not ready)",
    {
        "data_source": str,  # Type of data: sales, traffic, customers
        "time_range": str,  # e.g., "last_7_days", "last_month"
        "metrics": list,  # List of metrics to analyze
    },
)
async def analyze_data(args: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze business data (Approach C - HTTP API STUB).

    Future: Separate analytics microservice at analytics-service:8001
    Current: Returns placeholder
    """
    return {
        "content": [
            {
                "type": "text",
                "text": f"""Analytics Data Analysis (STUB)

NOTE: HTTP API microservice not yet implemented.
Future: POST http://analytics-service:8001/api/v1/analytics/analyze

Request would be:
{json.dumps(args, indent=2)}

For now, placeholder result returned.""",
            }
        ]
    }


@tool(
    "create_marketing_content",
    "Generate marketing content (STUB - HTTP API not ready)",
    {
        "content_type": str,  # social, email, blog
        "topic": str,
        "tone": str,  # professional, casual, friendly
        "length": str,  # short, medium, long
    },
)
async def create_marketing_content(args: dict[str, Any]) -> dict[str, Any]:
    """
    Generate marketing content (Approach C - HTTP API STUB).

    Future: Separate marketing microservice at marketing-service:8002
    Current: Returns placeholder
    """
    return {
        "content": [
            {
                "type": "text",
                "text": f"""Marketing Content Creation (STUB)

NOTE: HTTP API microservice not yet implemented.
Future: POST http://marketing-service:8002/api/v1/marketing/content

Request would be:
{json.dumps(args, indent=2)}

For now, placeholder result returned.""",
            }
        ]
    }


@tool(
    "handle_support_ticket",
    "Process customer support tickets and inquiries",
    {
        "ticket_id": str,
        "action": str,  # create, update, resolve, escalate
        "message": str,
        "priority": str,  # low, medium, high, urgent
    },
)
async def handle_support_ticket(args: dict[str, Any]) -> dict[str, Any]:
    """Handle customer support operations via direct agent integration."""
    try:
        ticket_id = args.get("ticket_id", "")
        action = args.get("action", "create")
        message = args.get("message", "")
        priority = args.get("priority", "medium")

        # Direct instantiation and call to SupportAgent
        agent = SupportAgent()

        # Build comprehensive prompt
        if action == "create":
            prompt = f"Create support ticket: {message} (Priority: {priority})"
        elif action == "update":
            prompt = f"Update ticket {ticket_id}: {message}"
        elif action == "resolve":
            prompt = f"Resolve ticket {ticket_id} with message: {message}"
        elif action == "escalate":
            prompt = f"Escalate ticket {ticket_id} to priority {priority}: {message}"
        else:
            prompt = f"Handle support ticket {action}: {message}"

        # Execute via agent
        result = await agent.execute(prompt)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Support Ticket {action.title()} Completed

Ticket ID: {ticket_id or "New"}
Priority: {priority}
Status: {result.status.value}

Response:
{result.content}""",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error handling ticket: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "execute_deployment",
    "Deploy WordPress themes, plugins, or updates",
    {
        "deployment_type": str,  # theme, plugin, update
        "target": str,  # Name of theme/plugin
        "environment": str,  # staging, production
        "rollback_on_error": bool,
    },
)
async def execute_deployment(args: dict[str, Any]) -> dict[str, Any]:
    """Execute deployment operations via direct agent integration."""
    try:
        deployment_type = args.get("deployment_type", "theme")
        target = args.get("target", "")
        environment = args.get("environment", "staging")
        rollback_on_error = args.get("rollback_on_error", True)

        # Direct instantiation and call to OperationsAgent
        agent = OperationsAgent()

        # Build comprehensive prompt
        prompt = f"""Deploy {deployment_type} to {environment} environment
Target: {target}
Rollback on error: {rollback_on_error}"""

        # Execute via agent
        result = await agent.execute(prompt)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Deployment Executed

Type: {deployment_type}
Target: {target}
Environment: {environment}
Status: {result.status.value}

Deployment Result:
{result.content}""",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error executing deployment: {str(e)}"}],
            "is_error": True,
        }


def create_devskyy_tools():
    """
    Create and return configured MCP server with all DevSkyy tools.

    Hybrid Integration:
    - Approach A (Direct): manage_product, handle_support_ticket, execute_deployment
    - Approach B (Queue): generate_3d_model, virtual_tryon, check_task_status
    - Approach C (HTTP Stubs): analyze_data, create_marketing_content

    Returns:
        McpSdkServerConfig: Configured MCP server for use with ClaudeAgentOptions
    """
    return create_sdk_mcp_server(
        name="devskyy",
        version="1.0.0",
        tools=[
            # Approach A: Direct Import (UNCHANGED)
            manage_product,
            handle_support_ticket,
            execute_deployment,
            # Approach B: Message Queue
            generate_3d_model,  # Full implementation
            virtual_tryon,  # Stub implementation
            check_task_status,  # Utility tool
            # Approach C: HTTP API (Stubs)
            analyze_data,
            create_marketing_content,
        ],
    )
