"""Pythonic wrappers for SOME/IP transports (UDP and TCP).

When the C++ extension is available, delegates to the native transport
implementations. Otherwise, provides stub behavior for testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip._bridge import (
    from_cpp_endpoint,
    from_cpp_message,
    get_ext,
    to_cpp_endpoint,
    to_cpp_message,
)
from opensomeip.exceptions import TransportError
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver


@dataclass(frozen=True, slots=True)
class Endpoint:
    """A network endpoint (IP address + port)."""

    ip: str
    port: int

    def __post_init__(self) -> None:
        if not (0 <= self.port <= 65535):
            raise ValueError(f"port must be 0..65535, got {self.port}")

    def __repr__(self) -> str:
        return f"Endpoint({self.ip!r}, {self.port})"


class _NativeTransportListener:
    """Bridges C++ ITransportListener callbacks into a MessageReceiver."""

    def __init__(self, receiver: MessageReceiver) -> None:
        self._receiver = receiver
        ext = get_ext()
        if ext is None:
            self._cpp: Any = None
            return

        parent = self

        class _Listener(ext.ITransportListener):  # type: ignore[name-defined,misc]
            def on_message_received(self, message: Any, sender: Any) -> None:
                py_msg = from_cpp_message(message)
                try:
                    py_msg.source_endpoint = from_cpp_endpoint(sender)
                except Exception:
                    pass
                parent._receiver.put(py_msg)

            def on_connection_lost(self, endpoint: Any) -> None:
                pass

            def on_connection_established(self, endpoint: Any) -> None:
                pass

            def on_error(self, error: Any) -> None:
                pass

        self._cpp = _Listener()

    @property
    def cpp(self) -> Any:
        return self._cpp


class Transport:
    """Base class for SOME/IP transports.

    Subclasses (:class:`UdpTransport`, :class:`TcpTransport`) provide
    protocol-specific behavior. All transports expose:

    - :meth:`start` / :meth:`stop` for explicit lifecycle control
    - Context manager support (``with`` / ``async with``)
    - :meth:`send` to transmit messages
    - :attr:`receiver` to consume incoming messages as an iterator
    """

    def __init__(
        self,
        local_endpoint: Endpoint,
        remote_endpoint: Endpoint | None = None,
    ) -> None:
        self._local = local_endpoint
        self._remote = remote_endpoint
        self._running = False
        self._receiver = MessageReceiver()
        self._listener = _NativeTransportListener(self._receiver)
        self._cpp: Any = None

    @property
    def local_endpoint(self) -> Endpoint:
        return self._local

    @property
    def remote_endpoint(self) -> Endpoint | None:
        return self._remote

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def receiver(self) -> MessageReceiver:
        """Access the :class:`MessageReceiver` for incoming messages."""
        return self._receiver

    def start(self) -> None:
        """Start the transport, delegating to C++ when available."""
        if self._running:
            return
        if self._cpp is not None:
            try:
                result = self._cpp.start()
                if hasattr(result, "name") and result.name != "SUCCESS":
                    raise TransportError(f"Native transport failed to start: {result.name}")
            except TransportError:
                raise
            except Exception:
                pass
        self._running = True

    def stop(self) -> None:
        """Stop the transport and close the message receiver."""
        if not self._running:
            return
        self._running = False
        if self._cpp is not None:
            self._cpp.stop()
        self._receiver.close()

    def send(self, message: Message, endpoint: Endpoint | None = None) -> None:
        """Send a SOME/IP message, delegating to C++ when available."""
        if not self._running:
            raise TransportError("Transport is not running")
        if self._cpp is not None:
            cpp_msg = to_cpp_message(message)
            target = endpoint or self._remote
            if target is None and hasattr(message, "source_endpoint"):
                target = message.source_endpoint
            if target is not None:
                cpp_ep = to_cpp_endpoint(target)
                self._cpp.send_message(cpp_msg, cpp_ep)

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


class UdpTransport(Transport):
    """SOME/IP transport over UDP.

    When the C++ extension is available, delegates to the native
    ``_opensomeip.UdpTransport``.

    Args:
        local_endpoint: The local bind address.
        remote_endpoint: The remote peer address.
        multicast_group: Optional multicast group to join.
    """

    def __init__(
        self,
        local_endpoint: Endpoint,
        remote_endpoint: Endpoint | None = None,
        *,
        multicast_group: str | None = None,
    ) -> None:
        super().__init__(local_endpoint, remote_endpoint)
        self._multicast_group = multicast_group
        ext = get_ext()
        if ext is not None:
            cpp_ep = to_cpp_endpoint(local_endpoint)
            self._cpp = ext.UdpTransport(cpp_ep)
            if self._listener.cpp is not None:
                self._cpp.set_listener(self._listener.cpp)

    @property
    def multicast_group(self) -> str | None:
        return self._multicast_group

    def start(self) -> None:
        super().start()
        if self._cpp is not None and self._multicast_group is not None:
            self._cpp.join_multicast_group(self._multicast_group)


class TcpTransport(Transport):
    """SOME/IP transport over TCP.

    When the C++ extension is available, delegates to the native
    ``_opensomeip.TcpTransport``.

    Args:
        local_endpoint: The local bind address.
        remote_endpoint: The remote peer address to connect to.
    """

    def __init__(
        self,
        local_endpoint: Endpoint,
        remote_endpoint: Endpoint | None = None,
    ) -> None:
        super().__init__(local_endpoint, remote_endpoint)
        self._connected = False
        ext = get_ext()
        if ext is not None:
            self._cpp = ext.TcpTransport()
            if self._listener.cpp is not None:
                self._cpp.set_listener(self._listener.cpp)

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        """Establish the TCP connection to the remote endpoint."""
        if self._remote is None:
            raise TransportError("No remote endpoint configured")
        if self._cpp is not None:
            cpp_ep = to_cpp_endpoint(self._remote)
            try:
                self._cpp.connect(cpp_ep)
            except Exception:
                pass
        self._connected = True

    def start(self) -> None:
        if self._cpp is not None:
            cpp_local = to_cpp_endpoint(self._local)
            try:
                self._cpp.initialize(cpp_local)
            except Exception:
                pass
        super().start()
        if self._remote is not None:
            self.connect()

    def stop(self) -> None:
        was_connected = self._connected
        self._connected = False
        if self._cpp is not None and was_connected:
            try:
                self._cpp.disconnect()
            except Exception:
                pass
        super().stop()
