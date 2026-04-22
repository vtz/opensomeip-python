"""Tests for opensomeip.rpc — RpcClient, RpcServer."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from opensomeip.exceptions import RpcError
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.rpc import ResponseSender, RpcClient, RpcServer
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode


@pytest.fixture()
def transport() -> UdpTransport:
    t = UdpTransport(Endpoint("0.0.0.0", 0))
    t.start()
    return t


class TestRpcClient:
    def test_lifecycle(self, transport: UdpTransport) -> None:
        client = RpcClient(transport)
        assert client.is_running is False
        client.start()
        assert client.is_running is True
        client.stop()
        assert client.is_running is False

    def test_context_manager(self, transport: UdpTransport) -> None:
        with RpcClient(transport) as client:
            assert client.is_running is True
        assert client.is_running is False

    def test_call_when_not_running(self, transport: UdpTransport) -> None:
        client = RpcClient(transport)
        with pytest.raises(RpcError, match="not running"):
            client.call(MessageId(0x1234, 0x0001))

    def test_call_raises_without_native(self, transport: UdpTransport) -> None:
        """call() raises RpcError when the C++ extension is unavailable."""
        with patch("opensomeip.rpc.get_ext", return_value=None):
            client = RpcClient(transport)
            client.start()
            with pytest.raises(RpcError, match="C\\+\\+ extension is not available"):
                client.call(MessageId(0x1234, 0x0001), payload=b"\x01")
            client.stop()

    def test_call_propagates_cpp_exception(self, transport: UdpTransport) -> None:
        """call() wraps native exceptions in RpcError."""
        mock_ext = MagicMock()
        mock_ext.rpc.RpcClient.return_value = MagicMock()
        mock_ext.rpc.RpcTimeout.return_value = MagicMock()
        mock_ext.rpc.RpcClient.return_value.call_method_sync.side_effect = OSError(
            "connection refused"
        )

        with patch("opensomeip.rpc.get_ext", return_value=mock_ext):
            client = RpcClient(transport)
            client.start()
            with pytest.raises(RpcError, match="connection refused"):
                client.call(MessageId(0x1234, 0x0001))
            client.stop()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, transport: UdpTransport) -> None:
        async with RpcClient(transport) as client:
            assert client.is_running is True

    @pytest.mark.asyncio
    async def test_call_async_when_not_running(self, transport: UdpTransport) -> None:
        client = RpcClient(transport)
        with pytest.raises(RpcError, match="not running"):
            await client.call_async(MessageId(0x1234, 0x0001))

    @pytest.mark.asyncio
    async def test_call_async_raises_without_native(self, transport: UdpTransport) -> None:
        """call_async() raises RpcError when the C++ extension is unavailable."""
        with patch("opensomeip.rpc.get_ext", return_value=None):
            client = RpcClient(transport)
            client.start()
            with pytest.raises(RpcError, match="C\\+\\+ extension is not available"):
                await client.call_async(MessageId(0x1234, 0x0001), timeout=0.1)
            client.stop()

    def test_get_statistics_returns_none_without_cpp(self, transport: UdpTransport) -> None:
        """Test get_statistics returns None when C++ extension is unavailable."""
        with patch("opensomeip.rpc.get_ext", return_value=None):
            client = RpcClient(transport)
            assert client.get_statistics() is None


class TestResponseSender:
    """Test ResponseSender.send()."""

    def test_send_calls_server_send_response(self, transport: UdpTransport) -> None:
        mock_server = MagicMock(spec=RpcServer)
        mock_server._transport = transport
        request = Message(
            message_id=MessageId(0x1234, 0x0001),
            request_id=RequestId(client_id=0x0001, session_id=1),
            message_type=MessageType.REQUEST,
            payload=b"req",
        )
        sender = ResponseSender(_request=request, _server=mock_server)
        sender.send(b"response", return_code=ReturnCode.E_OK)
        mock_server._send_response.assert_called_once()
        call_args = mock_server._send_response.call_args[0][0]
        assert call_args.message_type == MessageType.RESPONSE
        assert call_args.payload == b"response"
        assert call_args.return_code == ReturnCode.E_OK
        assert call_args.message_id == request.message_id
        assert call_args.request_id == request.request_id

    def test_send_triggers_server_send_response_with_real_server(
        self, transport: UdpTransport
    ) -> None:
        """Test ResponseSender.send triggers RpcServer._send_response (line 304)."""
        server = RpcServer(transport)
        server.start()
        request = Message(
            message_id=MessageId(0x1234, 0x0001),
            request_id=RequestId(client_id=0x0001, session_id=1),
            message_type=MessageType.REQUEST,
            payload=b"req",
        )
        sender = ResponseSender(_request=request, _server=server)
        with patch.object(transport, "send") as mock_send:
            sender.send(b"response")
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args.message_type == MessageType.RESPONSE
            assert call_args.payload == b"response"


class TestRpcServer:
    def test_lifecycle(self, transport: UdpTransport) -> None:
        server = RpcServer(transport)
        assert server.is_running is False
        server.start()
        assert server.is_running is True
        server.stop()
        assert server.is_running is False

    def test_context_manager(self, transport: UdpTransport) -> None:
        with RpcServer(transport) as server:
            assert server.is_running is True
        assert server.is_running is False

    def test_register_handler(self, transport: UdpTransport) -> None:
        server = RpcServer(transport)
        method = MessageId(0x1234, 0x0001)

        def handler(req: Message) -> Message:
            return Message(payload=b"ok")

        server.register_handler(method, handler)

    def test_register_async_handler(self, transport: UdpTransport) -> None:
        server = RpcServer(transport)
        method = MessageId(0x1234, 0x0001)

        async def handler(req: Message) -> Message:
            return Message(payload=b"ok")

        server.register_async_handler(method, handler)

    def test_incoming_requests_returns_receiver(self, transport: UdpTransport) -> None:
        server = RpcServer(transport)
        method = MessageId(0x1234, 0x0001)
        receiver = server.incoming_requests(method)
        assert isinstance(receiver, MessageReceiver)

    def test_stop_closes_request_receivers(self, transport: UdpTransport) -> None:
        server = RpcServer(transport)
        method = MessageId(0x1234, 0x0001)
        receiver = server.incoming_requests(method)
        server.start()
        server.stop()
        assert receiver.closed is True

    def test_get_statistics_returns_none_without_cpp(self, transport: UdpTransport) -> None:
        """Test get_statistics returns None when C++ extension is unavailable."""
        with patch("opensomeip.rpc.get_ext", return_value=None):
            server = RpcServer(transport)
            assert server.get_statistics() is None

    @pytest.mark.asyncio
    async def test_async_context_manager(self, transport: UdpTransport) -> None:
        """Test async __aenter__ and __aexit__ (lines 325-326, 334)."""
        async with RpcServer(transport) as server:
            assert server.is_running is True
        assert server.is_running is False
