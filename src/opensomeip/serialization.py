"""Pythonic wrappers for SOME/IP serialization and deserialization.

When the C++ extension is available, delegates to the native Serializer
and Deserializer for primitive types. Composite types (bytes, strings)
use the C++ primitives to ensure buffer consistency.
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip._bridge import get_ext


class Serializer:
    """Builds a SOME/IP payload by appending typed values.

    When the C++ extension is available, delegates to the native
    ``_opensomeip.Serializer`` for spec-compliant big-endian serialization.

    Can be used as a context manager::

        with Serializer() as s:
            s.write_uint16(0x1234)
            s.write_string("hello")
        data = s.to_bytes()
    """

    def __init__(self) -> None:
        self._buf = bytearray()
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            self._cpp = ext.Serializer()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def write_bool(self, value: bool) -> None:
        if self._cpp is not None:
            self._cpp.serialize_bool(value)
            return
        self._buf.append(1 if value else 0)

    def write_uint8(self, value: int) -> None:
        if self._cpp is not None:
            self._cpp.serialize_uint8(value)
            return
        self._buf.append(value & 0xFF)

    def write_uint16(self, value: int) -> None:
        if self._cpp is not None:
            self._cpp.serialize_uint16(value)
            return
        self._buf.extend(struct.pack("!H", value))

    def write_uint32(self, value: int) -> None:
        if self._cpp is not None:
            self._cpp.serialize_uint32(value)
            return
        self._buf.extend(struct.pack("!I", value))

    def write_uint64(self, value: int) -> None:
        if self._cpp is not None:
            self._cpp.serialize_uint64(value)
            return
        self._buf.extend(struct.pack("!Q", value))

    def write_int8(self, value: int) -> None:
        if self._cpp is not None:
            self._cpp.serialize_int8(value)
            return
        self._buf.extend(struct.pack("!b", value))

    def write_int16(self, value: int) -> None:
        if self._cpp is not None:
            self._cpp.serialize_int16(value)
            return
        self._buf.extend(struct.pack("!h", value))

    def write_int32(self, value: int) -> None:
        if self._cpp is not None:
            self._cpp.serialize_int32(value)
            return
        self._buf.extend(struct.pack("!i", value))

    def write_int64(self, value: int) -> None:
        if self._cpp is not None:
            self._cpp.serialize_int64(value)
            return
        self._buf.extend(struct.pack("!q", value))

    def write_float32(self, value: float) -> None:
        if self._cpp is not None:
            self._cpp.serialize_float(value)
            return
        self._buf.extend(struct.pack("!f", value))

    def write_float64(self, value: float) -> None:
        if self._cpp is not None:
            self._cpp.serialize_double(value)
            return
        self._buf.extend(struct.pack("!d", value))

    def write_bytes(self, value: bytes | bytearray | memoryview) -> None:
        """Write a length-prefixed byte blob (uint32 length + data)."""
        data = bytes(value)
        self.write_uint32(len(data))
        self.write_bytes_raw(data)

    def write_bytes_raw(self, value: bytes | bytearray | memoryview) -> None:
        """Write raw bytes without a length prefix."""
        if self._cpp is not None:
            for b in value:
                self._cpp.serialize_uint8(b)
            return
        self._buf.extend(value)

    def write_string(self, value: str, encoding: str = "utf-8") -> None:
        """Write a length-prefixed string (uint32 length + encoded + NUL)."""
        encoded = value.encode(encoding) + b"\x00"
        self.write_uint32(len(encoded))
        self.write_bytes_raw(encoded)

    def to_bytes(self) -> bytes:
        """Return the serialized payload as ``bytes``."""
        if self._cpp is not None:
            return bytes(self._cpp.get_buffer())
        return bytes(self._buf)

    def reset(self) -> None:
        """Clear the internal buffer."""
        if self._cpp is not None:
            self._cpp.reset()
        self._buf.clear()

    def __len__(self) -> int:
        if self._cpp is not None:
            return int(self._cpp.get_size())
        return len(self._buf)


class Deserializer:
    """Reads typed values from a SOME/IP payload.

    When the C++ extension is available, delegates to the native
    ``_opensomeip.Deserializer`` for spec-compliant deserialization.

    Example::

        d = Deserializer(payload)
        value = d.read_uint16()
        name = d.read_string()
    """

    def __init__(self, data: bytes | bytearray | memoryview) -> None:
        self._data = bytes(data)
        self._pos = 0
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            self._cpp = ext.Deserializer(self._data)

    @property
    def remaining(self) -> int:
        """Number of bytes remaining to be read."""
        if self._cpp is not None:
            return int(self._cpp.get_remaining())
        return len(self._data) - self._pos

    @property
    def position(self) -> int:
        """Current read position."""
        if self._cpp is not None:
            return int(self._cpp.get_position())
        return self._pos

    def _read(self, n: int) -> bytes:
        if self._pos + n > len(self._data):
            raise ValueError(
                f"Attempt to read {n} bytes at position {self._pos}, "
                f"but only {self.remaining} bytes remain"
            )
        result = self._data[self._pos : self._pos + n]
        self._pos += n
        return result

    def _cpp_call(self, method_name: str) -> Any:
        """Call a C++ deserializer method, converting errors to ValueError."""
        try:
            return getattr(self._cpp, method_name)()
        except Exception as e:
            raise ValueError(str(e)) from e

    def read_bool(self) -> bool:
        if self._cpp is not None:
            return bool(self._cpp_call("deserialize_bool"))
        return self._read(1)[0] != 0

    def read_uint8(self) -> int:
        if self._cpp is not None:
            return int(self._cpp_call("deserialize_uint8"))
        return self._read(1)[0]

    def read_uint16(self) -> int:
        if self._cpp is not None:
            return int(self._cpp_call("deserialize_uint16"))
        result: int = struct.unpack("!H", self._read(2))[0]
        return result

    def read_uint32(self) -> int:
        if self._cpp is not None:
            return int(self._cpp_call("deserialize_uint32"))
        result: int = struct.unpack("!I", self._read(4))[0]
        return result

    def read_uint64(self) -> int:
        if self._cpp is not None:
            return int(self._cpp_call("deserialize_uint64"))
        result: int = struct.unpack("!Q", self._read(8))[0]
        return result

    def read_int8(self) -> int:
        if self._cpp is not None:
            return int(self._cpp_call("deserialize_int8"))
        result: int = struct.unpack("!b", self._read(1))[0]
        return result

    def read_int16(self) -> int:
        if self._cpp is not None:
            return int(self._cpp_call("deserialize_int16"))
        result: int = struct.unpack("!h", self._read(2))[0]
        return result

    def read_int32(self) -> int:
        if self._cpp is not None:
            return int(self._cpp_call("deserialize_int32"))
        result: int = struct.unpack("!i", self._read(4))[0]
        return result

    def read_int64(self) -> int:
        if self._cpp is not None:
            return int(self._cpp_call("deserialize_int64"))
        result: int = struct.unpack("!q", self._read(8))[0]
        return result

    def read_float32(self) -> float:
        if self._cpp is not None:
            return float(self._cpp_call("deserialize_float"))
        result: float = struct.unpack("!f", self._read(4))[0]
        return result

    def read_float64(self) -> float:
        if self._cpp is not None:
            return float(self._cpp_call("deserialize_double"))
        result: float = struct.unpack("!d", self._read(8))[0]
        return result

    def read_bytes(self) -> bytes:
        """Read a length-prefixed byte blob (uint32 length + data)."""
        length = self.read_uint32()
        return bytes(self.read_uint8() for _ in range(length))

    def read_bytes_raw(self, n: int) -> bytes:
        """Read exactly *n* raw bytes."""
        if self._cpp is not None:
            return bytes(self._cpp_call("deserialize_uint8") for _ in range(n))
        return self._read(n)

    def read_string(self, encoding: str = "utf-8") -> str:
        """Read a length-prefixed, NUL-terminated string."""
        length = self.read_uint32()
        raw = bytes(self.read_uint8() for _ in range(length))
        if raw and raw[-1:] == b"\x00":
            raw = raw[:-1]
        return raw.decode(encoding)
