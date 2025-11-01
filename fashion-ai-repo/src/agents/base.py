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
        """
        Initialize the BaseAgent with identity, storage path, queue manager, and retry/time settings.
        
        Parameters:
            name: Agent name used for identification and log file naming.
            io_path: Filesystem path for agent input/output; the directory will be created if it does not exist.
            queue_manager: QueueManager used to publish and consume messages for this agent.
            retry_attempts: Maximum number of attempts to retry a failing task.
            timeout: Per-task timeout in seconds.
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
        """
        Process a single task identified by task_type using the provided payload and return the processing result.
        
        Parameters:
            task_type (str): Identifier of the task to execute.
            payload (Dict[str, Any]): Input data required to perform the task.
        
        Returns:
            Dict[str, Any]: Result of task processing containing outcome details or response data.
        """
        pass

    @abstractmethod
    def get_supported_tasks(self) -> List[str]:
        """
        List the task type identifiers that this agent can handle.
        
        Returns:
            A list of supported task type strings.
        """
        pass

    async def execute_with_retry(
        self, task_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task with retry logic and return its result.
        
        Attempts to run the specified task by calling process_task up to self.retry_attempts times, waiting with exponential backoff between retries when failures occur.
        
        Parameters:
            task_type (str): Identifier for the task to execute.
            payload (Dict[str, Any]): Data passed to the task.
        
        Returns:
            Dict[str, Any]: The result produced by the successful task execution.
        
        Raises:
            Exception: Re-raises the exception from the final failed attempt if the task keeps failing.
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
        """
        Send a task message to another agent via the queue manager.
        
        Parameters:
            target_agent (str): Name of the recipient agent.
            task_type (str): Type of task being requested.
            payload (Dict[str, Any]): Data to deliver with the message.
        
        Returns:
            True if the message was published successfully, False otherwise.
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
        """
        Mark the agent as running and log that it has started.
        """
        self.running = True
        self.logger.info(f"Agent {self.name} started")

    def stop(self) -> None:
        """
        Set the agent to a stopped state and record the stop event in the agent log.
        """
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