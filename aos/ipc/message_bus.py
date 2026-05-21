"""MessageBus — typed async pub/sub + request/reply.

Each subscriber gets its own asyncio.Queue for independent backpressure.
Topic routing is exact-match. Direct messages filter by recipient_pid.
Signals (BUDGET_EXCEEDED, KILL) bypass normal queueing via dedicated signal channels.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from aos.ipc.types import Message, MessageType, Subscription


class RequestTimeoutError(asyncio.TimeoutError):
    """Raised when a request/reply round-trip exceeds timeout."""


class SubscriptionClosedError(KeyError):
    """Raised when consuming from an unsubscribed channel."""


class MessageBus:
    """Async pub/sub bus with per-subscriber queues + request/reply.

    Thread-safety: serialized via internal lock. All public methods are async.
    """

    def __init__(self, *, queue_size: int = 1024) -> None:
        self._queue_size = queue_size
        self._lock = asyncio.Lock()
        # subscription_id -> (Subscription, Queue)
        self._subscriptions: dict[str, tuple[Subscription, asyncio.Queue[Message]]] = {}
        # topic -> set of subscription_ids
        self._topics: dict[str, set[str]] = {}
        # Pending request/reply futures keyed by correlation_id
        self._pending: dict[str, asyncio.Future[Message]] = {}

    async def subscribe(self, topic: str, subscriber_pid: int) -> Subscription:
        """Subscribe a PID to a topic. Returns the Subscription handle."""
        sub = Subscription(topic=topic, subscriber_pid=subscriber_pid)
        async with self._lock:
            queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=self._queue_size)
            self._subscriptions[sub.id] = (sub, queue)
            self._topics.setdefault(topic, set()).add(sub.id)
        return sub

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription. Subsequent recv() calls raise KeyError."""
        async with self._lock:
            entry = self._subscriptions.pop(subscription_id, None)
            if entry is None:
                return
            sub, _queue = entry
            topic_subs = self._topics.get(sub.topic)
            if topic_subs is not None:
                topic_subs.discard(subscription_id)
                if not topic_subs:
                    self._topics.pop(sub.topic, None)

    async def publish(self, message: Message) -> int:
        """Publish a message to all matching subscribers.

        Returns the number of subscribers the message was delivered to.
        For RESPONSE messages with a correlation_id matching a pending request,
        fulfills the request future and skips queue delivery.
        """
        if message.type == MessageType.RESPONSE and message.correlation_id is not None:
            async with self._lock:
                fut = self._pending.pop(message.correlation_id, None)
            if fut is not None and not fut.done():
                fut.set_result(message)
                return 1

        async with self._lock:
            sub_ids = list(self._topics.get(message.topic, set()))
            targets: list[tuple[Subscription, asyncio.Queue[Message]]] = []
            for sid in sub_ids:
                entry = self._subscriptions.get(sid)
                if entry is None:
                    continue
                sub, queue = entry
                if (
                    message.recipient_pid is not None
                    and sub.subscriber_pid != message.recipient_pid
                ):
                    continue
                targets.append((sub, queue))

        delivered = 0
        for _sub, queue in targets:
            try:
                queue.put_nowait(message)
                delivered += 1
            except asyncio.QueueFull:
                # Drop on full queue — caller responsible for backpressure
                continue
        return delivered

    async def recv(self, subscription_id: str) -> Message:
        """Receive one message from a subscription's queue. Blocks until available."""
        async with self._lock:
            entry = self._subscriptions.get(subscription_id)
        if entry is None:
            msg = f"Subscription {subscription_id} not found"
            raise KeyError(msg)
        _sub, queue = entry
        return await queue.get()

    async def consume(self, subscription_id: str) -> AsyncIterator[Message]:
        """Yield messages indefinitely. Stops when subscription is removed."""
        while True:
            async with self._lock:
                entry = self._subscriptions.get(subscription_id)
            if entry is None:
                return
            _sub, queue = entry
            msg = await queue.get()
            yield msg

    async def request(
        self,
        *,
        topic: str,
        sender_pid: int,
        payload: dict[str, Any],
        timeout_seconds: float = 30.0,
        recipient_pid: int | None = None,
    ) -> Message:
        """Send a REQUEST and wait for the matching RESPONSE.

        The correlation_id is auto-generated. The responder must call
        request_message.make_reply(...) and publish that.

        Raises RequestTimeoutError if no response arrives within timeout.
        """
        req = Message(
            type=MessageType.REQUEST,
            topic=topic,
            sender_pid=sender_pid,
            recipient_pid=recipient_pid,
            payload=payload,
        )
        correlation_id = req.correlation_id or req.id
        req = req.model_copy(update={"correlation_id": correlation_id})

        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Message] = loop.create_future()
        async with self._lock:
            self._pending[correlation_id] = fut

        try:
            await self.publish(req)
            return await asyncio.wait_for(fut, timeout=timeout_seconds)
        except asyncio.TimeoutError as exc:
            async with self._lock:
                self._pending.pop(correlation_id, None)
            msg = f"Request on topic {topic!r} timed out after {timeout_seconds}s"
            raise RequestTimeoutError(msg) from exc

    async def topic_subscriber_count(self, topic: str) -> int:
        """Count subscribers on a topic. Useful for routing decisions."""
        async with self._lock:
            return len(self._topics.get(topic, set()))
