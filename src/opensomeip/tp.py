"""Pythonic wrapper for SOME/IP Transport Protocol (TP) — large message segmentation.

When the C++ extension is available, delegates to the native TP
implementations. Otherwise, provides stub behavior for testing.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip._bridge import get_ext, to_cpp_message
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.transport import Endpoint, Transport

DEFAULT_MTU = 1400


class TpManager:
    """Manages SOME/IP-TP segmentation and reassembly.

    When the C++ extension is available, delegates to the native
    ``_opensomeip.tp.TpManager``.
    """

    def __init__(self, transport: Transport, *, mtu: int = DEFAULT_MTU) -> None:
        self._transport = transport
        self._mtu = mtu
        self._running = False
        self._reassembly_receiver = MessageReceiver()
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            cfg = ext.tp.TpConfig()
            cfg.max_segment_size = mtu
            self._cpp = ext.tp.TpManager(cfg)

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
        if self._cpp is not None:
            try:
                self._cpp.initialize()
                receiver = self._reassembly_receiver

                def _on_complete(complete_data: Any) -> None:
                    msg = Message(payload=bytes(complete_data))
                    receiver.put(msg)

                self._cpp.set_message_callback(_on_complete)
            except Exception:
                pass
        self._running = True

    def stop(self) -> None:
        """Stop the TP manager and close the reassembly receiver."""
        if self._cpp is not None:
            try:
                self._cpp.shutdown()
            except Exception:
                pass
        self._running = False
        self._reassembly_receiver.close()

    def send(
        self, message: Message, endpoint: Endpoint | None = None
    ) -> None:
        """Send a message, segmenting it if larger than MTU.

        When the C++ extension is available, delegates to the native
        ``TpManager::segment_message`` for proper SOME/IP-TP segmentation.
        Falls back to pure-Python segmentation if C++ fails.
        """
        if self._cpp is not None:
            try:
                cpp_msg = to_cpp_message(message)
                if self._cpp.needs_segmentation(cpp_msg):
                    _result, transfer_id = self._cpp.segment_message(cpp_msg)
                    max_segments = (len(message.payload) // self._mtu) + 2
                    for _ in range(max_segments):
                        seg_result, segment = self._cpp.get_next_segment(transfer_id)
                        if int(seg_result) != 0:
                            break
                        seg_msg = Message(
                            message_id=message.message_id,
                            request_id=message.request_id,
                            message_type=message.message_type,
                            return_code=message.return_code,
                            payload=bytes(segment.payload),
                        )
                        self._transport.send(seg_msg, endpoint)
                    return
                else:
                    self._transport.send(message, endpoint)
                    return
            except Exception:
                pass

        if len(message.payload) <= self._mtu:
            self._transport.send(message, endpoint)
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
                self._transport.send(segment, endpoint)
                offset += self._mtu

    def reassembled(self) -> MessageReceiver:
        """Return a :class:`MessageReceiver` yielding fully reassembled messages."""
        return self._reassembly_receiver

    def get_statistics(self) -> Any:
        """Return TP statistics (native only)."""
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
