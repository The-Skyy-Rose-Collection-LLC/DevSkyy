"""Base agent class with common functionality."""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.logging import AgentLogger
from src.core.queue import Message, QueueManager


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        name: str,
        io_path: Path,
        queue_manager: QueueManager,
        retry_attempts: int = 3,
        timeout: int = 60,
    ):
        """Initialize base agent.

        Args:
            name: Agent name
            io_path: Input/output path for agent data
            queue_manager: Queue manager instance
            retry_attempts: Number of retry attempts for failed tasks
            timeout: Task timeout in seconds
        """
        self.name = name
        self.io_path = Path(io_path)
        self.queue_manager = queue_manager
        self.retry_attempts = retry_attempts
        self.timeout = timeout
        self.logger = AgentLogger(name, log_file=Path(f"logs/agent_{name.lower()}.log"))
        self.running = False

        # Ensure IO path exists
        self.io_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def process_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task.

        Args:
            task_type: Type of task to process
            payload: Task payload

        Returns:
            Result dictionary
        """
        pass

    @abstractmethod
    def get_supported_tasks(self) -> List[str]:
        """Get list of supported task types.

        Returns:
            List of task type strings
        """
        pass

    async def execute_with_retry(
        self, task_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute task with retry logic.

        Args:
            task_type: Type of task
            payload: Task payload

        Returns:
            Result dictionary
        """
        for attempt in range(self.retry_attempts):
            try:
                self.logger.info(
                    f"Executing task: {task_type} (attempt {attempt + 1}/{self.retry_attempts})"
                )
                result = await self.process_task(task_type, payload)
                self.logger.info(f"Task completed successfully: {task_type}")
                return result
            except Exception as e:
                self.logger.error(f"Task failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.retry_attempts - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        raise RuntimeError(f"Task failed after {self.retry_attempts} attempts")

    def send_message(
        self, target_agent: str, task_type: str, payload: Dict[str, Any]
    ) -> bool:
        """Send message to another agent.

        Args:
            target_agent: Target agent name
            task_type: Task type
            payload: Message payload

        Returns:
            True if successful
        """
        message = Message(
            source_agent=self.name,
            target_agent=target_agent,
            task_type=task_type,
            payload=payload,
        )
        channel = f"{self.name.lower()}_to_{target_agent.lower()}"
        success = self.queue_manager.publish(channel, message)

        if success:
            self.logger.info(f"Sent message to {target_agent}: {task_type}")
        else:
            self.logger.error(f"Failed to send message to {target_agent}")

        return success

    def start(self) -> None:
        """Start the agent."""
        self.running = True
        self.logger.info(f"Agent {self.name} started")

    def stop(self) -> None:
        """Stop the agent."""
        self.running = False
        self.logger.info(f"Agent {self.name} stopped")

    async def run(self) -> None:
        """Main agent loop."""
        self.start()
        queue_name = self.name.lower()

        try:
            while self.running:
                message = self.queue_manager.pop_task(queue_name, timeout=5)
                if message:
                    try:
                        result = await self.execute_with_retry(
                            message.task_type, message.payload
                        )
                        self.logger.info(f"Task result: {result}")
                    except Exception as e:
                        self.logger.error(f"Failed to process task: {str(e)}")
        finally:
            self.stop()
