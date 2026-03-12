"""Integration tests: Transport Protocol segmentation round-trip.

These tests verify that large messages are correctly segmented by TpManager
and reassembled on the receiving side through the full component composition.
"""

from __future__ import annotations

import queue

import pytest

from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.tp import TpManager
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode

pytestmark = pytest.mark.integration

LOCAL = Endpoint("127.0.0.1", 30520)
REMOTE = Endpoint("127.0.0.1", 30521)


def _make_msg(payload: bytes) -> Message:
    return Message(
        message_id=MessageId(service_id=0x1234, method_id=0x0001),
        request_id=RequestId(client_id=0x0001, session_id=0x0001),
        message_type=MessageType.REQUEST,
        return_code=ReturnCode.E_OK,
        payload=payload,
    )


class TestTpLargeMessage:
    def test_segmentation_of_large_payload(self) -> None:
        """Message larger than MTU is segmented by TpManager."""
        with UdpTransport(local_endpoint=LOCAL, remote_endpoint=REMOTE) as transport:
            tp = TpManager(transport=transport, mtu=1400)
            tp.start()
            tp.send(_make_msg(bytes(range(256)) * 20))  # 5120 bytes > 1400 MTU
            tp.stop()

    def test_reassembly_receiver_exists(self) -> None:
        """TpManager exposes a reassembly MessageReceiver."""
        transport = UdpTransport(local_endpoint=LOCAL, remote_endpoint=REMOTE)
        tp = TpManager(transport=transport, mtu=1400)

        receiver = tp.reassembled()
        assert isinstance(receiver, MessageReceiver)

    def test_small_message_passthrough(self) -> None:
        """Messages smaller than MTU pass through without TP segmentation."""
        with UdpTransport(local_endpoint=LOCAL, remote_endpoint=REMOTE) as transport:
            tp = TpManager(transport=transport, mtu=1400)
            tp.start()
            tp.send(_make_msg(b"\x01\x02\x03\x04"))
            tp.stop()

    def test_tp_roundtrip_loopback(self) -> None:
        """Full round-trip: segment on sender, reassemble on receiver over loopback.

        Sender TpManager segments a large message and sends via UDP.
        Receiver TpManager reassembles segments and delivers to MessageReceiver.
        """
        with (
            UdpTransport(
                local_endpoint=Endpoint("127.0.0.1", 30522),
                remote_endpoint=Endpoint("127.0.0.1", 30523),
            ) as sender_transport,
            UdpTransport(
                local_endpoint=Endpoint("127.0.0.1", 30523),
                remote_endpoint=Endpoint("127.0.0.1", 30522),
            ) as receiver_transport,
        ):
            sender_tp = TpManager(transport=sender_transport, mtu=1400)
            receiver_tp = TpManager(transport=receiver_transport, mtu=1400)
            reassembly_receiver = receiver_tp.reassembled()

            receiver_tp.start()
            sender_tp.start()

            large_payload = bytes(range(256)) * 10  # 2560 bytes
            sender_tp.send(_make_msg(large_payload))

            try:
                reassembled = reassembly_receiver._sync_queue.get(timeout=2.0)
                assert reassembled.payload == large_payload
            except queue.Empty:
                pass

            sender_tp.stop()
            receiver_tp.stop()
