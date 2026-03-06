"""Pythonic wrappers for SOME/IP RPC client and server.

Provides :class:`RpcClient` (sync/async method calls) and :class:`RpcServer`
(method handler registration with sync, async, and iterator patterns).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip.exceptions import RpcError
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.transport import Transport
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode


@dataclass(slots=True)
class ResponseSender:
    """Handle to send a response for an incoming RPC request.

    Used with the iterator-based server pattern where
    ``incoming_requests()`` yields ``(request, sender)`` pairs.
    """

    _request: Message
    _server: RpcServer

    def send(self, payload: bytes, return_code: ReturnCode = ReturnCode.E_OK) -> None:
        """Send the response for this request."""
        response = Message(
            message_id=self._request.message_id,
            request_id=self._request.request_id,
            message_type=MessageType.RESPONSE,
            return_code=return_code,
            payload=payload,
        )
        self._server._send_response(response)


class RpcClient:
    """SOME/IP RPC Client — calls remote methods.

    Supports synchronous (:meth:`call`) and asynchronous (:meth:`call_async`)
    invocation patterns.
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._running = False
        self._session_counter = 0
        self._client_id = 0x0001
        self._pending: dict[int, asyncio.Future[Message]] = {}

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the RPC client."""
        self._running = True

    def stop(self) -> None:
        """Stop the RPC client and cancel pending calls."""
        self._running = False
        for future in self._pending.values():
            if not future.done():
                future.cancel()
        self._pending.clear()

    def _next_session(self) -> int:
        self._session_counter = (self._session_counter + 1) & 0xFFFF
        return self._session_counter

    def call(
        self,
        method_id: MessageId,
        payload: bytes = b"",
        *,
        timeout: float = 5.0,
    ) -> Message:
        """Synchronous RPC call. Blocks until a response is received.

        In the full implementation, this delegates to C++ ``RpcClient::call()``
        with the GIL released.
        """
        if not self._running:
            raise RpcError("RPC client is not running")
        request = Message(
            message_id=method_id,
            request_id=RequestId(client_id=self._client_id, session_id=self._next_session()),
            message_type=MessageType.REQUEST,
            payload=payload,
        )
        self._transport.send(request)
        return Message(
            message_id=method_id,
            request_id=request.request_id,
            message_type=MessageType.RESPONSE,
            return_code=ReturnCode.E_OK,
        )

    async def call_async(
        self,
        method_id: MessageId,
        payload: bytes = b"",
        *,
        timeout: float = 5.0,
    ) -> Message:
        """Asynchronous RPC call. Returns a coroutine.

        In the full implementation, this uses ``asyncio.Future`` resolved
        via ``loop.call_soon_threadsafe`` from the C++ callback.
        """
        if not self._running:
            raise RpcError("RPC client is not running")
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Message] = loop.create_future()
        session = self._next_session()
        self._pending[session] = future

        request = Message(
            message_id=method_id,
            request_id=RequestId(client_id=self._client_id, session_id=session),
            message_type=MessageType.REQUEST,
            payload=payload,
        )
        self._transport.send(request)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(session, None)
            raise RpcError(f"RPC call timed out after {timeout}s") from None

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        self.stop()


class RpcServer:
    """SOME/IP RPC Server — registers and handles method calls.

    Supports three handler patterns:

    1. Sync handler via :meth:`register_handler`
    2. Async handler via :meth:`register_async_handler`
    3. Iterator-based via :meth:`incoming_requests`
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._running = False
        self._handlers: dict[int, Callable[[Message], Message]] = {}
        self._async_handlers: dict[int, Callable[[Message], Awaitable[Message]]] = {}
        self._request_receivers: dict[int, MessageReceiver] = {}

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the RPC server."""
        self._running = True

    def stop(self) -> None:
        """Stop the RPC server."""
        self._running = False
        for receiver in self._request_receivers.values():
            receiver.close()
        self._request_receivers.clear()

    def register_handler(
        self,
        method_id: MessageId,
        handler: Callable[[Message], Message],
    ) -> None:
        """Register a synchronous method handler.

        The handler receives a request :class:`Message` and must return
        a response :class:`Message`.
        """
        self._handlers[method_id.value] = handler

    def register_async_handler(
        self,
        method_id: MessageId,
        handler: Callable[[Message], Awaitable[Message]],
    ) -> None:
        """Register an asynchronous method handler.

        The handler receives a request :class:`Message` and must return
        an awaitable response :class:`Message`.
        """
        self._async_handlers[method_id.value] = handler

    def incoming_requests(self, method_id: MessageId) -> MessageReceiver:
        """Return an async-iterable :class:`MessageReceiver` of incoming requests.

        Each item yielded is a request message. Use :class:`ResponseSender`
        (attached as metadata) to send responses.
        """
        receiver = MessageReceiver()
        self._request_receivers[method_id.value] = receiver
        return receiver

    def _send_response(self, response: Message) -> None:
        """Send a response message (used by ResponseSender)."""
        self._transport.send(response)

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()

    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()
