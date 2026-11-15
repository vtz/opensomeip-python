"""Tests for opensomeip.rpc — RpcClient, RpcServer."""

from __future__ import annotations

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

    def test_service_ids_attach_demux_and_adapt_handler(self) -> None:
        socket = UdpTransport(Endpoint("127.0.0.1", 0))
        native_socket = MagicMock()
        socket._cpp = native_socket
        demux = MagicMock()
        first = MagicMock()
        second = MagicMock()
        first.initialize.return_value = True
        second.initialize.return_value = True
        ext = MagicMock()
        ext.ServiceDemux.return_value = demux
        ext.rpc.RpcServer.side_effect = [first, second]
        ext.rpc.RpcResult.SUCCESS = "ok"
        ext.rpc.RpcResult.INTERNAL_ERROR = "err"

        with (
            patch("opensomeip.rpc.get_ext", return_value=ext),
            patch("opensomeip.transport.get_ext", return_value=ext),
        ):
            server = RpcServer(socket, service_ids=[0x1234, 0x2222])
            server.start()

            def echo(req: Message) -> Message:
                return Message(
                    message_id=req.message_id,
                    request_id=req.request_id,
                    payload=req.payload,
                )

            def fail(req: Message) -> Message:
                return Message(payload=b"", return_code=ReturnCode.E_NOT_OK)

            server.register_handler(MessageId(0x1234, 0x0001), echo)
            server.register_handler(MessageId(0x2222, 0x0002), fail)
            with pytest.raises(RpcError, match="not configured"):
                server.register_handler(MessageId(0x9999, 0x0003), echo)

        ext.ServiceDemux.assert_called_once_with(native_socket)
        assert ext.rpc.RpcServer.call_count == 2
        first.initialize.assert_called()
        second.initialize.assert_called()
        echo_handler = first.register_method.call_args.args[1]
        code, payload = echo_handler(0x0001, 7, b"\x01\x02")
        assert code == "ok"
        assert payload == b"\x01\x02"
        fail_handler = second.register_method.call_args.args[1]
        fail_code, fail_payload = fail_handler(1, 1, b"")
        assert fail_code == "err"
        assert fail_payload == b""
        first.register_method.assert_called_once()
        second.register_method.assert_called_once()
        assert server.is_running is True
        server.stop()
        first.shutdown.assert_called()
        second.shutdown.assert_called()

    def test_ephemeral_initialize_error_is_ignored(self, transport: UdpTransport) -> None:
        ext = MagicMock()
        ext.rpc.RpcServer.return_value.initialize.side_effect = OSError("bind")
        with patch("opensomeip.rpc.get_ext", return_value=ext):
            server = RpcServer(transport)
            server.start()
            assert server.is_running is True
            server.stop()

    def test_demux_initialize_error_propagates(self) -> None:
        socket = UdpTransport(Endpoint("127.0.0.1", 0))
        socket._cpp = MagicMock()
        ext = MagicMock()
        ext.ServiceDemux.return_value = MagicMock()
        ext.rpc.RpcServer.return_value.initialize.side_effect = OSError("bind")
        with (
            patch("opensomeip.rpc.get_ext", return_value=ext),
            patch("opensomeip.transport.get_ext", return_value=ext),
        ):
            server = RpcServer(socket, service_ids=[0x1234])
            with pytest.raises(OSError, match="bind"):
                server.start()

    def test_demux_partial_startup_shuts_down_registered_servers(self) -> None:
        socket = UdpTransport(Endpoint("127.0.0.1", 0))
        socket._cpp = MagicMock()
        first = MagicMock()
        second = MagicMock()
        first.initialize.return_value = True
        first.shutdown.side_effect = OSError("rollback")
        second.initialize.return_value = False
        ext = MagicMock()
        ext.ServiceDemux.return_value = MagicMock()
        ext.rpc.RpcServer.side_effect = [first, second]
        with (
            patch("opensomeip.rpc.get_ext", return_value=ext),
            patch("opensomeip.transport.get_ext", return_value=ext),
        ):
            server = RpcServer(socket, service_ids=[0x1234, 0x2222])
            with pytest.raises(RpcError, match="service demux"):
                server.start()
        first.shutdown.assert_called_once()
        second.shutdown.assert_not_called()
        assert server.is_running is False

    def test_demux_startup_exception_shuts_down_registered_servers(self) -> None:
        socket = UdpTransport(Endpoint("127.0.0.1", 0))
        socket._cpp = MagicMock()
        first = MagicMock()
        second = MagicMock()
        first.initialize.return_value = True
        second.initialize.side_effect = OSError("bind")
        ext = MagicMock()
        ext.ServiceDemux.return_value = MagicMock()
        ext.rpc.RpcServer.side_effect = [first, second]
        with (
            patch("opensomeip.rpc.get_ext", return_value=ext),
            patch("opensomeip.transport.get_ext", return_value=ext),
        ):
            server = RpcServer(socket, service_ids=[0x1234, 0x2222])
            with pytest.raises(OSError, match="bind"):
                server.start()
        first.shutdown.assert_called_once()
        assert server.is_running is False

    def test_demux_registration_failure_raises(self) -> None:
        socket = UdpTransport(Endpoint("127.0.0.1", 0))
        socket._cpp = MagicMock()
        ext = MagicMock()
        ext.ServiceDemux.return_value = MagicMock()
        ext.rpc.RpcServer.return_value.initialize.return_value = False
        with (
            patch("opensomeip.rpc.get_ext", return_value=ext),
            patch("opensomeip.transport.get_ext", return_value=ext),
        ):
            server = RpcServer(socket, service_ids=[0x1234])
            with pytest.raises(RpcError, match="service demux"):
                server.start()

    def test_demux_shutdown_error_is_raised_after_receivers_close(self) -> None:
        socket = UdpTransport(Endpoint("127.0.0.1", 0))
        socket._cpp = MagicMock()
        ext = MagicMock()
        ext.ServiceDemux.return_value = MagicMock()
        native = ext.rpc.RpcServer.return_value
        native.initialize.return_value = True
        native.shutdown.side_effect = OSError("closed")
        with (
            patch("opensomeip.rpc.get_ext", return_value=ext),
            patch("opensomeip.transport.get_ext", return_value=ext),
        ):
            server = RpcServer(socket, service_ids=[0x1234])
            receiver = server.incoming_requests(MessageId(0x1234, 0x0001))
            server.start()
            with pytest.raises(OSError, match="closed"):
                server.stop()
        assert receiver.closed is True

    def test_ephemeral_server_registers_handler_for_another_service(self) -> None:
        socket = UdpTransport(Endpoint("127.0.0.1", 0))
        native = MagicMock()
        ext = MagicMock()
        ext.rpc.RpcServer.return_value = native
        ext.rpc.RpcResult.SUCCESS = "ok"
        ext.rpc.RpcResult.INTERNAL_ERROR = "err"

        def echo(req: Message) -> Message:
            return Message(payload=b"ok")

        with patch("opensomeip.rpc.get_ext", return_value=ext):
            server = RpcServer(socket)
            server.register_handler(MessageId(0x1234, 0x0001), echo)

        native.register_method.assert_called_once()
        assert native.register_method.call_args.args[0] == 0x0001

    def test_service_ids_without_native_socket_stay_on_ephemeral_port(self) -> None:
        socket = UdpTransport(Endpoint("127.0.0.1", 0))
        ext = MagicMock()
        with patch("opensomeip.rpc.get_ext", return_value=ext):
            RpcServer(socket, service_ids=[0x1234])
        ext.ServiceDemux.assert_not_called()
        ext.rpc.RpcServer.assert_called_once()
        assert ext.rpc.RpcServer.call_args.args[0] == 0x1234
