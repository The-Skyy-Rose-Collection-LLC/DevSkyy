"""Message queue management using Redis."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

import redis
from pydantic import BaseModel


class Message(BaseModel):
    """Message schema for agent communication."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: str
    target_agent: str
    task_type: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    priority: Optional[str] = None
    retry_count: int = 0
    correlation_id: Optional[str] = None


class QueueManager:
    """Redis-based queue manager for agent communication."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "fashion_ai",
    ):
        """Initialize queue manager.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            prefix: Queue prefix for namespacing
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        self.prefix = prefix
        self.pubsub = self.redis_client.pubsub()

    def publish(self, channel: str, message: Message) -> bool:
        """
        Publish a Message to the specified logical Redis channel within the manager's namespace.
        
        Parameters:
            channel (str): Logical channel name (without the manager prefix).
            message (Message): Message object to publish.
        
        Returns:
            True if the message was published successfully, False otherwise.
        """
        try:
            channel_name = f"{self.prefix}:{channel}"
            message_json = message.model_dump_json()
            self.redis_client.publish(channel_name, message_json)
            return True
        except Exception as e:
            print(f"Error publishing message: {e}")
            return False

    def subscribe(self, channels: list[str]) -> None:
        """
        Subscribe to the given Redis channels under this manager's namespace prefix.
        
        Parameters:
            channels (list[str]): Channel names (without the manager prefix) to subscribe to.
        """
        channel_names = [f"{self.prefix}:{ch}" for ch in channels]
        self.pubsub.subscribe(*channel_names)

    def listen(self) -> Optional[Message]:
        """
        Waits for the next message on currently subscribed channels.
        
        Returns:
            Message parsed from the channel payload when a new message is received; `None` if no message arrives within the internal timeout or an error occurs.
        """
        try:
            message = self.pubsub.get_message(timeout=1.0)
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                return Message(**data)
            return None
        except Exception as e:
            print(f"Error listening for message: {e}")
            return None

    def push_task(self, queue: str, message: Message) -> bool:
        """
        Append a Message to the named namespaced queue.
        
        Parameters:
            queue (str): Logical queue name (without prefix).
            message (Message): Message object to enqueue.
        
        Returns:
            bool: `True` if the message was successfully enqueued, `False` otherwise.
        """
        try:
            queue_name = f"{self.prefix}:queue:{queue}"
            message_json = message.model_dump_json()
            self.redis_client.rpush(queue_name, message_json)
            return True
        except Exception as e:
            print(f"Error pushing task: {e}")
            return False

    def pop_task(self, queue: str, timeout: int = 5) -> Optional[Message]:
        """
        Remove and return a message from the named queue, waiting up to the given timeout.
        
        Parameters:
            queue (str): Name of the queue (without prefix).
            timeout (int): Maximum seconds to block waiting for a message.
        
        Returns:
            Message: The retrieved Message when available.
            None: If no message is available before the timeout or if an error occurs.
        """
        try:
            queue_name = f"{self.prefix}:queue:{queue}"
            result = self.redis_client.blpop(queue_name, timeout=timeout)
            if result:
                _, message_json = result
                data = json.loads(message_json)
                return Message(**data)
            return None
        except Exception as e:
            print(f"Error popping task: {e}")
            return None

    def get_queue_depth(self, queue: str) -> int:
        """
        Get the number of messages currently in the named queue.
        
        Returns:
            Number of messages in the queue.
        """
        queue_name = f"{self.prefix}:queue:{queue}"
        return self.redis_client.llen(queue_name)

    def close(self) -> None:
        """
        Close the manager's Redis resources.
        
        Closes the pubsub subscription and the underlying Redis client connection. After calling this method the QueueManager must not be used for further publish/subscribe or queue operations.
        """
        self.pubsub.close()
        self.redis_client.close()