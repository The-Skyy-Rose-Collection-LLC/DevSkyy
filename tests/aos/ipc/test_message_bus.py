"""Tests for MessageBus IPC."""

from __future__ import annotations

import asyncio

import pytest

from aos.ipc.message_bus import MessageBus, RequestTimeoutError
from aos.ipc.types import Message, MessageType


@pytest.fixture
def bus() -> MessageBus:
    return MessageBus()


class TestPubSub:
    @pytest.mark.asyncio
    async def test_publish_delivers_to_subscriber(self, bus: MessageBus):
        received: list[Message] = []
        sub = await bus.subscribe("test.topic", subscriber_pid=42)

        async def consume():
            async for msg in bus.consume(sub.id):
                received.append(msg)
                break

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.01)
        await bus.publish(
            Message(
                type=MessageType.EVENT,
                topic="test.topic",
                sender_pid=1,
                payload={"hello": "world"},
            )
        )
        await asyncio.wait_for(task, timeout=1.0)
        assert len(received) == 1
        assert received[0].payload == {"hello": "world"}

    @pytest.mark.asyncio
    async def test_multiple_subscribers_all_receive(self, bus: MessageBus):
        sub1 = await bus.subscribe("multi", subscriber_pid=1)
        sub2 = await bus.subscribe("multi", subscriber_pid=2)

        await bus.publish(
            Message(type=MessageType.EVENT, topic="multi", sender_pid=99, payload={"n": 1})
        )

        m1 = await asyncio.wait_for(bus.recv(sub1.id), timeout=1.0)
        m2 = await asyncio.wait_for(bus.recv(sub2.id), timeout=1.0)
        assert m1.payload == {"n": 1}
        assert m2.payload == {"n": 1}

    @pytest.mark.asyncio
    async def test_unsubscribe_stops_delivery(self, bus: MessageBus):
        sub = await bus.subscribe("byebye", subscriber_pid=5)
        await bus.unsubscribe(sub.id)
        await bus.publish(Message(type=MessageType.EVENT, topic="byebye", sender_pid=1, payload={}))
        with pytest.raises(KeyError):
            await bus.recv(sub.id)

    @pytest.mark.asyncio
    async def test_topic_isolation(self, bus: MessageBus):
        sub_a = await bus.subscribe("topic.a", subscriber_pid=1)
        sub_b = await bus.subscribe("topic.b", subscriber_pid=2)

        await bus.publish(
            Message(type=MessageType.EVENT, topic="topic.a", sender_pid=99, payload={"x": "a"})
        )

        m = await asyncio.wait_for(bus.recv(sub_a.id), timeout=1.0)
        assert m.payload == {"x": "a"}
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(bus.recv(sub_b.id), timeout=0.05)


class TestRecipientFilter:
    @pytest.mark.asyncio
    async def test_direct_message_to_pid(self, bus: MessageBus):
        sub_target = await bus.subscribe("direct", subscriber_pid=7)
        sub_other = await bus.subscribe("direct", subscriber_pid=8)

        await bus.publish(
            Message(
                type=MessageType.EVENT,
                topic="direct",
                sender_pid=1,
                recipient_pid=7,
                payload={"for": "seven"},
            )
        )

        m = await asyncio.wait_for(bus.recv(sub_target.id), timeout=1.0)
        assert m.payload == {"for": "seven"}
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(bus.recv(sub_other.id), timeout=0.05)


class TestRequestReply:
    @pytest.mark.asyncio
    async def test_request_reply_roundtrip(self, bus: MessageBus):
        async def responder():
            sub = await bus.subscribe("svc.echo", subscriber_pid=100)
            req = await bus.recv(sub.id)
            await bus.publish(req.make_reply(sender_pid=100, payload={"echo": req.payload}))

        responder_task = asyncio.create_task(responder())
        await asyncio.sleep(0.01)

        reply = await bus.request(
            topic="svc.echo",
            sender_pid=1,
            payload={"msg": "hi"},
            timeout_seconds=1.0,
        )
        await responder_task
        assert reply.payload == {"echo": {"msg": "hi"}}

    @pytest.mark.asyncio
    async def test_request_timeout(self, bus: MessageBus):
        with pytest.raises(RequestTimeoutError):
            await bus.request(
                topic="nobody.listens",
                sender_pid=1,
                payload={},
                timeout_seconds=0.1,
            )


class TestMessage:
    def test_make_reply_links_correlation(self):
        req = Message(
            type=MessageType.REQUEST,
            topic="t",
            sender_pid=1,
            correlation_id="abc",
            payload={},
        )
        rep = req.make_reply(sender_pid=2, payload={"ok": True})
        assert rep.type == MessageType.RESPONSE
        assert rep.recipient_pid == 1
        assert rep.correlation_id == "abc"

    def test_make_reply_uses_id_when_no_correlation(self):
        req = Message(type=MessageType.REQUEST, topic="t", sender_pid=1, payload={})
        rep = req.make_reply(sender_pid=2, payload={})
        assert rep.correlation_id == req.id

    def test_is_signal(self):
        m = Message(type=MessageType.SIGNAL, topic="kill", sender_pid=0, payload={})
        assert m.is_signal
