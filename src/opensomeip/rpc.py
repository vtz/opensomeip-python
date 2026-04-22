"""Pythonic wrappers for SOME/IP RPC client and server.

When the C++ extension is available, delegates to the native RPC
implementations. Otherwise, provides stub behavior for testing.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip._bridge import from_cpp_message, get_ext, to_cpp_message
from opensomeip.exceptions import RpcError
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.transport import Transport
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode


@dataclass(slots=True)
class ResponseSender:
    """Handle to send a response for an incoming RPC request."""

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

    When the C++ extension is available, delegates to the native
    ``_opensomeip.rpc.RpcClient``.
    """

    def __init__(self, transport: Transport, *, client_id: int = 0x0001) -> None:
        self._transport = transport
        self._running = False
        self._session_counter = 0
        self._client_id = client_id
        self._pending: dict[int, asyncio.Future[Message]] = {}
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            self._cpp = ext.rpc.RpcClient(client_id)

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the RPC client."""
        if self._cpp is not None:
            try:
                self._cpp.initialize()
            except Exception:
                pass
        self._running = True

    def stop(self) -> None:
        """Stop the RPC client and cancel pending calls."""
        if self._cpp is not None:
            try:
                self._cpp.shutdown()
            except Exception:
                pass
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
        """Synchronous RPC call. Blocks until a response is received."""
        if not self._running:
            raise RpcError("RPC client is not running")

        if self._cpp is None:
            raise RpcError(
                "Cannot perform RPC call: opensomeip C++ extension is not available. "
                "See https://github.com/vtz/opensomeip-python#troubleshooting"
            )

        try:
            import struct as _struct

            params = list(_struct.unpack(f"!{len(payload)}B", payload)) if payload else []
            cpp_timeout = get_ext().rpc.RpcTimeout()
            result = self._cpp.call_method_sync(
                method_id.service_id,
                method_id.method_id,
                params,
                cpp_timeout,
            )
            if int(result.result) != 0:
                raise RpcError(
                    f"RPC call to {method_id} failed with native result code {result.result}"
                )
            return_payload = bytes(result.return_values) if result.return_values else b""
            return Message(
                message_id=method_id,
                request_id=RequestId(
                    client_id=self._client_id, session_id=self._next_session()
                ),
                message_type=MessageType.RESPONSE,
                return_code=ReturnCode.E_OK,
                payload=return_payload,
            )
        except RpcError:
            raise
        except Exception as exc:
            raise RpcError(f"Native RPC call to {method_id} failed: {exc}") from exc

    async def call_async(
        self,
        method_id: MessageId,
        payload: bytes = b"",
        *,
        timeout: float = 5.0,
    ) -> Message:
        """Asynchronous RPC call. Returns a coroutine."""
        if not self._running:
            raise RpcError("RPC client is not running")

        if self._cpp is None:
            raise RpcError(
                "Cannot perform RPC call: opensomeip C++ extension is not available. "
                "See https://github.com/vtz/opensomeip-python#troubleshooting"
            )

        import struct

        params = list(struct.unpack(f"!{len(payload)}B", payload)) if payload else []
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Message] = loop.create_future()
        session = self._next_session()
        self._pending[session] = future

        def _on_response(cpp_resp: Any) -> None:
            return_payload = bytes(cpp_resp.return_values) if cpp_resp.return_values else b""
            py_msg = Message(
                message_id=method_id,
                request_id=RequestId(client_id=self._client_id, session_id=session),
                message_type=MessageType.RESPONSE,
                return_code=ReturnCode.E_OK,
                payload=return_payload,
            )
            loop.call_soon_threadsafe(future.set_result, py_msg)

        cpp_timeout = get_ext().rpc.RpcTimeout()
        self._cpp.call_method_async(
            method_id.service_id,
            method_id.method_id,
            params,
            _on_response,
            cpp_timeout,
        )
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(session, None)
            raise RpcError(f"RPC call timed out after {timeout}s") from None

    def get_statistics(self) -> Any:
        """Return RPC client statistics (native only)."""
        if self._cpp is not None:
            return self._cpp.get_statistics()
        return None

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

    When the C++ extension is available, delegates to the native
    ``_opensomeip.rpc.RpcServer``.
    """

    def __init__(self, transport: Transport, *, service_id: int = 0x0000) -> None:
        self._transport = transport
        self._running = False
        self._handlers: dict[int, Callable[[Message], Message]] = {}
        self._async_handlers: dict[int, Callable[[Message], Awaitable[Message]]] = {}
        self._request_receivers: dict[int, MessageReceiver] = {}
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            self._cpp = ext.rpc.RpcServer(service_id)

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the RPC server."""
        if self._cpp is not None:
            try:
                self._cpp.initialize()
            except Exception:
                pass
        self._running = True

    def stop(self) -> None:
        """Stop the RPC server."""
        if self._cpp is not None:
            try:
                self._cpp.shutdown()
            except Exception:
                pass
        self._running = False
        for receiver in self._request_receivers.values():
            receiver.close()
        self._request_receivers.clear()

    def register_handler(
        self,
        method_id: MessageId,
        handler: Callable[[Message], Message],
    ) -> None:
        """Register a synchronous method handler."""
        self._handlers[method_id.value] = handler

        if self._cpp is not None:

            def _cpp_handler(cpp_req: Any) -> Any:
                py_msg = from_cpp_message(cpp_req)
                py_resp = handler(py_msg)
                return to_cpp_message(py_resp)

            self._cpp.register_method(method_id.method_id, _cpp_handler)

    def register_async_handler(
        self,
        method_id: MessageId,
        handler: Callable[[Message], Awaitable[Message]],
    ) -> None:
        """Register an asynchronous method handler."""
        self._async_handlers[method_id.value] = handler

    def incoming_requests(self, method_id: MessageId) -> MessageReceiver:
        """Return an async-iterable receiver of incoming requests."""
        receiver = MessageReceiver()
        self._request_receivers[method_id.value] = receiver
        return receiver

    def _send_response(self, response: Message) -> None:
        """Send a response message (used by ResponseSender)."""
        self._transport.send(response)

    def get_statistics(self) -> Any:
        """Return RPC server statistics (native only)."""
        if self._cpp is not None:
            return self._cpp.get_statistics()
        return None

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
