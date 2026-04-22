"""Tests for opensomeip.transport — Transport, UdpTransport, TcpTransport."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from opensomeip.exceptions import TransportError
from opensomeip.message import Message
from opensomeip.transport import Endpoint, TcpTransport, UdpTransport


class TestEndpoint:
    def test_construction(self) -> None:
        ep = Endpoint(ip="127.0.0.1", port=30490)
        assert ep.ip == "127.0.0.1"
        assert ep.port == 30490

    def test_frozen(self) -> None:
        ep = Endpoint(ip="127.0.0.1", port=30490)
        with pytest.raises(AttributeError):
            ep.port = 1234  # type: ignore[misc]

    def test_invalid_port(self) -> None:
        with pytest.raises(ValueError, match="port"):
            Endpoint(ip="0.0.0.0", port=70000)

    def test_repr(self) -> None:
        ep = Endpoint(ip="10.0.0.1", port=1234)
        assert "10.0.0.1" in repr(ep)
        assert "1234" in repr(ep)


class TestUdpTransport:
    def test_construction(self) -> None:
        local = Endpoint("0.0.0.0", 30490)
        remote = Endpoint("192.168.1.1", 30490)
        t = UdpTransport(local, remote)
        assert t.local_endpoint == local
        assert t.remote_endpoint == remote

    def test_start_stop(self) -> None:
        t = UdpTransport(Endpoint("0.0.0.0", 0))
        assert t.is_running is False
        t.start()
        assert t.is_running is True
        t.stop()
        assert t.is_running is False

    def test_context_manager(self) -> None:
        t = UdpTransport(Endpoint("0.0.0.0", 0))
        with t:
            assert t.is_running is True
        assert t.is_running is False

    def test_send_when_not_running(self) -> None:
        t = UdpTransport(Endpoint("0.0.0.0", 0))
        with pytest.raises(TransportError, match="not running"):
            t.send(Message())

    def test_send_raises_without_native(self) -> None:
        """send() raises TransportError when the C++ extension is unavailable."""
        with patch("opensomeip.transport.get_ext", return_value=None):
            t = UdpTransport(Endpoint("0.0.0.0", 0))
            t.start()
            with pytest.raises(TransportError, match="native transport is not available"):
                t.send(Message())
            t.stop()

    def test_multicast_group(self) -> None:
        t = UdpTransport(Endpoint("0.0.0.0", 0), multicast_group="239.1.1.1")
        assert t.multicast_group == "239.1.1.1"

    def test_receiver_closed_on_stop(self) -> None:
        t = UdpTransport(Endpoint("0.0.0.0", 0))
        t.start()
        assert t.receiver.closed is False
        t.stop()
        assert t.receiver.closed is True

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        t = UdpTransport(Endpoint("0.0.0.0", 0))
        async with t:
            assert t.is_running is True
        assert t.is_running is False


class TestTcpTransport:
    def test_construction(self) -> None:
        t = TcpTransport(Endpoint("0.0.0.0", 0), Endpoint("192.168.1.1", 30490))
        assert t.is_connected is False

    def test_start_auto_connects(self) -> None:
        t = TcpTransport(Endpoint("0.0.0.0", 0), Endpoint("192.168.1.1", 30490))
        t.start()
        assert t.is_running is True
        assert t.is_connected is True
        t.stop()
        assert t.is_connected is False

    def test_connect_without_remote(self) -> None:
        t = TcpTransport(Endpoint("0.0.0.0", 0))
        with pytest.raises(TransportError, match="No remote"):
            t.connect()

    def test_context_manager(self) -> None:
        t = TcpTransport(Endpoint("0.0.0.0", 0), Endpoint("192.168.1.1", 30490))
        with t:
            assert t.is_connected is True
        assert t.is_connected is False

    def test_idempotent_start(self) -> None:
        t = TcpTransport(Endpoint("0.0.0.0", 0), Endpoint("192.168.1.1", 30490))
        t.start()
        t.start()  # idempotent
        assert t.is_running is True
        t.stop()
