"""Tests for opensomeip.receiver — MessageReceiver sync/async iterator."""

from __future__ import annotations

import asyncio
import threading
import time

import pytest

from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.types import MessageId


def _make_msg(n: int) -> Message:
    return Message(message_id=MessageId(service_id=n, method_id=0))


class TestMessageReceiverSync:
    def test_put_and_iterate(self) -> None:
        r = MessageReceiver()
        r.put(_make_msg(1))
        r.put(_make_msg(2))
        r.close()

        msgs = list(r)
        assert len(msgs) == 2
        assert msgs[0].message_id.service_id == 1
        assert msgs[1].message_id.service_id == 2

    def test_close_stops_iteration(self) -> None:
        r = MessageReceiver()
        r.close()
        assert list(r) == []

    def test_pending_count(self) -> None:
        r = MessageReceiver()
        assert r.pending == 0
        r.put(_make_msg(1))
        assert r.pending == 1
        r.put(_make_msg(2))
        assert r.pending == 2

    def test_closed_property(self) -> None:
        r = MessageReceiver()
        assert r.closed is False
        r.close()
        assert r.closed is True

    def test_put_after_close_is_ignored(self) -> None:
        r = MessageReceiver()
        r.close()
        r.put(_make_msg(1))

    def test_threaded_put(self) -> None:
        r = MessageReceiver()
        results: list[Message] = []

        def producer() -> None:
            for i in range(5):
                r.put(_make_msg(i))
                time.sleep(0.01)
            r.close()

        t = threading.Thread(target=producer)
        t.start()

        for msg in r:
            results.append(msg)

        t.join()
        assert len(results) == 5


class TestMessageReceiverAsync:
    @pytest.mark.asyncio
    async def test_async_iterate(self) -> None:
        r = MessageReceiver()
        # Initialize the async queue first by calling __aiter__
        aiter = r.__aiter__()
        r.put(_make_msg(1))
        r.put(_make_msg(2))
        r.close()

        msgs: list[Message] = []
        async for msg in aiter:
            msgs.append(msg)

        assert len(msgs) == 2

    @pytest.mark.asyncio
    async def test_async_close_stops(self) -> None:
        r = MessageReceiver()
        aiter = r.__aiter__()

        async def close_later() -> None:
            await asyncio.sleep(0.05)
            r.close()

        loop = asyncio.get_running_loop()
        loop.call_later(0.05, r.close)

        msgs: list[Message] = []
        async for msg in aiter:
            msgs.append(msg)

        assert len(msgs) == 0

    @pytest.mark.asyncio
    async def test_async_put_from_thread(self) -> None:
        r = MessageReceiver()
        aiter = r.__aiter__()

        def producer() -> None:
            time.sleep(0.05)
            r.put(_make_msg(42))
            time.sleep(0.05)
            r.close()

        t = threading.Thread(target=producer)
        t.start()

        msgs: list[Message] = []
        async for msg in aiter:
            msgs.append(msg)

        t.join()
        assert len(msgs) == 1
        assert msgs[0].message_id.service_id == 42
