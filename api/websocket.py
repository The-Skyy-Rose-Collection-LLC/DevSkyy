"""WebSocket server for real-time dashboard updates.

This module provides WebSocket endpoints for real-time communication
between the backend and frontend dashboard:
- Agent status updates
- Round Table competition progress
- Task execution updates
- 3D pipeline progress
- System metrics

Replaces HTTP polling with <100ms real-time updates.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

logger = logging.getLogger(__name__)

# Create WebSocket router
ws_router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections across multiple channels.

    Channels:
    - agents: Agent status and execution updates
    - round_table: LLM Round Table competition progress
    - tasks: Task execution status
    - 3d_pipeline: 3D asset generation progress
    - metrics: System performance metrics
    """

    def __init__(self) -> None:
        """Initialize connection manager with empty connection pools."""
        self.active_connections: dict[str, set[WebSocket]] = {
            "agents": set(),
            "round_table": set(),
            "tasks": set(),
            "3d_pipeline": set(),
            "metrics": set(),
        }
        self._message_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._broadcast_task: asyncio.Task[None] | None = None

    async def connect(self, websocket: WebSocket, channel: str) -> bool:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
            channel: Channel name (agents, round_table, tasks, etc.)

        Returns:
            True if connection accepted, False if invalid channel
        """
        if channel not in self.active_connections:
            logger.warning(f"Attempted connection to invalid channel: {channel}")
            return False

        await websocket.accept()
        self.active_connections[channel].add(websocket)
        logger.info(
            f"WebSocket connected to {channel} channel "
            f"(total: {len(self.active_connections[channel])})"
        )
        return True

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            channel: Channel name
        """
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            logger.info(
                f"WebSocket disconnected from {channel} channel "
                f"(remaining: {len(self.active_connections[channel])})"
            )

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Broadcast message to all connections in a channel.

        Automatically removes dead connections during broadcast.

        Args:
            channel: Channel to broadcast to
            message: Message dictionary to send (will be JSON-encoded)
        """
        if channel not in self.active_connections:
            logger.warning(f"Attempted broadcast to invalid channel: {channel}")
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        dead_connections = set()
        message_json = json.dumps(message)

        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(message_json)
            except WebSocketDisconnect:
                dead_connections.add(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to {channel}: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        if dead_connections:
            self.active_connections[channel] -= dead_connections
            logger.info(f"Removed {len(dead_connections)} dead connections from {channel}")

    async def broadcast_to_all(self, message: dict[str, Any]) -> None:
        """Broadcast message to all channels.

        Args:
            message: Message to broadcast
        """
        for channel in self.active_connections:
            await self.broadcast(channel, message)

    def get_connection_count(self, channel: str | None = None) -> int:
        """Get number of active connections.

        Args:
            channel: Optional channel to count (None = total across all channels)

        Returns:
            Number of active connections
        """
        if channel:
            return len(self.active_connections.get(channel, set()))
        return sum(len(conns) for conns in self.active_connections.values())

    def get_stats(self) -> dict[str, int]:
        """Get connection statistics.

        Returns:
            Dictionary mapping channel names to connection counts
        """
        return {
            channel: len(connections) for channel, connections in self.active_connections.items()
        }


# Global connection manager instance
manager = ConnectionManager()


@ws_router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    """WebSocket endpoint for real-time updates.

    Args:
        websocket: FastAPI WebSocket connection
        channel: Channel name (agents, round_table, tasks, 3d_pipeline, metrics)

    Raises:
        WebSocketDisconnect: When client disconnects
    """
    # Validate and connect
    if not await manager.connect(websocket, channel):
        await websocket.close(code=4004, reason=f"Invalid channel: {channel}")
        return

    try:
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client (ping/pong, subscriptions, etc.)
                data = await websocket.receive_text()

                # Handle client messages (optional)
                try:
                    client_message = json.loads(data)
                    message_type = client_message.get("type")

                    if message_type == "ping":
                        # Respond to ping with pong
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.now().isoformat()}
                        )
                    elif message_type == "subscribe":
                        # Handle subscription updates (future enhancement)
                        logger.info(f"Client subscription update: {client_message}")
                    else:
                        logger.debug(f"Unhandled message type: {message_type}")

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {data}")

            except TimeoutError:
                # Send periodic keepalive
                await websocket.send_json(
                    {
                        "type": "keepalive",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error on {channel}: {e}")
        manager.disconnect(websocket, channel)


# =============================================================================
# Convenience Functions for Broadcasting Updates
# =============================================================================


async def broadcast_agent_update(
    agent_id: str, status: str, data: dict[str, Any] | None = None
) -> None:
    """Broadcast agent status update.

    Args:
        agent_id: Agent identifier
        status: Agent status (running, completed, failed, etc.)
        data: Optional additional data
    """
    message = {
        "type": "agent_status_update",
        "agent_id": agent_id,
        "status": status,
        "data": data or {},
    }
    await manager.broadcast("agents", message)


async def broadcast_round_table_update(
    competition_id: str,
    stage: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Broadcast Round Table competition update.

    Args:
        competition_id: Competition identifier
        stage: Competition stage (generating, scoring, ab_testing, completed)
        data: Optional stage-specific data
    """
    message = {
        "type": "competition_update",
        "competition_id": competition_id,
        "stage": stage,
        "data": data or {},
    }
    await manager.broadcast("round_table", message)


async def broadcast_task_update(
    task_id: str,
    status: str,
    progress: float | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Broadcast task execution update.

    Args:
        task_id: Task identifier
        status: Task status
        progress: Optional progress percentage (0-100)
        data: Optional additional data
    """
    message = {
        "type": "task_update",
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "data": data or {},
    }
    await manager.broadcast("tasks", message)


async def broadcast_3d_pipeline_update(
    pipeline_id: str,
    stage: str,
    progress: float | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Broadcast 3D pipeline progress update.

    Args:
        pipeline_id: Pipeline identifier
        stage: Pipeline stage (generating, validating, uploading, completed)
        progress: Optional progress percentage (0-100)
        data: Optional stage-specific data
    """
    message = {
        "type": "pipeline_update",
        "pipeline_id": pipeline_id,
        "stage": stage,
        "progress": progress,
        "data": data or {},
    }
    await manager.broadcast("3d_pipeline", message)


async def broadcast_metrics_update(metrics: dict[str, Any]) -> None:
    """Broadcast system metrics update.

    Args:
        metrics: System metrics dictionary
    """
    message = {
        "type": "metrics_update",
        "metrics": metrics,
    }
    await manager.broadcast("metrics", message)


async def broadcast_error(channel: str, error: str, error_type: str = "error") -> None:
    """Broadcast error message to a channel.

    Args:
        channel: Channel to broadcast to
        error: Error message
        error_type: Error type (error, warning, info)
    """
    message = {
        "type": "error",
        "error_type": error_type,
        "message": error,
    }
    await manager.broadcast(channel, message)
