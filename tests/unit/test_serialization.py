"""Tests for opensomeip.serialization — Serializer and Deserializer."""

from __future__ import annotations

import math
import struct

import pytest

from opensomeip.serialization import Deserializer, Serializer


class TestSerializer:
    def test_empty(self) -> None:
        s = Serializer()
        assert s.to_bytes() == b""
        assert len(s) == 0

    def test_context_manager(self) -> None:
        with Serializer() as s:
            s.write_uint8(42)
        assert s.to_bytes() == b"\x2a"

    def test_write_bool(self) -> None:
        s = Serializer()
        s.write_bool(True)
        s.write_bool(False)
        assert s.to_bytes() == b"\x01\x00"

    def test_write_uint8(self) -> None:
        s = Serializer()
        s.write_uint8(0xFF)
        assert s.to_bytes() == b"\xff"

    def test_write_uint16(self) -> None:
        s = Serializer()
        s.write_uint16(0x1234)
        assert s.to_bytes() == struct.pack("!H", 0x1234)

    def test_write_uint32(self) -> None:
        s = Serializer()
        s.write_uint32(0x12345678)
        assert s.to_bytes() == struct.pack("!I", 0x12345678)

    def test_write_uint64(self) -> None:
        s = Serializer()
        s.write_uint64(0x123456789ABCDEF0)
        assert s.to_bytes() == struct.pack("!Q", 0x123456789ABCDEF0)

    def test_write_int8(self) -> None:
        s = Serializer()
        s.write_int8(-1)
        assert s.to_bytes() == b"\xff"

    def test_write_int16(self) -> None:
        s = Serializer()
        s.write_int16(-256)
        assert s.to_bytes() == struct.pack("!h", -256)

    def test_write_int32(self) -> None:
        s = Serializer()
        s.write_int32(-1)
        assert s.to_bytes() == b"\xff\xff\xff\xff"

    def test_write_int64(self) -> None:
        s = Serializer()
        s.write_int64(-1)
        assert s.to_bytes() == b"\xff" * 8

    def test_write_float32(self) -> None:
        s = Serializer()
        s.write_float32(1.0)
        assert s.to_bytes() == struct.pack("!f", 1.0)

    def test_write_float64(self) -> None:
        s = Serializer()
        s.write_float64(1.0)
        assert s.to_bytes() == struct.pack("!d", 1.0)

    def test_write_bytes(self) -> None:
        s = Serializer()
        s.write_bytes(b"\x01\x02\x03")
        data = s.to_bytes()
        assert data[:4] == struct.pack("!I", 3)
        assert data[4:] == b"\x01\x02\x03"

    def test_write_bytes_raw(self) -> None:
        s = Serializer()
        s.write_bytes_raw(b"\xde\xad")
        assert s.to_bytes() == b"\xde\xad"

    def test_write_string(self) -> None:
        s = Serializer()
        s.write_string("hi")
        data = s.to_bytes()
        length = struct.unpack("!I", data[:4])[0]
        assert length == 3  # "hi" + NUL
        assert data[4:7] == b"hi\x00"

    def test_reset(self) -> None:
        s = Serializer()
        s.write_uint8(1)
        s.reset()
        assert s.to_bytes() == b""
        assert len(s) == 0

    def test_len(self) -> None:
        s = Serializer()
        s.write_uint16(1)
        assert len(s) == 2


class TestDeserializer:
    def test_read_bool(self) -> None:
        d = Deserializer(b"\x01\x00")
        assert d.read_bool() is True
        assert d.read_bool() is False

    def test_read_uint8(self) -> None:
        d = Deserializer(b"\xff")
        assert d.read_uint8() == 0xFF

    def test_read_uint16(self) -> None:
        d = Deserializer(struct.pack("!H", 0x1234))
        assert d.read_uint16() == 0x1234

    def test_read_uint32(self) -> None:
        d = Deserializer(struct.pack("!I", 0x12345678))
        assert d.read_uint32() == 0x12345678

    def test_read_uint64(self) -> None:
        d = Deserializer(struct.pack("!Q", 0x123456789ABCDEF0))
        assert d.read_uint64() == 0x123456789ABCDEF0

    def test_read_int8(self) -> None:
        d = Deserializer(b"\xff")
        assert d.read_int8() == -1

    def test_read_int16(self) -> None:
        d = Deserializer(struct.pack("!h", -256))
        assert d.read_int16() == -256

    def test_read_int32(self) -> None:
        d = Deserializer(b"\xff\xff\xff\xff")
        assert d.read_int32() == -1

    def test_read_int64(self) -> None:
        d = Deserializer(b"\xff" * 8)
        assert d.read_int64() == -1

    def test_read_float32(self) -> None:
        d = Deserializer(struct.pack("!f", 3.14))
        assert math.isclose(d.read_float32(), 3.14, rel_tol=1e-6)

    def test_read_float64(self) -> None:
        d = Deserializer(struct.pack("!d", 3.14159265358979))
        assert math.isclose(d.read_float64(), 3.14159265358979, rel_tol=1e-15)

    def test_read_bytes(self) -> None:
        payload = struct.pack("!I", 3) + b"\x01\x02\x03"
        d = Deserializer(payload)
        assert d.read_bytes() == b"\x01\x02\x03"

    def test_read_bytes_raw(self) -> None:
        d = Deserializer(b"\xde\xad\xbe\xef")
        assert d.read_bytes_raw(2) == b"\xde\xad"
        assert d.read_bytes_raw(2) == b"\xbe\xef"

    def test_read_string(self) -> None:
        payload = struct.pack("!I", 3) + b"hi\x00"
        d = Deserializer(payload)
        assert d.read_string() == "hi"

    def test_remaining(self) -> None:
        d = Deserializer(b"\x01\x02\x03")
        assert d.remaining == 3
        d.read_uint8()
        assert d.remaining == 2

    def test_position(self) -> None:
        d = Deserializer(b"\x01\x02\x03")
        assert d.position == 0
        d.read_uint8()
        assert d.position == 1

    def test_read_past_end(self) -> None:
        d = Deserializer(b"\x01")
        with pytest.raises(ValueError, match="bytes remain"):
            d.read_uint16()

    def test_from_memoryview(self) -> None:
        data = memoryview(b"\x01\x02")
        d = Deserializer(data)
        assert d.read_uint8() == 1

    def test_from_bytearray(self) -> None:
        data = bytearray(b"\x01\x02")
        d = Deserializer(data)
        assert d.read_uint8() == 1


class TestRoundTrip:
    def test_uint8_roundtrip(self) -> None:
        s = Serializer()
        s.write_uint8(42)
        d = Deserializer(s.to_bytes())
        assert d.read_uint8() == 42

    def test_mixed_types_roundtrip(self) -> None:
        s = Serializer()
        s.write_uint16(1000)
        s.write_int32(-42)
        s.write_string("test")
        s.write_bytes(b"\xab\xcd")

        d = Deserializer(s.to_bytes())
        assert d.read_uint16() == 1000
        assert d.read_int32() == -42
        assert d.read_string() == "test"
        assert d.read_bytes() == b"\xab\xcd"
        assert d.remaining == 0
