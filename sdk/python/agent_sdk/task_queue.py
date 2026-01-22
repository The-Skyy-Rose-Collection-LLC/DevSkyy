"""
Task Queue Infrastructure
==========================

Redis-backed message queue with priority support for background job processing.

Features:
- Priority queuing with Redis sorted sets
- Task metadata storage with TTL
- Result polling with timeout
- Task status tracking
- Pattern from: agent_sdk/integration_examples/approach_b_message_queue.py
- Connection pattern from: core/redis_cache.py

Usage:
    queue = get_task_queue()
    await queue.connect()

    # Enqueue task
    task_id = await queue.enqueue(
        task_type="generate_3d",
        task_data={"prompt": "ring"},
        priority=TaskPriority.HIGH,
        timeout=300
    )

    # Poll for result
    result = await queue.get_result(task_id, timeout=300)
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Queue configuration
QUEUE_PREFIX = "devskyy:tasks:"
RESULT_PREFIX = "devskyy:results:"
TASK_TIMEOUT = 300  # 5 minutes default

# Pub/Sub channels (Enterprise hardening: Zero-overhead result delivery)
RESULT_CHANNEL = "devskyy:results:channel"


class TaskStatus(str, Enum):
    """Task processing status."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskPriority(int, Enum):
    """Task priority levels (higher number = higher priority)."""

    CRITICAL = 10  # Immediate processing
    HIGH = 7  # 3D generation, critical business
    NORMAL = 5  # Standard operations
    LOW = 3  # Background tasks
    BACKGROUND = 1  # Lowest priority


class TaskQueue:
    """
    Async Redis-backed task queue with priority support.

    Uses Redis sorted sets for priority queuing (ZADD/ZPOPMAX pattern).
    Stores task metadata with TTL for automatic cleanup.

    Pattern from:
    - agent_sdk/integration_examples/approach_b_message_queue.py:60-126
    - core/redis_cache.py:80-100 (connection pattern)
    """

    __slots__ = ("redis_url", "_redis", "_connected", "_metrics", "_health_check_task")

    def __init__(self, redis_url: str | None = None) -> None:
        """
        Initialize task queue.

        Args:
            redis_url: Redis connection URL (default: from env or localhost)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Any = None
        self._connected = False
        self._health_check_task: Any = None
        self._metrics = {
            "tasks_queued": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_timeout": 0,
        }

    async def connect(self) -> bool:
        """
        Connect to Redis with automatic retry.

        Returns:
            True if connected successfully, False otherwise
        """
        if self._connected:
            return True

        try:
            import redis.asyncio as redis

            # Create Redis client from URL with connection pooling
            # Enterprise hardening: Connection pool prevents exhaustion under load
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
                max_connections=50,  # Limit concurrent connections
                health_check_interval=30,  # Auto health check every 30s
            )

            # Test connection
            await self._redis.ping()
            self._connected = True

            # Start periodic health check
            if not self._health_check_task or self._health_check_task.done():
                self._health_check_task = asyncio.create_task(self._periodic_health_check())

            logger.info(
                f"Task queue connected to Redis: "
                f"{self.redis_url.split('@')[-1] if '@' in self.redis_url else 'localhost'}"
            )
            return True

        except ImportError:
            logger.error("redis package not installed - task queue unavailable")
            return False
        except Exception as e:
            logger.error(f"Task queue connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        # Stop health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._health_check_task

        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Task queue disconnected")

    async def _periodic_health_check(self) -> None:
        """
        Periodic health check to detect connection failures early.

        Enterprise hardening: Proactive health monitoring prevents silent failures.
        Auto-reconnects on failure to maintain availability.
        """
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                if self._redis and self._connected:
                    try:
                        await asyncio.wait_for(self._redis.ping(), timeout=5.0)
                        logger.debug("Redis health check: OK")
                    except TimeoutError:
                        logger.warning("Redis health check timeout - reconnecting...")
                        self._connected = False
                        await self.connect()
                    except Exception as e:
                        logger.error(f"Redis health check failed: {e} - reconnecting...")
                        self._connected = False
                        await self.connect()

            except asyncio.CancelledError:
                logger.info("Health check task cancelled")
                break
            except Exception as e:
                logger.error(f"Health check error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Brief pause before retry

    async def enqueue(
        self,
        task_type: str,
        task_data: dict[str, Any],
        priority: int = TaskPriority.NORMAL,
        timeout: int = 300,
    ) -> str:
        """
        Enqueue task to Redis sorted set.

        Args:
            task_type: Type of task (e.g., "generate_3d", "fashn_tryon")
            task_data: Task input data
            priority: Task priority (higher = processed first)
            timeout: Task timeout in seconds

        Returns:
            task_id: Unique task identifier

        Pattern from: agent_sdk/integration_examples/approach_b_message_queue.py:60-106
        """
        await self.connect()

        if not self._connected:
            raise RuntimeError("Task queue not connected to Redis")

        # Generate unique task ID
        timestamp = datetime.now(UTC).timestamp()
        task_id = f"{task_type}:{timestamp}"

        # Create task metadata
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "data": task_data,
            "status": TaskStatus.QUEUED.value,
            "created_at": datetime.now(UTC).isoformat(),
            "priority": priority,
            "timeout": timeout,
        }

        # Store task metadata with TTL
        task_key = f"{QUEUE_PREFIX}{task_id}"
        await self._redis.setex(task_key, timeout, json.dumps(task))

        # Add to priority queue (sorted set)
        queue_name = f"queue:{task_type}"
        await self._redis.zadd(queue_name, {task_id: priority})

        self._metrics["tasks_queued"] += 1

        logger.info(f"Task queued: {task_id} (type: {task_type}, priority: {priority})")

        return task_id

    async def get_result(self, task_id: str, timeout: int = 30) -> dict[str, Any]:
        """
        Poll for task result with timeout.

        Args:
            task_id: Task identifier
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Task result or timeout error

        Pattern from: agent_sdk/integration_examples/approach_b_message_queue.py:108-120
        """
        await self.connect()

        if not self._connected:
            return {"status": TaskStatus.FAILED.value, "error": "Task queue not connected"}

        result_key = f"{RESULT_PREFIX}{task_id}"
        end_time = datetime.now(UTC) + timedelta(seconds=timeout)

        # Poll for result
        while datetime.now(UTC) < end_time:
            result = await self._redis.get(result_key)
            if result:
                result_data = json.loads(result)

                # Update metrics
                if result_data.get("status") == "completed":
                    self._metrics["tasks_completed"] += 1
                elif result_data.get("status") == "failed":
                    self._metrics["tasks_failed"] += 1

                return result_data

            await asyncio.sleep(1)

        # Timeout
        self._metrics["tasks_timeout"] += 1
        logger.warning(f"Task timeout: {task_id}")

        return {
            "status": TaskStatus.TIMEOUT.value,
            "error": "Timeout waiting for result",
            "task_id": task_id,
        }

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Get current task status.

        Args:
            task_id: Task identifier

        Returns:
            Task metadata or not_found status
        """
        await self.connect()

        if not self._connected:
            return {"status": "error", "error": "Task queue not connected"}

        task_key = f"{QUEUE_PREFIX}{task_id}"
        task_data = await self._redis.get(task_key)

        if task_data:
            return json.loads(task_data)

        # Check result (task might be completed)
        result_key = f"{RESULT_PREFIX}{task_id}"
        result_data = await self._redis.get(result_key)

        if result_data:
            return json.loads(result_data)

        return {"status": "not_found", "error": f"Task {task_id} not found (may have expired)"}

    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """
        Update task status.

        Args:
            task_id: Task identifier
            status: New status

        Returns:
            True if updated successfully
        """
        await self.connect()

        if not self._connected:
            return False

        task_key = f"{QUEUE_PREFIX}{task_id}"
        task_data = await self._redis.get(task_key)

        if not task_data:
            return False

        task = json.loads(task_data)
        task["status"] = status.value
        task["updated_at"] = datetime.now(UTC).isoformat()

        # Update with remaining TTL
        ttl = await self._redis.ttl(task_key)
        if ttl > 0:
            await self._redis.setex(task_key, ttl, json.dumps(task))
            return True

        return False

    async def store_result(self, task_id: str, result: dict[str, Any], ttl: int = 300) -> bool:
        """
        Store task result and notify via Pub/Sub.

        Enterprise hardening: Pub/Sub notification enables zero-overhead result delivery.

        Args:
            task_id: Task identifier
            result: Task result data
            ttl: Result TTL in seconds

        Returns:
            True if stored successfully
        """
        await self.connect()

        if not self._connected:
            return False

        result_key = f"{RESULT_PREFIX}{task_id}"
        await self._redis.setex(result_key, ttl, json.dumps(result))

        # Pub/Sub notification (zero overhead for waiting clients)
        await self.publish_result(task_id, result)

        logger.info(f"Task result stored: {task_id} (status: {result.get('status')})")
        return True

    async def publish_result(self, task_id: str, result: dict[str, Any]) -> None:
        """
        Publish result notification via Pub/Sub.

        Args:
            task_id: Task identifier
            result: Task result data
        """
        await self.connect()

        if not self._connected:
            return

        # Publish task completion to channel
        message = {"task_id": task_id, "status": result.get("status")}
        await self._redis.publish(RESULT_CHANNEL, json.dumps(message))

    async def get_result_pubsub(self, task_id: str, timeout: int = 30) -> dict[str, Any]:
        """
        Wait for task result via Pub/Sub (zero overhead).

        Enterprise hardening: Replaces polling with Pub/Sub for instant notification.
        Falls back to direct fetch if message not received (handles restarts).

        Args:
            task_id: Task identifier
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Task result or timeout error
        """
        await self.connect()

        if not self._connected:
            return {"status": TaskStatus.FAILED.value, "error": "Task queue not connected"}

        # Subscribe to result channel
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(RESULT_CHANNEL)

        try:
            # Check if result already exists (completed before subscription)
            result_key = f"{RESULT_PREFIX}{task_id}"
            existing_result = await self._redis.get(result_key)
            if existing_result:
                result_data = json.loads(existing_result)
                # Update metrics
                if result_data.get("status") == "completed":
                    self._metrics["tasks_completed"] += 1
                elif result_data.get("status") == "failed":
                    self._metrics["tasks_failed"] += 1
                return result_data

            # Wait for Pub/Sub notification
            end_time = datetime.now(UTC) + timedelta(seconds=timeout)

            while datetime.now(UTC) < end_time:
                try:
                    # Check for message with short timeout
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True), timeout=1.0
                    )

                    if message and message["type"] == "message":
                        data = json.loads(message["data"])

                        # Check if this is our task
                        if data.get("task_id") == task_id:
                            # Fetch full result
                            result_json = await self._redis.get(result_key)
                            if result_json:
                                result_data = json.loads(result_json)

                                # Update metrics
                                if result_data.get("status") == "completed":
                                    self._metrics["tasks_completed"] += 1
                                elif result_data.get("status") == "failed":
                                    self._metrics["tasks_failed"] += 1

                                return result_data

                except TimeoutError:
                    # No message yet, continue waiting
                    continue

            # Timeout
            self._metrics["tasks_timeout"] += 1
            logger.warning(f"Task timeout: {task_id}")

            return {
                "status": TaskStatus.TIMEOUT.value,
                "error": "Timeout waiting for result",
                "task_id": task_id,
            }

        finally:
            await pubsub.unsubscribe(RESULT_CHANNEL)
            await pubsub.close()

    async def get_queue_length(self, task_type: str) -> int:
        """
        Get number of pending tasks in queue.

        Args:
            task_type: Type of tasks to count

        Returns:
            Number of pending tasks
        """
        await self.connect()

        if not self._connected:
            return 0

        queue_name = f"queue:{task_type}"
        return await self._redis.zcard(queue_name)

    def get_metrics(self) -> dict[str, int]:
        """Get queue metrics."""
        return self._metrics.copy()


# Global singleton instance
_task_queue: TaskQueue | None = None


def get_task_queue() -> TaskQueue:
    """
    Get global task queue instance.

    Returns:
        Singleton TaskQueue instance
    """
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
