"""Tests for opensomeip.exceptions — exception hierarchy."""

from __future__ import annotations

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


class TestExceptionHierarchy:
    def test_base_is_exception(self) -> None:
        assert issubclass(SomeIpError, Exception)

    def test_transport_inherits_base(self) -> None:
        assert issubclass(TransportError, SomeIpError)

    def test_connection_inherits_transport(self) -> None:
        assert issubclass(ConnectionError, TransportError)

    def test_connection_lost_inherits_transport(self) -> None:
        assert issubclass(ConnectionLostError, TransportError)

    def test_serialization_inherits_base(self) -> None:
        assert issubclass(SerializationError, SomeIpError)

    def test_timeout_inherits_base(self) -> None:
        assert issubclass(TimeoutError, SomeIpError)

    def test_sd_inherits_base(self) -> None:
        assert issubclass(ServiceDiscoveryError, SomeIpError)

    def test_rpc_inherits_base(self) -> None:
        assert issubclass(RpcError, SomeIpError)

    def test_e2e_inherits_base(self) -> None:
        assert issubclass(E2EError, SomeIpError)

    def test_config_inherits_base(self) -> None:
        assert issubclass(ConfigurationError, SomeIpError)


class TestExceptionUsage:
    def test_raise_and_catch_base(self) -> None:
        try:
            raise TransportError("connection failed")
        except SomeIpError as e:
            assert str(e) == "connection failed"

    def test_raise_and_catch_specific(self) -> None:
        try:
            raise ConnectionLostError("peer disconnected")
        except ConnectionLostError as e:
            assert str(e) == "peer disconnected"

    def test_catch_transport_catches_connection(self) -> None:
        try:
            raise ConnectionError("refused")
        except TransportError:
            pass

    def test_message_preserved(self) -> None:
        err = RpcError("method not found")
        assert str(err) == "method not found"
