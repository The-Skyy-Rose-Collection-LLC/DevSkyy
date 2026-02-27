"""WordPress Bridge Agent API — SSE streaming endpoint + webhook dispatch.

Provides:
- POST /api/v1/agent/execute — Run agent with SSE streaming
- POST /api/v1/agent/webhooks/dispatch — Process incoming WooCommerce webhooks
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from agents.wordpress_bridge.agent import WordPressBridgeAgent, run_agent
from agents.wordpress_bridge.prompts import PROCESS_ORDER_PROMPT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["wordpress-agent"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class AgentExecuteRequest(BaseModel):
    """Request body for agent execution."""

    intent: str = Field(
        ..., description="Operation intent (e.g., sync_collection, health_check)"
    )
    prompt: str = Field(
        ..., min_length=1, description="Natural language instruction for the agent"
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (collection, source, etc.)",
    )


class WebhookDispatchRequest(BaseModel):
    """Request body for WooCommerce webhook dispatch."""

    topic: str = Field(
        ..., description="Webhook topic (e.g., order.created, order.updated)"
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Raw webhook payload from WooCommerce"
    )


# ---------------------------------------------------------------------------
# SSE Streaming Endpoint
# ---------------------------------------------------------------------------


@router.post("/execute")
async def execute_agent(request: AgentExecuteRequest):
    """Execute WordPress Bridge Agent with SSE streaming.

    Returns a Server-Sent Events stream with agent progress.
    Each event is a JSON object with type, content, and optional metadata.
    Stream ends with data: [DONE]
    """

    async def event_stream():
        try:
            async for event in run_agent(
                prompt=request.prompt,
                correlation_id=request.context.get("correlation_id"),
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            logger.exception("Agent execution failed")
            error_event = {"type": "error", "content": "Agent execution failed"}
            yield f"data: {json.dumps(error_event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Webhook Dispatch Endpoint
# ---------------------------------------------------------------------------


@router.post("/webhooks/dispatch")
async def dispatch_webhook(request: WebhookDispatchRequest):
    """Process incoming WooCommerce webhook by dispatching to agent.

    Formats the webhook payload as a structured prompt and runs the agent.
    Returns the agent's response (non-streaming for webhooks).
    """
    # Format webhook as agent prompt based on topic
    topic = request.topic
    payload = request.payload

    if topic.startswith("order."):
        order_id = payload.get("id", "unknown")
        order_total = payload.get("total", "0.00")
        items = payload.get("line_items", [])
        item_summary = ", ".join(
            f"{item.get('quantity', 1)}x {item.get('name', 'Unknown')}"
            for item in items[:5]  # Limit to first 5 items
        )
        prompt = PROCESS_ORDER_PROMPT.format(
            order_id=order_id,
            order_summary=f"Total: ${order_total}. Items: {item_summary}",
        )
    elif topic.startswith("product."):
        product_id = payload.get("id", "unknown")
        product_name = payload.get("name", "Unknown Product")
        prompt = (
            f"Product updated on WooCommerce: {product_name} (ID: {product_id}). "
            "Review and sync if needed."
        )
    else:
        prompt = (
            f"Received webhook '{topic}'. "
            f"Payload summary: {json.dumps(payload)[:500]}"
        )

    try:
        agent = WordPressBridgeAgent()
        result = await agent.execute(prompt)
        return {
            "status": "processed",
            "topic": topic,
            "result": result.get("result", ""),
            "session_id": result.get("session_id"),
        }
    except Exception as e:
        logger.exception("Webhook processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
