"""Tests for coverage gaps in _bridge, receiver, sd, transport, and tp modules."""

from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.sd import SdClient, SdConfig, SdServer
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, ReturnCode

# ---------------------------------------------------------------------------
# 1. _bridge.py — from_cpp_* functions
# ---------------------------------------------------------------------------


class TestBridgeFromCpp:
    def test_from_cpp_endpoint(self) -> None:
        from opensomeip._bridge import from_cpp_endpoint

        mock = SimpleNamespace(address="127.0.0.1", port=8080)
        ep = from_cpp_endpoint(mock)
        assert ep.ip == "127.0.0.1"
        assert ep.port == 8080

    def test_from_cpp_message_id(self) -> None:
        from opensomeip._bridge import from_cpp_message_id

        mock = SimpleNamespace(service_id=0x1234, method_id=0x0001)
        mid = from_cpp_message_id(mock)
        assert mid.service_id == 0x1234
        assert mid.method_id == 0x0001

    def test_from_cpp_request_id(self) -> None:
        from opensomeip._bridge import from_cpp_request_id

        mock = SimpleNamespace(client_id=0x0010, session_id=0x0001)
        rid = from_cpp_request_id(mock)
        assert rid.client_id == 0x0010
        assert rid.session_id == 0x0001

    def test_from_cpp_message(self) -> None:
        from opensomeip._bridge import from_cpp_message

        mock = SimpleNamespace(
            message_id=SimpleNamespace(service_id=0x1234, method_id=0x0001),
            request_id=SimpleNamespace(client_id=0x0010, session_id=0x0001),
            message_type=0,  # REQUEST
            return_code=0,  # E_OK
            interface_version=1,
            payload=b"test",
        )
        msg = from_cpp_message(mock)
        assert msg.message_id.service_id == 0x1234
        assert msg.message_id.method_id == 0x0001
        assert msg.request_id.client_id == 0x0010
        assert msg.request_id.session_id == 0x0001
        assert msg.message_type == MessageType.REQUEST
        assert msg.return_code == ReturnCode.E_OK
        assert msg.interface_version == 1
        assert msg.payload == b"test"

    def test_from_cpp_service_instance(self) -> None:
        from opensomeip._bridge import from_cpp_service_instance

        mock = SimpleNamespace(
            service_id=0x1234,
            instance_id=0x0001,
            major_version=2,
            minor_version=3,
        )
        svc = from_cpp_service_instance(mock)
        assert svc.service_id == 0x1234
        assert svc.instance_id == 0x0001
        assert svc.major_version == 2
        assert svc.minor_version == 3


# ---------------------------------------------------------------------------
# 2. receiver.py — _ensure_async_queue (no loop), _put_async fallback, __anext__
# ---------------------------------------------------------------------------


class TestReceiverCoverage:
    def test_ensure_async_queue_when_no_running_loop(self) -> None:
        """_ensure_async_queue sets _loop to None when get_running_loop raises."""
        r = MessageReceiver()
        # Call _ensure_async_queue from a thread (no running event loop)
        result: list[object] = []

        def in_thread() -> None:
            q = r._ensure_async_queue()
            result.append(q)
            result.append(r._loop)

        t = threading.Thread(target=in_thread)
        t.start()
        t.join()

        assert len(result) == 2
        assert result[0] is not None
        assert result[1] is None  # _loop is None when no running loop

    def test_put_async_fallback_when_no_loop(self) -> None:
        """_put_async fallback path when loop is None or not running."""
        r = MessageReceiver()
        # Initialize async queue without a running loop (so _loop is None)
        r._ensure_async_queue()
        assert r._loop is None
        # _put_async should use put_nowait fallback (lines 55-58)
        r._put_async(Message(payload=b"x"))
        # Verify message made it to async queue via fallback path
        r.close()
        # Run async consumer to drain the async queue
        collected: list[Message] = []

        async def consume() -> None:
            aiter = r.__aiter__()
            try:
                while True:
                    msg = await aiter.__anext__()
                    collected.append(msg)
            except StopAsyncIteration:
                pass

        asyncio.run(consume())
        assert len(collected) == 1
        assert collected[0].payload == b"x"

    def test_put_async_when_async_queue_none(self) -> None:
        """_put_async returns early when _async_queue is None."""
        r = MessageReceiver()
        # Never call _ensure_async_queue, so _async_queue stays None
        r._put_async(Message(payload=b"x"))  # should not raise
        assert r._async_queue is None

    @pytest.mark.asyncio
    async def test_anext_yields_messages(self) -> None:
        """__anext__ yields messages and raises StopAsyncIteration on sentinel."""
        r = MessageReceiver()
        aiter = r.__aiter__()
        r.put(Message(payload=b"first"))
        r.put(Message(payload=b"second"))
        r.close()

        msgs: list[Message] = []
        with pytest.raises(StopAsyncIteration):
            while True:
                msg = await aiter.__anext__()
                msgs.append(msg)

        assert len(msgs) == 2
        assert msgs[0].payload == b"first"
        assert msgs[1].payload == b"second"


# ---------------------------------------------------------------------------
# 3. sd.py — config, get_statistics, async context manager
# ---------------------------------------------------------------------------


@pytest.fixture()
def sd_config() -> SdConfig:
    return SdConfig(
        multicast_endpoint=Endpoint("239.1.1.1", 30490),
        unicast_endpoint=Endpoint("192.168.1.100", 30490),
    )


class TestSdCoverage:
    def test_sd_server_config_property(self, sd_config: SdConfig) -> None:
        server = SdServer(sd_config)
        assert server.config is sd_config

    def test_sd_server_get_statistics(self, sd_config: SdConfig) -> None:
        """get_statistics returns a value (None without C++, Statistics with)."""
        server = SdServer(sd_config)
        result = server.get_statistics()
        if server._cpp is None:
            assert result is None
        else:
            assert result is not None

    def test_sd_client_config_property(self, sd_config: SdConfig) -> None:
        client = SdClient(sd_config)
        assert client.config is sd_config

    def test_sd_client_get_statistics(self, sd_config: SdConfig) -> None:
        """get_statistics returns a value (None without C++, Statistics with)."""
        client = SdClient(sd_config)
        result = client.get_statistics()
        if client._cpp is None:
            assert result is None
        else:
            assert result is not None

    @pytest.mark.asyncio
    async def test_sd_client_async_context_manager(self, sd_config: SdConfig) -> None:
        """SdClient async context manager (__aenter__/__aexit__)."""
        async with SdClient(sd_config) as client:
            assert client.is_running is True
        assert client.is_running is False


# ---------------------------------------------------------------------------
# 4. transport.py — _NativeTransportListener (get_ext None), send source_endpoint
# ---------------------------------------------------------------------------


class TestTransportCoverage:
    def test_native_transport_listener_cpp_none_when_ext_unavailable(self) -> None:
        """_NativeTransportListener has _cpp=None when get_ext returns None."""
        with patch("opensomeip.transport.get_ext", return_value=None):
            from opensomeip.transport import _NativeTransportListener

            receiver = MessageReceiver()
            listener = _NativeTransportListener(receiver)
            assert listener.cpp is None

    def test_send_uses_source_endpoint_when_no_endpoint_or_remote(self) -> None:
        """send() uses message.source_endpoint when endpoint and remote are None."""
        t = UdpTransport(Endpoint("0.0.0.0", 0))
        t.start()
        mock_cpp = MagicMock()
        t._cpp = mock_cpp
        msg = Message(payload=b"test")
        msg.source_endpoint = Endpoint("192.168.1.1", 30490)
        mock_cpp_msg = MagicMock()
        mock_cpp_ep = MagicMock()
        with (
            patch("opensomeip.transport.to_cpp_message", return_value=mock_cpp_msg),
            patch("opensomeip.transport.to_cpp_endpoint", return_value=mock_cpp_ep),
        ):
            t.send(msg)
        mock_cpp.send_message.assert_called_once_with(mock_cpp_msg, mock_cpp_ep)
        t.stop()


# ---------------------------------------------------------------------------
# 5. tp.py — pure-Python large message segmentation, get_statistics
# ---------------------------------------------------------------------------


class TestTpCoverage:
    def test_send_large_message_pure_python_path(self) -> None:
        """Send message larger than MTU uses pure-Python segmentation when C++ unavailable."""
        t = UdpTransport(Endpoint("0.0.0.0", 0))
        t.start()
        tp = __import__("opensomeip.tp", fromlist=["TpManager"]).TpManager
        manager = tp(t, mtu=100)
        manager.start()
        with patch.object(manager, "_cpp", None), patch.object(t, "send"):
            msg = Message(
                message_id=MessageId(0x1234, 0x0001),
                payload=b"x" * 250,
            )
            manager.send(msg)
        manager.stop()
        t.stop()

    def test_get_statistics_returns_none(self) -> None:
        """get_statistics returns None when C++ extension is unavailable."""
        t = UdpTransport(Endpoint("0.0.0.0", 0))
        t.start()
        from opensomeip.tp import TpManager

        manager = TpManager(t)
        with patch.object(manager, "_cpp", None):
            result = manager.get_statistics()
            assert result is None
        t.stop()
