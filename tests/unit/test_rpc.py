"""Tests for opensomeip.rpc — RpcClient, RpcServer."""

from __future__ import annotations

import pytest

from opensomeip.exceptions import RpcError
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.rpc import RpcClient, RpcServer
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType


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

    def test_call_returns_response(self, transport: UdpTransport) -> None:
        client = RpcClient(transport)
        client.start()
        response = client.call(MessageId(0x1234, 0x0001), payload=b"\x01")
        assert response.message_type == MessageType.RESPONSE
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
