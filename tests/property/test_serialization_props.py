"""Hypothesis property-based tests for serialization round-trips."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from opensomeip.serialization import Deserializer, Serializer


@given(st.booleans())
def test_bool_roundtrip(value: bool) -> None:
    s = Serializer()
    s.write_bool(value)
    d = Deserializer(s.to_bytes())
    assert d.read_bool() is value


@given(st.integers(min_value=0, max_value=0xFF))
def test_uint8_roundtrip(value: int) -> None:
    s = Serializer()
    s.write_uint8(value)
    d = Deserializer(s.to_bytes())
    assert d.read_uint8() == value


@given(st.integers(min_value=0, max_value=0xFFFF))
def test_uint16_roundtrip(value: int) -> None:
    s = Serializer()
    s.write_uint16(value)
    d = Deserializer(s.to_bytes())
    assert d.read_uint16() == value


@given(st.integers(min_value=0, max_value=0xFFFFFFFF))
def test_uint32_roundtrip(value: int) -> None:
    s = Serializer()
    s.write_uint32(value)
    d = Deserializer(s.to_bytes())
    assert d.read_uint32() == value


@given(st.integers(min_value=0, max_value=0xFFFFFFFFFFFFFFFF))
def test_uint64_roundtrip(value: int) -> None:
    s = Serializer()
    s.write_uint64(value)
    d = Deserializer(s.to_bytes())
    assert d.read_uint64() == value


@given(st.integers(min_value=-128, max_value=127))
def test_int8_roundtrip(value: int) -> None:
    s = Serializer()
    s.write_int8(value)
    d = Deserializer(s.to_bytes())
    assert d.read_int8() == value


@given(st.integers(min_value=-32768, max_value=32767))
def test_int16_roundtrip(value: int) -> None:
    s = Serializer()
    s.write_int16(value)
    d = Deserializer(s.to_bytes())
    assert d.read_int16() == value


@given(st.integers(min_value=-(2**31), max_value=2**31 - 1))
def test_int32_roundtrip(value: int) -> None:
    s = Serializer()
    s.write_int32(value)
    d = Deserializer(s.to_bytes())
    assert d.read_int32() == value


@given(st.integers(min_value=-(2**63), max_value=2**63 - 1))
def test_int64_roundtrip(value: int) -> None:
    s = Serializer()
    s.write_int64(value)
    d = Deserializer(s.to_bytes())
    assert d.read_int64() == value


@given(st.floats(allow_nan=False, allow_infinity=False, width=32))
def test_float32_roundtrip(value: float) -> None:
    s = Serializer()
    s.write_float32(value)
    d = Deserializer(s.to_bytes())
    result = d.read_float32()
    if value == 0.0:
        assert result == 0.0
    else:
        assert abs(result - value) / abs(value) < 1e-6


@given(st.floats(allow_nan=False, allow_infinity=False, width=64))
def test_float64_roundtrip(value: float) -> None:
    s = Serializer()
    s.write_float64(value)
    d = Deserializer(s.to_bytes())
    assert d.read_float64() == value


@given(st.binary(max_size=1024))
def test_bytes_roundtrip(value: bytes) -> None:
    s = Serializer()
    s.write_bytes(value)
    d = Deserializer(s.to_bytes())
    assert d.read_bytes() == value


@given(st.text(max_size=256))
def test_string_roundtrip(value: str) -> None:
    s = Serializer()
    s.write_string(value)
    d = Deserializer(s.to_bytes())
    assert d.read_string() == value
