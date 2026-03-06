"""SOME/IP Message dataclass — the primary data unit exchanged via the protocol."""

from __future__ import annotations

from dataclasses import dataclass, field

from opensomeip.types import MessageId, MessageType, ProtocolVersion, RequestId, ReturnCode


@dataclass(slots=True)
class Message:
    """A SOME/IP message.

    This is a pure-Python representation suitable for serialization across
    gRPC or any other transport.  The ``payload`` is plain ``bytes``.
    """

    message_id: MessageId = field(default_factory=lambda: MessageId(0, 0))
    request_id: RequestId = field(default_factory=lambda: RequestId(0, 0))
    message_type: MessageType = MessageType.REQUEST
    return_code: ReturnCode = ReturnCode.E_OK
    protocol_version: ProtocolVersion = ProtocolVersion.VERSION_1
    interface_version: int = 1
    payload: bytes = b""

    def __post_init__(self) -> None:
        if not (0 <= self.interface_version <= 0xFF):
            raise ValueError(f"interface_version must be 0..0xFF, got {self.interface_version:#x}")

    def __repr__(self) -> str:
        payload_preview = self.payload[:16].hex()
        if len(self.payload) > 16:
            payload_preview += f"...({len(self.payload)} bytes)"
        return (
            f"Message("
            f"message_id={self.message_id!r}, "
            f"request_id={self.request_id!r}, "
            f"type={self.message_type.name}, "
            f"rc={self.return_code.name}, "
            f"payload={payload_preview})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return NotImplemented
        return (
            self.message_id == other.message_id
            and self.request_id == other.request_id
            and self.message_type == other.message_type
            and self.return_code == other.return_code
            and self.protocol_version == other.protocol_version
            and self.interface_version == other.interface_version
            and self.payload == other.payload
        )
