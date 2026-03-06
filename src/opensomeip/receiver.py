"""MessageReceiver — thread-safe dual sync/async iterator for incoming messages.

Provides both ``__iter__`` (blocking) and ``__aiter__`` (non-blocking) interfaces,
allowing consumers to choose between synchronous and asynchronous consumption of
incoming SOME/IP messages.
"""

from __future__ import annotations

import asyncio
import queue
import threading
from typing import Any

from opensomeip.message import Message

_SENTINEL: Any = object()


class MessageReceiver:
    """Thread-safe message queue with dual sync/async iterator interface.

    C++ callbacks push messages via :meth:`put`. Consumers iterate using
    ``for msg in receiver:`` (sync) or ``async for msg in receiver:`` (async).

    The receiver must be :meth:`close`-d to signal end-of-stream.
    """

    def __init__(self, maxsize: int = 0) -> None:
        self._sync_queue: queue.Queue[Message | Any] = queue.Queue(maxsize=maxsize)
        self._async_queue: asyncio.Queue[Message | Any] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._closed = False
        self._lock = threading.Lock()

    def _ensure_async_queue(self) -> asyncio.Queue[Message | Any]:
        with self._lock:
            if self._async_queue is None:
                self._async_queue = asyncio.Queue()
                try:
                    self._loop = asyncio.get_running_loop()
                except RuntimeError:
                    self._loop = None
            return self._async_queue

    def _put_async(self, item: Message | Any) -> None:
        with self._lock:
            aq = self._async_queue
            loop = self._loop
        if aq is None:
            return
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(aq.put_nowait, item)
        else:
            import contextlib

            with contextlib.suppress(Exception):
                aq.put_nowait(item)

    def put(self, message: Message) -> None:
        """Push a message into the receiver (called from callback threads).

        Thread-safe. If an asyncio queue has been initialized, the message
        is also pushed there via ``call_soon_threadsafe``.
        """
        if self._closed:
            return
        self._sync_queue.put_nowait(message)
        self._put_async(message)

    def close(self) -> None:
        """Signal end-of-stream. Unblocks all waiting consumers."""
        self._closed = True
        self._sync_queue.put_nowait(_SENTINEL)
        self._put_async(_SENTINEL)

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def pending(self) -> int:
        """Number of messages currently queued (sync queue)."""
        return self._sync_queue.qsize()

    # --- Sync iterator ---

    def __iter__(self) -> MessageReceiver:
        return self

    def __next__(self) -> Message:
        """Block until a message is available. Raises ``StopIteration`` on close."""
        while True:
            try:
                item = self._sync_queue.get(timeout=0.5)
            except queue.Empty:
                if self._closed:
                    raise StopIteration from None
                continue
            if item is _SENTINEL:
                raise StopIteration
            return item

    # --- Async iterator ---

    def __aiter__(self) -> MessageReceiver:
        self._ensure_async_queue()
        return self

    async def __anext__(self) -> Message:
        """Await until a message is available. Raises ``StopAsyncIteration`` on close."""
        q = self._ensure_async_queue()
        item = await q.get()
        if item is _SENTINEL:
            raise StopAsyncIteration
        return item
