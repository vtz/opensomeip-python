"""Tests for opensomeip.server — SomeIpServer high-level API."""

from __future__ import annotations

import pytest

from opensomeip.message import Message
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.server import ServerConfig, SomeIpServer
from opensomeip.transport import Endpoint
from opensomeip.types import MessageId


@pytest.fixture()
def server_config() -> ServerConfig:
    return ServerConfig(
        local_endpoint=Endpoint("0.0.0.0", 30490),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.100", 30490),
        ),
        services=[ServiceInstance(service_id=0x1234, instance_id=0x0001)],
    )


class TestSomeIpServer:
    def test_lifecycle(self, server_config: ServerConfig) -> None:
        server = SomeIpServer(server_config)
        assert server.is_running is False
        server.start()
        assert server.is_running is True
        assert server.transport.is_running is True
        assert server.sd_server.is_running is True
        assert server.rpc_server.is_running is True
        assert server.event_publisher.is_running is True
        server.stop()
        assert server.is_running is False

    def test_context_manager(self, server_config: ServerConfig) -> None:
        with SomeIpServer(server_config) as server:
            assert server.is_running is True
        assert server.is_running is False

    def test_services_offered_on_start(self, server_config: ServerConfig) -> None:
        with SomeIpServer(server_config) as server:
            offered = server.sd_server.offered_services
            assert ServiceInstance(0x1234, 0x0001) in offered

    def test_register_method(self, server_config: ServerConfig) -> None:
        server = SomeIpServer(server_config)
        method = MessageId(0x1234, 0x0001)

        def handler(req: Message) -> Message:
            return Message(payload=b"response")

        server.register_method(method, handler)

    def test_register_event_and_publish(self, server_config: ServerConfig) -> None:
        with SomeIpServer(server_config) as server:
            server.register_event(event_id=0x8001, eventgroup_id=0x0001)
            server.publish_event(event_id=0x8001, payload=b"\x01")

    @pytest.mark.asyncio
    async def test_async_context_manager(self, server_config: ServerConfig) -> None:
        async with SomeIpServer(server_config) as server:
            assert server.is_running is True
        assert server.is_running is False

    def test_config_property(self, server_config: ServerConfig) -> None:
        server = SomeIpServer(server_config)
        assert server.config is server_config
