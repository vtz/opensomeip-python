"""Tests for opensomeip.message — Message dataclass."""

from __future__ import annotations

import pytest

from opensomeip.message import Message
from opensomeip.types import MessageId, MessageType, ProtocolVersion, RequestId, ReturnCode


class TestMessage:
    def test_default_construction(self) -> None:
        msg = Message()
        assert msg.message_id == MessageId(0, 0)
        assert msg.request_id == RequestId(0, 0)
        assert msg.message_type == MessageType.REQUEST
        assert msg.return_code == ReturnCode.E_OK
        assert msg.protocol_version == ProtocolVersion.VERSION_1
        assert msg.interface_version == 1
        assert msg.payload == b""

    def test_construction_with_values(self) -> None:
        mid = MessageId(service_id=0x1234, method_id=0x0001)
        rid = RequestId(client_id=0x0010, session_id=0x0001)
        msg = Message(
            message_id=mid,
            request_id=rid,
            message_type=MessageType.RESPONSE,
            return_code=ReturnCode.E_OK,
            payload=b"\xde\xad\xbe\xef",
        )
        assert msg.message_id == mid
        assert msg.request_id == rid
        assert msg.message_type == MessageType.RESPONSE
        assert msg.return_code == ReturnCode.E_OK
        assert msg.payload == b"\xde\xad\xbe\xef"

    def test_payload_is_bytes(self) -> None:
        msg = Message(payload=b"\x01\x02\x03")
        assert isinstance(msg.payload, bytes)

    def test_eq(self) -> None:
        mid = MessageId(service_id=0x1234, method_id=0x0001)
        a = Message(message_id=mid, payload=b"\x01")
        b = Message(message_id=mid, payload=b"\x01")
        assert a == b

    def test_ne_different_payload(self) -> None:
        mid = MessageId(service_id=0x1234, method_id=0x0001)
        a = Message(message_id=mid, payload=b"\x01")
        b = Message(message_id=mid, payload=b"\x02")
        assert a != b

    def test_ne_different_message_id(self) -> None:
        a = Message(message_id=MessageId(0x1234, 0x0001))
        b = Message(message_id=MessageId(0x5678, 0x0001))
        assert a != b

    def test_eq_not_message(self) -> None:
        msg = Message()
        assert msg != "not a message"
        assert msg.__eq__("not a message") is NotImplemented

    def test_repr_short_payload(self) -> None:
        msg = Message(
            message_id=MessageId(0x1234, 0x0001),
            payload=b"\x01\x02\x03",
        )
        r = repr(msg)
        assert "010203" in r
        assert "REQUEST" in r

    def test_repr_long_payload(self) -> None:
        msg = Message(payload=b"\xaa" * 32)
        r = repr(msg)
        assert "32 bytes" in r

    def test_invalid_interface_version(self) -> None:
        with pytest.raises(ValueError, match="interface_version"):
            Message(interface_version=0x100)

    def test_mutable_payload(self) -> None:
        msg = Message(payload=b"\x01")
        msg.payload = b"\x02\x03"
        assert msg.payload == b"\x02\x03"

    def test_mutable_message_type(self) -> None:
        msg = Message()
        msg.message_type = MessageType.RESPONSE
        assert msg.message_type == MessageType.RESPONSE


class TestMessageFromFixture:
    def test_fixture(self, sample_message: Message) -> None:
        assert sample_message.message_id.service_id == 0x1234
        assert sample_message.payload == b"\x01\x02\x03\x04"
