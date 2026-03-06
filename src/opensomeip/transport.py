"""Pythonic wrappers for SOME/IP transports (UDP and TCP).

Provides context managers, explicit lifecycle methods, and a callback bridge
that feeds incoming messages to a :class:`~opensomeip.receiver.MessageReceiver`.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

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
        """Start the transport. Must be called before :meth:`send`.

        In the full implementation, this delegates to the C++ transport's
        ``start()`` with the GIL released.
        """
        if self._running:
            return
        self._running = True

    def stop(self) -> None:
        """Stop the transport and close the message receiver.

        In the full implementation, this delegates to the C++ transport's
        ``stop()`` with the GIL released.
        """
        if not self._running:
            return
        self._running = False
        self._receiver.close()

    def send(self, message: Message) -> None:
        """Send a SOME/IP message.

        In the full implementation, this converts to C++ ``MessagePtr`` and
        calls the transport's ``send()`` with the GIL released.
        """
        if not self._running:
            raise TransportError("Transport is not running")

    # --- Context manager (sync) ---

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

    # --- Context manager (async) ---

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

    @property
    def multicast_group(self) -> str | None:
        return self._multicast_group


class TcpTransport(Transport):
    """SOME/IP transport over TCP.

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

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        """Establish the TCP connection to the remote endpoint.

        In the full implementation, this delegates to C++ with the GIL released.
        """
        if self._remote is None:
            raise TransportError("No remote endpoint configured")
        self._connected = True

    def start(self) -> None:
        super().start()
        if self._remote is not None:
            self.connect()

    def stop(self) -> None:
        self._connected = False
        super().stop()
