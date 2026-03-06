"""Tests for opensomeip.sd — SdServer, SdClient, ServiceInstance."""

from __future__ import annotations

import pytest

from opensomeip.sd import SdClient, SdConfig, SdServer, ServiceInstance
from opensomeip.transport import Endpoint


@pytest.fixture()
def sd_config() -> SdConfig:
    return SdConfig(
        multicast_endpoint=Endpoint("239.1.1.1", 30490),
        unicast_endpoint=Endpoint("192.168.1.100", 30490),
    )


class TestServiceInstance:
    def test_construction(self) -> None:
        si = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        assert si.service_id == 0x1234
        assert si.instance_id == 0x0001
        assert si.major_version == 1
        assert si.minor_version == 0

    def test_repr(self) -> None:
        si = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        r = repr(si)
        assert "0x1234" in r
        assert "0x0001" in r

    def test_frozen(self) -> None:
        si = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        with pytest.raises(AttributeError):
            si.service_id = 0x5678  # type: ignore[misc]

    def test_eq(self) -> None:
        a = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        b = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        assert a == b

    def test_hash(self) -> None:
        a = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        s = {a}
        assert a in s


class TestSdConfig:
    def test_defaults(self, sd_config: SdConfig) -> None:
        assert sd_config.ttl == 3
        assert sd_config.cyclic_offer_delay_ms == 1000
        assert sd_config.repetitions_max == 3


class TestSdServer:
    def test_lifecycle(self, sd_config: SdConfig) -> None:
        server = SdServer(sd_config)
        assert server.is_running is False
        server.start()
        assert server.is_running is True
        server.stop()
        assert server.is_running is False

    def test_context_manager(self, sd_config: SdConfig) -> None:
        with SdServer(sd_config) as server:
            assert server.is_running is True
        assert server.is_running is False

    def test_offer_and_stop_offer(self, sd_config: SdConfig) -> None:
        server = SdServer(sd_config)
        svc = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        server.offer(svc)
        assert svc in server.offered_services
        server.stop_offer(svc)
        assert svc not in server.offered_services

    def test_stop_clears_offers(self, sd_config: SdConfig) -> None:
        server = SdServer(sd_config)
        server.start()
        server.offer(ServiceInstance(0x1234, 0x0001))
        server.stop()
        assert len(server.offered_services) == 0

    @pytest.mark.asyncio
    async def test_async_context_manager(self, sd_config: SdConfig) -> None:
        async with SdServer(sd_config) as server:
            assert server.is_running is True
        assert server.is_running is False


class TestSdClient:
    def test_lifecycle(self, sd_config: SdConfig) -> None:
        client = SdClient(sd_config)
        client.start()
        assert client.is_running is True
        client.stop()
        assert client.is_running is False

    def test_context_manager(self, sd_config: SdConfig) -> None:
        with SdClient(sd_config) as client:
            assert client.is_running is True
        assert client.is_running is False

    def test_find_returns_receiver(self, sd_config: SdConfig) -> None:
        client = SdClient(sd_config)
        svc = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        receiver = client.find(svc)
        assert receiver is not None
