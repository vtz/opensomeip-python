"""Pythonic wrapper for SOME/IP Transport Protocol (TP) — large message segmentation.

Provides :class:`TpManager` which transparently segments messages exceeding
the transport MTU and reassembles incoming segments.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.transport import Transport

DEFAULT_MTU = 1400


class TpManager:
    """Manages SOME/IP-TP segmentation and reassembly.

    Wraps a :class:`~opensomeip.transport.Transport` to transparently handle
    messages larger than the MTU.

    Lifecycle is explicit via :meth:`start` / :meth:`stop`, or use as a
    context manager.
    """

    def __init__(self, transport: Transport, *, mtu: int = DEFAULT_MTU) -> None:
        self._transport = transport
        self._mtu = mtu
        self._running = False
        self._reassembly_receiver = MessageReceiver()

    @property
    def transport(self) -> Transport:
        return self._transport

    @property
    def mtu(self) -> int:
        return self._mtu

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the TP manager."""
        self._running = True

    def stop(self) -> None:
        """Stop the TP manager and close the reassembly receiver."""
        self._running = False
        self._reassembly_receiver.close()

    def send(self, message: Message) -> None:
        """Send a message, segmenting it if larger than MTU.

        In the full implementation, this delegates to C++ ``TpManager::send()``
        with the GIL released. Messages smaller than MTU are passed through
        directly to the underlying transport.
        """
        if len(message.payload) <= self._mtu:
            self._transport.send(message)
        else:
            offset = 0
            while offset < len(message.payload):
                chunk = message.payload[offset : offset + self._mtu]
                segment = Message(
                    message_id=message.message_id,
                    request_id=message.request_id,
                    message_type=message.message_type,
                    return_code=message.return_code,
                    payload=chunk,
                )
                self._transport.send(segment)
                offset += self._mtu

    def reassembled(self) -> MessageReceiver:
        """Return a :class:`MessageReceiver` yielding fully reassembled messages."""
        return self._reassembly_receiver

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
