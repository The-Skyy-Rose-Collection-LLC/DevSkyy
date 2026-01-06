"""WebSocket Integration Layer for Agent Execution.

This module provides integration between agent execution, task tracking,
and WebSocket real-time updates to the dashboard.

It acts as a middleware layer that:
1. Wraps agent execution with WebSocket broadcasts
2. Updates task status with real-time notifications
3. Broadcasts Round Table competition progress
4. Monitors 3D pipeline stages
5. Emits real-time metrics

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .websocket import (
    broadcast_3d_pipeline_update,
    broadcast_agent_update,
    broadcast_error,
    broadcast_metrics_update,
    broadcast_round_table_update,
    broadcast_task_update,
)

logger = logging.getLogger(__name__)


class WebSocketIntegration:
    """
    Integration layer between backend services and WebSocket broadcasting.

    Provides helper methods to broadcast updates during:
    - Agent execution lifecycle
    - Task processing
    - Round Table competitions
    - 3D asset generation
    - System metrics collection
    """

    @staticmethod
    async def broadcast_agent_execution_start(
        agent_id: str,
        agent_type: str,
        task_id: str,
        prompt: str,
    ) -> None:
        """Broadcast when agent execution starts."""
        try:
            await broadcast_agent_update(
                agent_id=agent_id,
                status="running",
                data={
                    "agent_type": agent_type,
                    "task_id": task_id,
                    "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "started_at": datetime.now(UTC).isoformat(),
                },
            )

            await broadcast_task_update(
                task_id=task_id,
                status="running",
                progress=0.0,
                data={
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                },
            )

            logger.debug(f"Broadcast agent start: {agent_id} (task: {task_id})")

        except Exception as e:
            logger.error(f"Failed to broadcast agent start: {e}")

    @staticmethod
    async def broadcast_agent_execution_complete(
        agent_id: str,
        agent_type: str,
        task_id: str,
        result: Any,
        duration_ms: float,
        technique_used: str | None = None,
    ) -> None:
        """Broadcast when agent execution completes."""
        try:
            await broadcast_agent_update(
                agent_id=agent_id,
                status="completed",
                data={
                    "agent_type": agent_type,
                    "task_id": task_id,
                    "duration_ms": duration_ms,
                    "technique_used": technique_used,
                    "completed_at": datetime.now(UTC).isoformat(),
                },
            )

            await broadcast_task_update(
                task_id=task_id,
                status="completed",
                progress=100.0,
                data={
                    "agent_id": agent_id,
                    "result_preview": str(result)[:200] if result else None,
                    "duration_ms": duration_ms,
                },
            )

            logger.debug(f"Broadcast agent complete: {agent_id} (task: {task_id})")

        except Exception as e:
            logger.error(f"Failed to broadcast agent complete: {e}")

    @staticmethod
    async def broadcast_agent_execution_error(
        agent_id: str,
        agent_type: str,
        task_id: str,
        error: str,
    ) -> None:
        """Broadcast when agent execution fails."""
        try:
            await broadcast_agent_update(
                agent_id=agent_id,
                status="error",
                data={
                    "agent_type": agent_type,
                    "task_id": task_id,
                    "error": error,
                    "failed_at": datetime.now(UTC).isoformat(),
                },
            )

            await broadcast_task_update(
                task_id=task_id,
                status="failed",
                data={
                    "agent_id": agent_id,
                    "error": error,
                },
            )

            await broadcast_error(
                channel="agents",
                error=f"Agent {agent_id} failed: {error}",
                error_type="error",
            )

            logger.debug(f"Broadcast agent error: {agent_id} (task: {task_id})")

        except Exception as e:
            logger.error(f"Failed to broadcast agent error: {e}")

    @staticmethod
    async def broadcast_round_table_start(
        competition_id: str,
        prompt: str,
        providers: list[str],
    ) -> None:
        """Broadcast when Round Table competition starts."""
        try:
            await broadcast_round_table_update(
                competition_id=competition_id,
                stage="generating",
                data={
                    "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "providers": providers,
                    "provider_count": len(providers),
                    "started_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.debug(f"Broadcast Round Table start: {competition_id}")

        except Exception as e:
            logger.error(f"Failed to broadcast Round Table start: {e}")

    @staticmethod
    async def broadcast_round_table_scoring(
        competition_id: str,
        entries_count: int,
    ) -> None:
        """Broadcast when Round Table enters scoring phase."""
        try:
            await broadcast_round_table_update(
                competition_id=competition_id,
                stage="scoring",
                data={
                    "entries_count": entries_count,
                    "scoring_started_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.debug(f"Broadcast Round Table scoring: {competition_id}")

        except Exception as e:
            logger.error(f"Failed to broadcast Round Table scoring: {e}")

    @staticmethod
    async def broadcast_round_table_ab_testing(
        competition_id: str,
        finalist_a: str,
        finalist_b: str,
    ) -> None:
        """Broadcast when Round Table enters A/B testing phase."""
        try:
            await broadcast_round_table_update(
                competition_id=competition_id,
                stage="ab_testing",
                data={
                    "finalist_a": finalist_a,
                    "finalist_b": finalist_b,
                    "ab_testing_started_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.debug(f"Broadcast Round Table A/B test: {competition_id}")

        except Exception as e:
            logger.error(f"Failed to broadcast Round Table A/B test: {e}")

    @staticmethod
    async def broadcast_round_table_complete(
        competition_id: str,
        winner: str,
        winner_score: float,
        total_duration_ms: float,
    ) -> None:
        """Broadcast when Round Table competition completes."""
        try:
            await broadcast_round_table_update(
                competition_id=competition_id,
                stage="completed",
                data={
                    "winner": winner,
                    "winner_score": winner_score,
                    "total_duration_ms": total_duration_ms,
                    "completed_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.debug(f"Broadcast Round Table complete: {competition_id} (winner: {winner})")

        except Exception as e:
            logger.error(f"Failed to broadcast Round Table complete: {e}")

    @staticmethod
    async def broadcast_3d_generation_start(
        pipeline_id: str,
        prompt: str,
        format: str,
    ) -> None:
        """Broadcast when 3D generation starts."""
        try:
            await broadcast_3d_pipeline_update(
                pipeline_id=pipeline_id,
                stage="generating",
                progress=0.0,
                data={
                    "prompt": prompt,
                    "format": format,
                    "started_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.debug(f"Broadcast 3D generation start: {pipeline_id}")

        except Exception as e:
            logger.error(f"Failed to broadcast 3D generation start: {e}")

    @staticmethod
    async def broadcast_3d_generation_progress(
        pipeline_id: str,
        stage: str,
        progress: float,
        message: str | None = None,
    ) -> None:
        """Broadcast 3D generation progress update."""
        try:
            await broadcast_3d_pipeline_update(
                pipeline_id=pipeline_id,
                stage=stage,
                progress=progress,
                data={
                    "message": message,
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.debug(f"Broadcast 3D generation progress: {pipeline_id} ({stage}: {progress}%)")

        except Exception as e:
            logger.error(f"Failed to broadcast 3D generation progress: {e}")

    @staticmethod
    async def broadcast_3d_generation_complete(
        pipeline_id: str,
        model_url: str,
        preview_url: str | None,
        format: str,
        size_mb: float,
    ) -> None:
        """Broadcast when 3D generation completes."""
        try:
            await broadcast_3d_pipeline_update(
                pipeline_id=pipeline_id,
                stage="completed",
                progress=100.0,
                data={
                    "model_url": model_url,
                    "preview_url": preview_url,
                    "format": format,
                    "size_mb": size_mb,
                    "completed_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.debug(f"Broadcast 3D generation complete: {pipeline_id}")

        except Exception as e:
            logger.error(f"Failed to broadcast 3D generation complete: {e}")

    @staticmethod
    async def broadcast_3d_generation_error(
        pipeline_id: str,
        error: str,
    ) -> None:
        """Broadcast when 3D generation fails."""
        try:
            await broadcast_3d_pipeline_update(
                pipeline_id=pipeline_id,
                stage="failed",
                data={
                    "error": error,
                    "failed_at": datetime.now(UTC).isoformat(),
                },
            )

            await broadcast_error(
                channel="3d_pipeline",
                error=f"3D generation {pipeline_id} failed: {error}",
                error_type="error",
            )

            logger.debug(f"Broadcast 3D generation error: {pipeline_id}")

        except Exception as e:
            logger.error(f"Failed to broadcast 3D generation error: {e}")

    @staticmethod
    async def broadcast_system_metrics(
        metrics: dict[str, Any],
    ) -> None:
        """Broadcast system metrics update."""
        try:
            await broadcast_metrics_update(metrics)
            logger.debug("Broadcast system metrics update")

        except Exception as e:
            logger.error(f"Failed to broadcast system metrics: {e}")

    @staticmethod
    async def start_metrics_broadcaster(interval_seconds: int = 5) -> None:
        """Start background task to broadcast metrics periodically."""

        async def metrics_loop():
            while True:
                try:
                    # Collect current metrics
                    # TODO: Integrate with security/prometheus_exporter.py
                    metrics = {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "cpu_percent": 45.2,  # Placeholder
                        "memory_percent": 62.8,  # Placeholder
                        "active_connections": 12,  # Placeholder
                        "requests_per_second": 45.5,  # Placeholder
                        "avg_latency_ms": 125.3,  # Placeholder
                    }

                    await WebSocketIntegration.broadcast_system_metrics(metrics)

                except Exception as e:
                    logger.error(f"Metrics broadcast loop error: {e}")

                await asyncio.sleep(interval_seconds)

        # Start the background task
        asyncio.create_task(metrics_loop())
        logger.info(f"Started metrics broadcaster (interval: {interval_seconds}s)")


def wrap_agent_execution(
    agent_id: str,
    agent_type: str,
    task_id: str,
) -> Callable:
    """
    Decorator to wrap agent execution with WebSocket broadcasts.

    Usage:
        @wrap_agent_execution("commerce-001", "commerce", "task-123")
        async def execute():
            return await agent.execute_smart(prompt)
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Extract prompt if available
            prompt = kwargs.get("prompt", args[0] if args else "")

            # Broadcast start
            await WebSocketIntegration.broadcast_agent_execution_start(
                agent_id=agent_id,
                agent_type=agent_type,
                task_id=task_id,
                prompt=str(prompt),
            )

            start_time = asyncio.get_event_loop().time()

            try:
                # Execute the actual function
                result = await func(*args, **kwargs)

                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000

                # Extract technique if available
                technique = None
                if isinstance(result, dict):
                    technique = result.get("technique_used") or result.get("technique")

                # Broadcast success
                await WebSocketIntegration.broadcast_agent_execution_complete(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    task_id=task_id,
                    result=result,
                    duration_ms=duration_ms,
                    technique_used=technique,
                )

                return result

            except Exception as e:
                # Broadcast error
                await WebSocketIntegration.broadcast_agent_execution_error(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    task_id=task_id,
                    error=str(e),
                )
                raise

        return wrapper

    return decorator


# Export convenience functions
__all__ = [
    "WebSocketIntegration",
    "wrap_agent_execution",
]
