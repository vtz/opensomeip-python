"""Integration tests: Service Discovery offer <-> find over loopback.

These tests verify the full composition of Transport + SdServer/SdClient
through the high-level and low-level SD APIs.
"""

from __future__ import annotations

import time

import pytest

from opensomeip.client import ClientConfig, SomeIpClient
from opensomeip.sd import SdClient, SdConfig, SdServer, ServiceInstance
from opensomeip.server import ServerConfig, SomeIpServer
from opensomeip.transport import Endpoint

pytestmark = pytest.mark.integration

SERVICE = ServiceInstance(service_id=0xABCD, instance_id=0x0001)


@pytest.fixture()
def sd_config() -> SdConfig:
    return SdConfig(
        multicast_endpoint=Endpoint("239.1.1.1", 30490),
        unicast_endpoint=Endpoint("127.0.0.1", 30510),
    )


@pytest.fixture()
def server_config(sd_config: SdConfig) -> ServerConfig:
    return ServerConfig(
        local_endpoint=Endpoint("127.0.0.1", 30510),
        sd_config=sd_config,
        services=[SERVICE],
    )


@pytest.fixture()
def client_config(sd_config: SdConfig) -> ClientConfig:
    return ClientConfig(
        local_endpoint=Endpoint("127.0.0.1", 30511),
        sd_config=sd_config,
    )


class TestSdDiscovery:
    def test_offer_and_find_low_level(self, sd_config: SdConfig) -> None:
        """SdServer offers a service, SdClient issues a find (low-level API)."""
        server = SdServer(sd_config)
        server.start()
        server.offer(SERVICE)

        found: list[ServiceInstance] = []

        def on_found(svc: ServiceInstance) -> None:
            found.append(svc)

        client = SdClient(sd_config)
        client.start()
        client.find(SERVICE, on_found)

        time.sleep(0.5)

        client.stop()
        server.stop_offer(SERVICE)
        server.stop()

    def test_offer_and_find_high_level(
        self, server_config: ServerConfig, client_config: ClientConfig
    ) -> None:
        """SomeIpServer offers, SomeIpClient discovers (high-level API)."""
        with SomeIpServer(server_config) as server:
            assert server.is_running

            with SomeIpClient(client_config) as client:
                assert client.is_running

    def test_multiple_services(self, sd_config: SdConfig) -> None:
        """Offering multiple services from the same SdServer."""
        svc_a = ServiceInstance(service_id=0x1111, instance_id=0x0001)
        svc_b = ServiceInstance(service_id=0x2222, instance_id=0x0001)

        server = SdServer(sd_config)
        server.start()
        server.offer(svc_a)
        server.offer(svc_b)

        assert svc_a in server.offered_services
        assert svc_b in server.offered_services

        server.stop_offer(svc_a)
        server.stop_offer(svc_b)
        server.stop()

    def test_stop_offer_removes_service(self, sd_config: SdConfig) -> None:
        """After stop_offer, the service is removed from offered set."""
        server = SdServer(sd_config)
        server.start()
        server.offer(SERVICE)
        assert SERVICE in server.offered_services

        server.stop_offer(SERVICE)
        assert SERVICE not in server.offered_services
        server.stop()

    def test_server_lifecycle_context_manager(self, server_config: ServerConfig) -> None:
        """SomeIpServer context manager properly manages SD lifecycle."""
        with SomeIpServer(server_config) as server:
            assert server.is_running
        assert not server.is_running
