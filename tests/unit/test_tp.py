"""Tests for opensomeip.tp — TpManager."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.tp import TpManager
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId


@pytest.fixture()
def transport() -> UdpTransport:
    t = UdpTransport(Endpoint("0.0.0.0", 0))
    t.start()
    return t


class TestTpManager:
    def test_lifecycle(self, transport: UdpTransport) -> None:
        tp = TpManager(transport)
        assert tp.is_running is False
        tp.start()
        assert tp.is_running is True
        tp.stop()
        assert tp.is_running is False

    def test_context_manager(self, transport: UdpTransport) -> None:
        with TpManager(transport) as tp:
            assert tp.is_running is True
        assert tp.is_running is False

    def test_mtu_default(self, transport: UdpTransport) -> None:
        tp = TpManager(transport)
        assert tp.mtu == 1400

    def test_custom_mtu(self, transport: UdpTransport) -> None:
        tp = TpManager(transport, mtu=500)
        assert tp.mtu == 500

    def test_transport_property(self, transport: UdpTransport) -> None:
        tp = TpManager(transport)
        assert tp.transport is transport

    def test_send_small_message(self, transport: UdpTransport) -> None:
        tp = TpManager(transport)
        tp.start()
        msg = Message(
            message_id=MessageId(0x1234, 0x0001),
            payload=b"\x01" * 100,
        )
        with patch.object(transport, "send"):
            tp.send(msg)
        tp.stop()

    def test_send_large_message_segments(self, transport: UdpTransport) -> None:
        tp = TpManager(transport, mtu=100)
        tp.start()
        msg = Message(
            message_id=MessageId(0x1234, 0x0001),
            payload=b"\xaa" * 350,
        )
        with patch.object(transport, "send"):
            tp.send(msg)
        tp.stop()

    def test_reassembled_returns_receiver(self, transport: UdpTransport) -> None:
        tp = TpManager(transport)
        receiver = tp.reassembled()
        assert isinstance(receiver, MessageReceiver)

    def test_stop_closes_reassembly_receiver(self, transport: UdpTransport) -> None:
        tp = TpManager(transport)
        receiver = tp.reassembled()
        tp.start()
        tp.stop()
        assert receiver.closed is True

    @pytest.mark.asyncio
    async def test_async_context_manager(self, transport: UdpTransport) -> None:
        async with TpManager(transport) as tp:
            assert tp.is_running is True
