"""Tests for opensomeip.types — enums, MessageId, RequestId."""

from __future__ import annotations

import pytest

from opensomeip.types import MessageId, MessageType, ProtocolVersion, RequestId, ReturnCode


class TestMessageType:
    def test_values(self) -> None:
        assert MessageType.REQUEST == 0x00
        assert MessageType.REQUEST_NO_RETURN == 0x01
        assert MessageType.NOTIFICATION == 0x02
        assert MessageType.RESPONSE == 0x80
        assert MessageType.ERROR == 0x81

    def test_tp_variants(self) -> None:
        assert MessageType.TP_REQUEST == 0x20
        assert MessageType.TP_REQUEST_NO_RETURN == 0x21
        assert MessageType.TP_NOTIFICATION == 0x22

    def test_is_int(self) -> None:
        assert isinstance(MessageType.REQUEST, int)

    def test_from_int(self) -> None:
        assert MessageType(0x80) is MessageType.RESPONSE


class TestReturnCode:
    def test_values(self) -> None:
        assert ReturnCode.E_OK == 0x00
        assert ReturnCode.E_NOT_OK == 0x01
        assert ReturnCode.E_UNKNOWN_SERVICE == 0x02
        assert ReturnCode.E_UNKNOWN_METHOD == 0x03
        assert ReturnCode.E_TIMEOUT == 0x06
        assert ReturnCode.E_MALFORMED_MESSAGE == 0x09

    def test_all_values_unique(self) -> None:
        values = [m.value for m in ReturnCode]
        assert len(values) == len(set(values))


class TestProtocolVersion:
    def test_version_1(self) -> None:
        assert ProtocolVersion.VERSION_1 == 0x01


class TestMessageId:
    def test_construction(self) -> None:
        mid = MessageId(service_id=0x1234, method_id=0x5678)
        assert mid.service_id == 0x1234
        assert mid.method_id == 0x5678

    def test_value_property(self) -> None:
        mid = MessageId(service_id=0x1234, method_id=0x5678)
        assert mid.value == 0x12345678

    def test_from_value(self) -> None:
        mid = MessageId.from_value(0x12345678)
        assert mid.service_id == 0x1234
        assert mid.method_id == 0x5678

    def test_roundtrip_value(self) -> None:
        original = MessageId(service_id=0xABCD, method_id=0xEF01)
        restored = MessageId.from_value(original.value)
        assert restored == original

    def test_eq(self) -> None:
        a = MessageId(service_id=0x1234, method_id=0x0001)
        b = MessageId(service_id=0x1234, method_id=0x0001)
        assert a == b

    def test_ne(self) -> None:
        a = MessageId(service_id=0x1234, method_id=0x0001)
        b = MessageId(service_id=0x1234, method_id=0x0002)
        assert a != b

    def test_hash(self) -> None:
        a = MessageId(service_id=0x1234, method_id=0x0001)
        b = MessageId(service_id=0x1234, method_id=0x0001)
        assert hash(a) == hash(b)
        assert {a, b} == {a}

    def test_frozen(self) -> None:
        mid = MessageId(service_id=0x1234, method_id=0x0001)
        with pytest.raises(AttributeError):
            mid.service_id = 0x5678  # type: ignore[misc]

    def test_repr(self) -> None:
        mid = MessageId(service_id=0x1234, method_id=0x0001)
        r = repr(mid)
        assert "0x1234" in r
        assert "0x0001" in r

    def test_invalid_service_id(self) -> None:
        with pytest.raises(ValueError, match="service_id"):
            MessageId(service_id=0x10000, method_id=0x0001)

    def test_invalid_method_id(self) -> None:
        with pytest.raises(ValueError, match="method_id"):
            MessageId(service_id=0x0001, method_id=-1)

    def test_zero(self) -> None:
        mid = MessageId(service_id=0, method_id=0)
        assert mid.value == 0

    def test_max(self) -> None:
        mid = MessageId(service_id=0xFFFF, method_id=0xFFFF)
        assert mid.value == 0xFFFFFFFF


class TestRequestId:
    def test_construction(self) -> None:
        rid = RequestId(client_id=0x0010, session_id=0x0001)
        assert rid.client_id == 0x0010
        assert rid.session_id == 0x0001

    def test_value_property(self) -> None:
        rid = RequestId(client_id=0x0010, session_id=0x0001)
        assert rid.value == 0x00100001

    def test_from_value(self) -> None:
        rid = RequestId.from_value(0x00100001)
        assert rid.client_id == 0x0010
        assert rid.session_id == 0x0001

    def test_roundtrip_value(self) -> None:
        original = RequestId(client_id=0xABCD, session_id=0xEF01)
        restored = RequestId.from_value(original.value)
        assert restored == original

    def test_eq(self) -> None:
        a = RequestId(client_id=0x0010, session_id=0x0001)
        b = RequestId(client_id=0x0010, session_id=0x0001)
        assert a == b

    def test_ne(self) -> None:
        a = RequestId(client_id=0x0010, session_id=0x0001)
        b = RequestId(client_id=0x0010, session_id=0x0002)
        assert a != b

    def test_hash(self) -> None:
        a = RequestId(client_id=0x0010, session_id=0x0001)
        b = RequestId(client_id=0x0010, session_id=0x0001)
        assert hash(a) == hash(b)

    def test_frozen(self) -> None:
        rid = RequestId(client_id=0x0010, session_id=0x0001)
        with pytest.raises(AttributeError):
            rid.client_id = 0x0020  # type: ignore[misc]

    def test_repr(self) -> None:
        rid = RequestId(client_id=0x0010, session_id=0x0001)
        r = repr(rid)
        assert "0x0010" in r
        assert "0x0001" in r

    def test_invalid_client_id(self) -> None:
        with pytest.raises(ValueError, match="client_id"):
            RequestId(client_id=0x10000, session_id=0x0001)

    def test_invalid_session_id(self) -> None:
        with pytest.raises(ValueError, match="session_id"):
            RequestId(client_id=0x0001, session_id=-1)
