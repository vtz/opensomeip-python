"""Core SOME/IP types: enums, MessageId, RequestId."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class MessageType(enum.IntEnum):
    """SOME/IP message type field values."""

    REQUEST = 0x00
    REQUEST_NO_RETURN = 0x01
    NOTIFICATION = 0x02
    REQUEST_ACK = 0x40
    RESPONSE = 0x80
    ERROR = 0x81
    RESPONSE_ACK = 0xC0
    ERROR_ACK = 0xC1
    TP_REQUEST = 0x20
    TP_REQUEST_NO_RETURN = 0x21
    TP_NOTIFICATION = 0x22


class ReturnCode(enum.IntEnum):
    """SOME/IP return code field values."""

    E_OK = 0x00
    E_NOT_OK = 0x01
    E_UNKNOWN_SERVICE = 0x02
    E_UNKNOWN_METHOD = 0x03
    E_NOT_READY = 0x04
    E_NOT_REACHABLE = 0x05
    E_TIMEOUT = 0x06
    E_WRONG_PROTOCOL_VERSION = 0x07
    E_WRONG_INTERFACE_VERSION = 0x08
    E_MALFORMED_MESSAGE = 0x09
    E_WRONG_MESSAGE_TYPE = 0x0A
    E_E2E_REPEATED = 0x0B
    E_E2E_WRONG_SEQUENCE = 0x0C
    E_E2E = 0x0D
    E_E2E_NOT_AVAILABLE = 0x0E
    E_E2E_NO_NEW_DATA = 0x0F


class ProtocolVersion(enum.IntEnum):
    """SOME/IP protocol version field values."""

    VERSION_1 = 0x01


@dataclass(frozen=True, slots=True)
class MessageId:
    """SOME/IP Message ID composed of service ID and method ID.

    The 32-bit Message ID is split as:
      - service_id: upper 16 bits
      - method_id: lower 16 bits
    """

    service_id: int
    method_id: int

    def __post_init__(self) -> None:
        if not (0 <= self.service_id <= 0xFFFF):
            raise ValueError(f"service_id must be 0..0xFFFF, got {self.service_id:#x}")
        if not (0 <= self.method_id <= 0xFFFF):
            raise ValueError(f"method_id must be 0..0xFFFF, got {self.method_id:#x}")

    @property
    def value(self) -> int:
        """Combined 32-bit message ID."""
        return (self.service_id << 16) | self.method_id

    @classmethod
    def from_value(cls, value: int) -> MessageId:
        """Construct from a combined 32-bit message ID."""
        return cls(service_id=(value >> 16) & 0xFFFF, method_id=value & 0xFFFF)

    def __repr__(self) -> str:
        return f"MessageId(service_id={self.service_id:#06x}, method_id={self.method_id:#06x})"


@dataclass(frozen=True, slots=True)
class RequestId:
    """SOME/IP Request ID composed of client ID and session ID.

    The 32-bit Request ID is split as:
      - client_id: upper 16 bits
      - session_id: lower 16 bits
    """

    client_id: int
    session_id: int

    def __post_init__(self) -> None:
        if not (0 <= self.client_id <= 0xFFFF):
            raise ValueError(f"client_id must be 0..0xFFFF, got {self.client_id:#x}")
        if not (0 <= self.session_id <= 0xFFFF):
            raise ValueError(f"session_id must be 0..0xFFFF, got {self.session_id:#x}")

    @property
    def value(self) -> int:
        """Combined 32-bit request ID."""
        return (self.client_id << 16) | self.session_id

    @classmethod
    def from_value(cls, value: int) -> RequestId:
        """Construct from a combined 32-bit request ID."""
        return cls(client_id=(value >> 16) & 0xFFFF, session_id=value & 0xFFFF)

    def __repr__(self) -> str:
        return f"RequestId(client_id={self.client_id:#06x}, session_id={self.session_id:#06x})"
