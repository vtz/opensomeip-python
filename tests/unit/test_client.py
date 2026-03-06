"""Tests for opensomeip.client — SomeIpClient high-level API."""

from __future__ import annotations

import pytest

from opensomeip.client import ClientConfig, SomeIpClient
from opensomeip.receiver import MessageReceiver
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.transport import Endpoint
from opensomeip.types import MessageId, MessageType


@pytest.fixture()
def client_config() -> ClientConfig:
    return ClientConfig(
        local_endpoint=Endpoint("0.0.0.0", 0),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.200", 30490),
        ),
    )


class TestSomeIpClient:
    def test_lifecycle(self, client_config: ClientConfig) -> None:
        client = SomeIpClient(client_config)
        assert client.is_running is False
        client.start()
        assert client.is_running is True
        assert client.transport.is_running is True
        assert client.sd_client.is_running is True
        assert client.rpc_client.is_running is True
        assert client.event_subscriber.is_running is True
        client.stop()
        assert client.is_running is False

    def test_context_manager(self, client_config: ClientConfig) -> None:
        with SomeIpClient(client_config) as client:
            assert client.is_running is True
        assert client.is_running is False

    def test_find_returns_receiver(self, client_config: ClientConfig) -> None:
        with SomeIpClient(client_config) as client:
            svc = ServiceInstance(service_id=0x1234, instance_id=0x0001)
            receiver = client.find(svc)
            assert isinstance(receiver, MessageReceiver)

    def test_call(self, client_config: ClientConfig) -> None:
        with SomeIpClient(client_config) as client:
            response = client.call(MessageId(0x1234, 0x0001), payload=b"\x01")
            assert response.message_type == MessageType.RESPONSE

    def test_subscribe_events(self, client_config: ClientConfig) -> None:
        with SomeIpClient(client_config) as client:
            receiver = client.subscribe_events(eventgroup_id=0x0001)
            assert isinstance(receiver, MessageReceiver)

    @pytest.mark.asyncio
    async def test_async_context_manager(self, client_config: ClientConfig) -> None:
        async with SomeIpClient(client_config) as client:
            assert client.is_running is True
        assert client.is_running is False

    def test_config_property(self, client_config: ClientConfig) -> None:
        client = SomeIpClient(client_config)
        assert client.config is client_config
