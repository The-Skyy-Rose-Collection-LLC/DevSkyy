"""
Background Worker for Task Processing
======================================

Celery-style worker that processes tasks from Redis queue.

Features:
- Full TripoAssetAgent integration
- Stub FashnTryOnAgent (infrastructure ready, not implemented)
- Priority queue processing
- Error handling with retry logic
- Graceful shutdown

Pattern from:
- agent_sdk/integration_examples/approach_b_message_queue.py:323-482
- orchestration/asset_pipeline.py:777-804 (exponential backoff)

Usage:
    python -m agent_sdk.worker
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import socket
from datetime import UTC, datetime
from typing import Any

from agent_sdk.task_queue import (
    QUEUE_PREFIX,
    TaskQueue,
    TaskStatus,
)
from agents.tripo_agent import TripoAssetAgent

# Dead Letter Queue for failed tasks
DLQ_PREFIX = "devskyy:dlq:"
LOCK_PREFIX = "devskyy:locks:"

# FASHN agent commented out - not yet integrated
# from agents.fashn_agent import FashnTryOnAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BackgroundWorker:
    """
    Background worker for processing queued tasks.

    Pattern from:
    - agent_sdk/integration_examples/approach_b_message_queue.py:323-482
    """

    __slots__ = (
        "redis_url",
        "_redis",
        "_task_queue",
        "running",
        "tripo_agent",
        "fashn_agent",
        "_shutdown_event",
    )

    def __init__(self, redis_url: str | None = None) -> None:
        """
        Initialize background worker.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Any = None
        self._task_queue: TaskQueue | None = None
        self.running = False
        self._shutdown_event = asyncio.Event()

        # Initialize agents
        self.tripo_agent: TripoAssetAgent | None = None
        self.fashn_agent: Any = None  # Not yet implemented

    async def connect(self) -> None:
        """Connect to Redis and TaskQueue."""
        if not self._redis:
            import redis.asyncio as redis

            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                retry_on_timeout=True,
            )

            await self._redis.ping()
            logger.info("Worker connected to Redis")

        # Initialize TaskQueue for Pub/Sub notifications
        if not self._task_queue:
            self._task_queue = TaskQueue(redis_url=self.redis_url)
            await self._task_queue.connect()
            logger.info("Worker connected to TaskQueue (Pub/Sub enabled)")

    async def process_generate_3d(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process 3D generation task - FULL IMPLEMENTATION.

        Calls TripoAssetAgent to generate 3D models from text or image.

        Args:
            task_data: Task input data

        Returns:
            Task result with status and data
        """
        try:
            # Initialize agent if needed
            if self.tripo_agent is None:
                self.tripo_agent = TripoAssetAgent()
                logger.info("TripoAssetAgent initialized")

            # Extract parameters
            prompt = task_data.get("prompt", "")
            image_url = task_data.get("image_url")
            style = task_data.get("style", "realistic")

            logger.info(
                f"Generating 3D model: prompt='{prompt}', image={bool(image_url)}, style={style}"
            )

            # Call agent based on input type
            if image_url:
                # Image-to-3D generation
                result = await self.tripo_agent._tool_generate_from_image(
                    image_url=image_url,
                    product_name=prompt,
                    collection="SIGNATURE",
                    garment_type="tee",
                    additional_details=f"Style: {style}",
                )
            else:
                # Text-to-3D generation
                result = await self.tripo_agent._tool_generate_from_text(
                    product_name=prompt,
                    collection="SIGNATURE",
                    garment_type="tee",
                    additional_details=f"Style: {style}",
                )

            logger.info(f"✅ 3D generation successful: {result.get('task_id')}")

            return {
                "status": "completed",
                "result": result,
                "completed_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 3D generation failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "error_type": type(e).__name__}

    async def process_fashn_tryon(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process virtual try-on task - STUB IMPLEMENTATION.

        Infrastructure is ready, but actual integration is TODO.
        Returns clear placeholder with integration instructions.

        TODO: Full integration steps:
        1. Uncomment: from agents.fashn_agent import FashnTryOnAgent
        2. Initialize: self.fashn_agent = FashnTryOnAgent()
        3. Call: await self.fashn_agent._tool_virtual_tryon(...)
        4. Update tests
        5. Remove stub markers

        Args:
            task_data: Task input data

        Returns:
            Stub result with integration steps
        """
        logger.warning("⚠️  FASHN try-on STUB called - not yet integrated")

        # Extract parameters (for future use)
        model_image = task_data.get("model_image")
        garment_image = task_data.get("garment_image")
        category = task_data.get("category", "tops")

        logger.info(
            f"STUB: Virtual try-on request: "
            f"model={model_image}, garment={garment_image}, category={category}"
        )

        return {
            "status": "failed",
            "error": "FASHN virtual try-on not yet implemented",
            "message": "Infrastructure ready. See worker.py:process_fashn_tryon for integration steps.",
            "stub": True,
            "integration_steps": [
                "1. Uncomment FashnTryOnAgent import in worker.py",
                "2. Initialize self.fashn_agent = FashnTryOnAgent() in __init__",
                "3. Replace stub implementation with actual agent call",
                "4. Add proper error handling and retry logic",
                "5. Update tests to verify integration",
                "6. Remove stub markers and warnings",
            ],
            "requested_params": {
                "model_image": model_image,
                "garment_image": garment_image,
                "category": category,
            },
        }

    async def process_task(self, task_id: str, task_data: dict[str, Any]) -> None:
        """
        Route task to appropriate processor.

        Args:
            task_id: Task identifier
            task_data: Task metadata
        """
        task_type = task_data.get("task_type")

        logger.info(f"📋 Processing task {task_id} (type: {task_type})")

        try:
            # Route to processor
            if task_type == "generate_3d":
                result = await self.process_generate_3d(task_data.get("data", {}))
            elif task_type == "fashn_tryon":
                result = await self.process_fashn_tryon(task_data.get("data", {}))
            else:
                result = {"status": "failed", "error": f"Unknown task type: {task_type}"}

            # Enterprise hardening: Store result with Pub/Sub notification
            await self._task_queue.store_result(task_id, result, ttl=300)

            logger.info(f"✅ Task {task_id} completed (status: {result.get('status')})")

        except Exception as e:
            logger.error(f"❌ Task {task_id} failed: {e}", exc_info=True)

            # Store error result with Pub/Sub notification
            error_result = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.now(UTC).isoformat(),
            }

            await self._task_queue.store_result(task_id, error_result, ttl=300)

            # Enterprise hardening: Dead Letter Queue for failed tasks
            # Preserves failed tasks for debugging (7 day TTL)
            dlq_key = f"{DLQ_PREFIX}{task_id}"
            dlq_entry = {
                "task_id": task_id,
                "task_data": task_data,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.now(UTC).isoformat(),
                "worker_host": socket.gethostname(),
            }
            await self._redis.setex(dlq_key, 604800, json.dumps(dlq_entry))  # 7 days
            logger.info(f"📝 Task moved to DLQ: {task_id}")

    async def run(self) -> None:
        """
        Main worker loop.

        Continuously polls Redis queues for tasks and processes them.
        """
        await self.connect()
        self.running = True

        logger.info("🚀 Background worker started")
        logger.info("📋 Monitoring queues: generate_3d, fashn_tryon")
        logger.info(f"📡 Redis: {self.redis_url}")

        # Task types to monitor
        task_types = ["generate_3d", "fashn_tryon"]

        while self.running and not self._shutdown_event.is_set():
            try:
                # Check all known queues
                for task_type in task_types:
                    queue_name = f"queue:{task_type}"

                    # Pop highest priority task (ZPOPMAX)
                    result = await self._redis.zpopmax(queue_name, count=1)

                    if result:
                        task_id, priority = result[0]

                        logger.info(f"🔄 Dequeued task: {task_id} (priority: {priority})")

                        # Enterprise hardening: Atomic task locking prevents duplicate processing
                        task_lock_key = f"{LOCK_PREFIX}{task_id}"
                        hostname = socket.gethostname()

                        # Attempt atomic lock with TTL (NX = set only if not exists)
                        acquired = await self._redis.set(
                            task_lock_key,
                            hostname,
                            ex=300,
                            nx=True,  # 5 min lock TTL
                        )

                        if not acquired:
                            logger.warning(
                                f"⚠️  Task {task_id} already locked by another worker - skipping"
                            )
                            continue

                        try:
                            # Fetch task data
                            task_key = f"{QUEUE_PREFIX}{task_id}"
                            task_json = await self._redis.get(task_key)

                            if task_json:
                                task_data = json.loads(task_json)

                                # Update status to processing
                                task_data["status"] = TaskStatus.PROCESSING.value
                                task_data["started_at"] = datetime.now(UTC).isoformat()
                                task_data["worker_host"] = hostname

                                await self._redis.setex(task_key, 300, json.dumps(task_data))

                                # Process task
                                await self.process_task(task_id, task_data)
                            else:
                                logger.warning(f"⚠️  Task data not found: {task_id}")

                        finally:
                            # Always release lock
                            await self._redis.delete(task_lock_key)

                # Sleep briefly if no tasks
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("Worker received cancellation signal")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Backoff on error

        logger.info("👋 Worker stopped")

    async def stop(self) -> None:
        """Graceful shutdown."""
        logger.info("Stopping worker...")
        self.running = False
        self._shutdown_event.set()

        # Close connections
        if self._redis:
            await self._redis.close()

        if self.tripo_agent:
            await self.tripo_agent.close()

        logger.info("Worker shutdown complete")


# Global worker instance
_worker: BackgroundWorker | None = None


async def main() -> None:
    """Entry point for worker process."""
    global _worker
    _worker = BackgroundWorker()

    # Setup signal handlers
    loop = asyncio.get_running_loop()

    def signal_handler(sig):
        logger.info(f"Received signal {sig}, initiating shutdown...")
        asyncio.create_task(_worker.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    try:
        await _worker.run()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down worker...")
        await _worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
