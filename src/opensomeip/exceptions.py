"""Exception hierarchy for opensomeip.

All exceptions inherit from :class:`SomeIpError`. This module is pure Python
so it can be imported for type-checking even without the compiled extension.
"""

from __future__ import annotations


class SomeIpError(Exception):
    """Base exception for all opensomeip errors."""


class TransportError(SomeIpError):
    """Error related to SOME/IP transport operations."""


class ConnectionError(TransportError):
    """Failed to establish a transport connection."""


class ConnectionLostError(TransportError):
    """An established transport connection was lost."""


class SerializationError(SomeIpError):
    """Error during SOME/IP payload serialization or deserialization."""


class TimeoutError(SomeIpError):
    """A SOME/IP operation timed out."""


class ServiceDiscoveryError(SomeIpError):
    """Error related to SOME/IP Service Discovery."""


class RpcError(SomeIpError):
    """Error during a SOME/IP RPC call."""


class E2EError(SomeIpError):
    """Error related to E2E (End-to-End) protection."""


class ConfigurationError(SomeIpError):
    """Invalid configuration provided to an opensomeip component."""
