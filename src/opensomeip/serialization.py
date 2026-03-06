"""Pythonic wrappers for SOME/IP serialization and deserialization.

Provides :class:`Serializer` and :class:`Deserializer` for encoding/decoding
SOME/IP payloads using the wire format (big-endian by default).
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


class Serializer:
    """Builds a SOME/IP payload by appending typed values.

    Can be used as a context manager — ``to_bytes()`` is called on exit.

    Example::

        with Serializer() as s:
            s.write_uint16(0x1234)
            s.write_string("hello")
        data = s.to_bytes()
    """

    def __init__(self) -> None:
        self._buf = bytearray()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def write_bool(self, value: bool) -> None:
        self._buf.append(1 if value else 0)

    def write_uint8(self, value: int) -> None:
        self._buf.append(value & 0xFF)

    def write_uint16(self, value: int) -> None:
        self._buf.extend(struct.pack("!H", value))

    def write_uint32(self, value: int) -> None:
        self._buf.extend(struct.pack("!I", value))

    def write_uint64(self, value: int) -> None:
        self._buf.extend(struct.pack("!Q", value))

    def write_int8(self, value: int) -> None:
        self._buf.extend(struct.pack("!b", value))

    def write_int16(self, value: int) -> None:
        self._buf.extend(struct.pack("!h", value))

    def write_int32(self, value: int) -> None:
        self._buf.extend(struct.pack("!i", value))

    def write_int64(self, value: int) -> None:
        self._buf.extend(struct.pack("!q", value))

    def write_float32(self, value: float) -> None:
        self._buf.extend(struct.pack("!f", value))

    def write_float64(self, value: float) -> None:
        self._buf.extend(struct.pack("!d", value))

    def write_bytes(self, value: bytes | bytearray | memoryview) -> None:
        """Write a length-prefixed byte blob (uint32 length + data)."""
        data = bytes(value)
        self.write_uint32(len(data))
        self._buf.extend(data)

    def write_bytes_raw(self, value: bytes | bytearray | memoryview) -> None:
        """Write raw bytes without a length prefix."""
        self._buf.extend(value)

    def write_string(self, value: str, encoding: str = "utf-8") -> None:
        """Write a length-prefixed string (uint32 length + BOM-less encoded + NUL)."""
        encoded = value.encode(encoding) + b"\x00"
        self.write_uint32(len(encoded))
        self._buf.extend(encoded)

    def to_bytes(self) -> bytes:
        """Return the serialized payload as ``bytes``."""
        return bytes(self._buf)

    def reset(self) -> None:
        """Clear the internal buffer."""
        self._buf.clear()

    def __len__(self) -> int:
        return len(self._buf)


class Deserializer:
    """Reads typed values from a SOME/IP payload.

    Example::

        d = Deserializer(payload)
        value = d.read_uint16()
        name = d.read_string()
    """

    def __init__(self, data: bytes | bytearray | memoryview) -> None:
        self._data = bytes(data)
        self._pos = 0

    @property
    def remaining(self) -> int:
        """Number of bytes remaining to be read."""
        return len(self._data) - self._pos

    @property
    def position(self) -> int:
        """Current read position."""
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

    def read_bool(self) -> bool:
        return self._read(1)[0] != 0

    def read_uint8(self) -> int:
        return self._read(1)[0]

    def read_uint16(self) -> int:
        result: int = struct.unpack("!H", self._read(2))[0]
        return result

    def read_uint32(self) -> int:
        result: int = struct.unpack("!I", self._read(4))[0]
        return result

    def read_uint64(self) -> int:
        result: int = struct.unpack("!Q", self._read(8))[0]
        return result

    def read_int8(self) -> int:
        result: int = struct.unpack("!b", self._read(1))[0]
        return result

    def read_int16(self) -> int:
        result: int = struct.unpack("!h", self._read(2))[0]
        return result

    def read_int32(self) -> int:
        result: int = struct.unpack("!i", self._read(4))[0]
        return result

    def read_int64(self) -> int:
        result: int = struct.unpack("!q", self._read(8))[0]
        return result

    def read_float32(self) -> float:
        result: float = struct.unpack("!f", self._read(4))[0]
        return result

    def read_float64(self) -> float:
        result: float = struct.unpack("!d", self._read(8))[0]
        return result

    def read_bytes(self) -> bytes:
        """Read a length-prefixed byte blob (uint32 length + data)."""
        length = self.read_uint32()
        return self._read(length)

    def read_bytes_raw(self, n: int) -> bytes:
        """Read exactly *n* raw bytes."""
        return self._read(n)

    def read_string(self, encoding: str = "utf-8") -> str:
        """Read a length-prefixed, NUL-terminated string."""
        length = self.read_uint32()
        raw = self._read(length)
        if raw and raw[-1:] == b"\x00":
            raw = raw[:-1]
        return raw.decode(encoding)
