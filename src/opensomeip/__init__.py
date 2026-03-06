"""opensomeip — Python bindings for the opensomeip C++ SOME/IP stack."""

from __future__ import annotations

from opensomeip._version import __version__
from opensomeip.exceptions import (
    ConfigurationError,
    ConnectionError,
    ConnectionLostError,
    E2EError,
    RpcError,
    SerializationError,
    ServiceDiscoveryError,
    SomeIpError,
    TimeoutError,
    TransportError,
)
from opensomeip.message import Message
from opensomeip.types import (
    MessageId,
    MessageType,
    ProtocolVersion,
    RequestId,
    ReturnCode,
)

__all__ = [
    "__version__",
    "ConfigurationError",
    "ConnectionError",
    "ConnectionLostError",
    "E2EError",
    "Message",
    "MessageId",
    "MessageType",
    "ProtocolVersion",
    "RequestId",
    "ReturnCode",
    "RpcError",
    "SerializationError",
    "ServiceDiscoveryError",
    "SomeIpError",
    "TimeoutError",
    "TransportError",
]
