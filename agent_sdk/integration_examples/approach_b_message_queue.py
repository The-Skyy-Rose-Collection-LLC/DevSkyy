"""
Approach B: Message Queue (Redis + Background Workers)

PROS:
✅ Horizontal scaling - add more workers easily
✅ Non-blocking - agent doesn't wait for completion
✅ Fault tolerance - retry failed jobs automatically
✅ Load balancing - distribute work across workers
✅ Monitoring - track job status, failures, throughput
✅ Priority queues - important tasks first
✅ Decoupled - agent and workers can deploy independently

CONS:
❌ Added complexity - Redis, workers, monitoring
❌ Higher latency - network + queue overhead
❌ Eventual consistency - results not immediate
❌ Debugging harder - distributed traces needed
❌ Infrastructure cost - Redis server required
❌ State management - need to poll for results

BEST FOR:
- Large workloads (1000+ req/day)
- Long-running operations (>30 seconds)
- Production deployments
- Horizontal scaling requirements
- Background processing needs

ARCHITECTURE:
┌─────────┐      ┌───────┐      ┌────────┐      ┌────────────┐
│ Agent   │─────>│ Redis │─────>│ Worker │─────>│ Tripo3D    │
│ SDK     │      │ Queue │      │ Pool   │      │ Agent      │
└─────────┘      └───────┘      └────────┘      └────────────┘
    │                                                   │
    │                                                   │
    └───────────── Poll for results ───────────────────┘
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

from claude_agent_sdk import tool

# For production, use Celery. For this example, we'll show the pattern
# pip install celery redis aioredis

try:
    import redis.asyncio as redis
except ImportError:
    print("⚠️  Install redis: pip install redis aioredis")


# Configuration
REDIS_URL = "redis://localhost:6379/0"
QUEUE_PREFIX = "devskyy:tasks:"
RESULT_PREFIX = "devskyy:results:"
TASK_TIMEOUT = 300  # 5 minutes


class TaskQueue:
    """
    Async Redis-based task queue.

    In production, replace this with Celery or AWS SQS.
    """

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self._redis: redis.Redis | None = None

    async def connect(self):
        """Connect to Redis."""
        if not self._redis:
            self._redis = await redis.from_url(self.redis_url)

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()

    async def enqueue(self, task_type: str, task_data: dict[str, Any], priority: int = 0) -> str:
        """
        Enqueue a task.

        Args:
            task_type: Type of task (e.g., "generate_3d", "create_product")
            task_data: Task parameters
            priority: Higher number = higher priority

        Returns:
            task_id: Unique task identifier
        """
        await self.connect()

        # Generate unique task ID
        task_id = f"{task_type}:{datetime.utcnow().timestamp()}"

        # Create task payload
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "data": task_data,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "priority": priority,
        }

        # Store task metadata
        await self._redis.setex(f"{QUEUE_PREFIX}{task_id}", TASK_TIMEOUT, json.dumps(task))

        # Push to priority queue
        # Using sorted set for priority (higher score = higher priority)
        queue_name = f"queue:{task_type}"
        await self._redis.zadd(queue_name, {task_id: priority})

        return task_id

    async def get_result(self, task_id: str, timeout: int = 30) -> dict[str, Any]:
        """
        Poll for task result.

        Args:
            task_id: Task identifier
            timeout: Max seconds to wait

        Returns:
            Result data or error
        """
        await self.connect()

        result_key = f"{RESULT_PREFIX}{task_id}"
        end_time = datetime.utcnow() + timedelta(seconds=timeout)

        # Poll for result
        while datetime.utcnow() < end_time:
            result = await self._redis.get(result_key)

            if result:
                return json.loads(result)

            # Wait before next poll
            await asyncio.sleep(1)

        # Timeout
        return {"status": "timeout", "error": f"Task {task_id} did not complete within {timeout}s"}


# Initialize global queue
task_queue = TaskQueue()


@tool(
    "generate_3d_model",
    "Generate a 3D model from text description or image using Tripo3D",
    {
        "prompt": str,
        "image_url": str,
        "style": str,
        "wait_for_completion": bool,  # New: whether to wait or return task ID
    },
)
async def generate_3d_model(args: dict[str, Any]) -> dict[str, Any]:
    """
    Queue-based 3D generation.

    Flow:
    1. Enqueue task to Redis
    2. Return task ID immediately (async mode)
       OR wait for completion (sync mode)
    3. Background worker processes the task
    4. Result stored in Redis
    """
    try:
        prompt = args.get("prompt", "")
        image_url = args.get("image_url")
        style = args.get("style", "realistic")
        wait = args.get("wait_for_completion", True)

        # Enqueue the task
        task_id = await task_queue.enqueue(
            task_type="generate_3d",
            task_data={"prompt": prompt, "image_url": image_url, "style": style},
            priority=5,  # Medium priority
        )

        if not wait:
            # Async mode - return immediately with task ID
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""3D Generation Task Queued

Task ID: {task_id}
Status: Processing in background

The task has been queued and will be processed by available workers.
Use the task ID to check status later.""",
                    }
                ]
            }

        # Sync mode - wait for completion
        result = await task_queue.get_result(task_id, timeout=120)

        if result.get("status") == "success":
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""3D Model Generated Successfully!

Model URL: {result.get('model_url')}
Task ID: {task_id}
Processing Time: {result.get('duration_ms')}ms

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
Check status later using the task ID.""",
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
    "check_task_status",
    "Check the status of a queued task",
    {
        "task_id": str,
    },
)
async def check_task_status(args: dict[str, Any]) -> dict[str, Any]:
    """
    Check status of a queued task.

    This is important for async workflows where tasks return immediately.
    """
    try:
        task_id = args.get("task_id", "")

        if not task_id:
            raise ValueError("task_id is required")

        result = await task_queue.get_result(task_id, timeout=1)

        status = result.get("status", "unknown")

        status_messages = {
            "pending": "⏳ Task is queued and waiting for a worker",
            "processing": "🔄 Task is currently being processed",
            "success": "✅ Task completed successfully",
            "failed": "❌ Task failed",
            "timeout": "⏱️ Task status unknown (may still be processing)",
        }

        message = status_messages.get(status, "❓ Unknown status")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Task Status: {task_id}

{message}

Details:
{json.dumps(result, indent=2)}""",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error checking task status: {str(e)}"}],
            "is_error": True,
        }


# ============================================================================
# Background Worker (runs separately from the agent)
# ============================================================================


class BackgroundWorker:
    """
    Background worker that processes queued tasks.

    In production:
    - Run multiple workers for horizontal scaling
    - Use Celery for robust task management
    - Add retry logic and dead letter queues
    - Implement health checks and monitoring
    """

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self._redis: redis.Redis | None = None
        self.running = False

    async def connect(self):
        """Connect to Redis."""
        if not self._redis:
            self._redis = await redis.from_url(self.redis_url)

    async def process_task(self, task_id: str, task_data: dict[str, Any]):
        """
        Process a single task.

        This is where you call the actual agent logic.
        """
        task_type = task_data.get("task_type")

        try:
            if task_type == "generate_3d":
                # Import here to avoid circular dependencies
                from agents.tripo_agent import Tripo3DAgent

                agent = Tripo3DAgent()
                data = task_data.get("data", {})

                # Do the actual work
                if data.get("image_url"):
                    result = await agent.generate_from_image(
                        image_url=data["image_url"],
                        prompt=data.get("prompt", ""),
                        style=data.get("style", "realistic"),
                    )
                else:
                    result = await agent.generate_from_text(
                        prompt=data.get("prompt", ""), style=data.get("style", "realistic")
                    )

                # Store successful result
                result_data = {
                    "status": "success",
                    "task_id": task_id,
                    "model_url": result.get("model_url"),
                    "duration_ms": result.get("duration_ms"),
                    "completed_at": datetime.utcnow().isoformat(),
                }

            elif task_type == "create_product":
                from agents.commerce_agent import CommerceAgent

                agent = CommerceAgent()
                data = task_data.get("data", {})

                result = await agent.create_product(data.get("product_data", {}))

                result_data = {
                    "status": "success",
                    "task_id": task_id,
                    "product_id": result.get("id"),
                    "product_url": result.get("permalink"),
                    "completed_at": datetime.utcnow().isoformat(),
                }

            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Store result
            result_key = f"{RESULT_PREFIX}{task_id}"
            await self._redis.setex(result_key, TASK_TIMEOUT, json.dumps(result_data))

        except Exception as e:
            # Store error result
            error_data = {
                "status": "failed",
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "completed_at": datetime.utcnow().isoformat(),
            }

            result_key = f"{RESULT_PREFIX}{task_id}"
            await self._redis.setex(result_key, TASK_TIMEOUT, json.dumps(error_data))

    async def run(self):
        """
        Main worker loop.

        Continuously polls queues for new tasks.
        """
        await self.connect()
        self.running = True

        print("🔄 Background worker started")

        while self.running:
            try:
                # Check all known queues (in production, use BLPOP for efficiency)
                for task_type in ["generate_3d", "create_product", "analyze_data"]:
                    queue_name = f"queue:{task_type}"

                    # Pop highest priority task
                    result = await self._redis.zpopmax(queue_name, count=1)

                    if result:
                        task_id, priority = result[0]

                        # Fetch task data
                        task_key = f"{QUEUE_PREFIX}{task_id}"
                        task_json = await self._redis.get(task_key)

                        if task_json:
                            task_data = json.loads(task_json)
                            print(f"📋 Processing task: {task_id}")

                            # Update status to processing
                            task_data["status"] = "processing"
                            await self._redis.setex(task_key, TASK_TIMEOUT, json.dumps(task_data))

                            # Process the task
                            await self.process_task(task_id, task_data)

                            print(f"✅ Completed task: {task_id}")

                # Sleep if no tasks found
                await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Worker error: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        if self._redis:
            await self._redis.close()


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        # Run as background worker
        async def run_worker():
            worker = BackgroundWorker()
            try:
                await worker.run()
            except KeyboardInterrupt:
                print("\n👋 Shutting down worker...")
                await worker.stop()

        asyncio.run(run_worker())

    else:
        # Run as example client
        print("✅ Approach B: Message Queue - Example complete")
        print("\nTo test:")
        print("  1. Start Redis: redis-server")
        print("  2. Start worker: python approach_b_message_queue.py worker")
        print("  3. Run client: python approach_b_message_queue.py")
        print("\nOr use Celery in production:")
        print("  celery -A tasks worker --loglevel=info")
