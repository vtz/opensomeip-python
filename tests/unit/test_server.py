"""Tests for opensomeip.server — SomeIpServer high-level API.

Covers spec areas:
    - Transport selection (UDP/TCP) — feat_req_someip_800-854
    - Service Discovery — feat_req_someipsd_200-205
    - RPC method handling
    - Event publishing — feat_req_someipsd_203-205
    - TP integration — feat_req_someiptp_400-414
    - E2E protection — feat_req_someip_102-103
    - Error handling — feat_req_someip_900-904
"""

from __future__ import annotations

import pytest

from opensomeip.e2e import E2ECheckStatus, E2EConfig, E2EProfile, E2EProfileId
from opensomeip.exceptions import TransportError
from opensomeip.message import Message
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.server import ServerConfig, SomeIpServer, TransportMode
from opensomeip.transport import Endpoint, TcpTransport, UdpTransport
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


@pytest.fixture()
def tcp_server_config() -> ServerConfig:
    return ServerConfig(
        local_endpoint=Endpoint("0.0.0.0", 30490),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.100", 30490),
        ),
        services=[ServiceInstance(service_id=0x1234, instance_id=0x0001)],
        transport_mode=TransportMode.TCP,
    )


class _DummyE2EProfile(E2EProfile):
    def protect(self, data: bytearray, counter: int) -> bytearray:
        data.append(counter & 0xFF)
        return data

    def check(self, data: bytes, counter: int) -> E2ECheckStatus:
        return E2ECheckStatus.OK


@pytest.fixture()
def e2e_server_config() -> ServerConfig:
    return ServerConfig(
        local_endpoint=Endpoint("0.0.0.0", 30490),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.100", 30490),
        ),
        e2e_config=E2EConfig(
            profile_id=E2EProfileId.PROFILE_01,
            data_id=0x1234,
            data_length=16,
        ),
        e2e_profile=_DummyE2EProfile(),
    )


@pytest.fixture()
def tp_server_config() -> ServerConfig:
    return ServerConfig(
        local_endpoint=Endpoint("0.0.0.0", 30490),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.100", 30490),
        ),
        enable_tp=True,
        tp_mtu=100,
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

    def test_register_event_and_publish_raises_without_native(
        self, server_config: ServerConfig
    ) -> None:
        with SomeIpServer(server_config) as server:
            server.register_event(event_id=0x8001, eventgroup_id=0x0001)
            with pytest.raises(RuntimeError, match="C\\+\\+ extension is not available"):
                server.publish_event(event_id=0x8001, payload=b"\x01")

    @pytest.mark.asyncio
    async def test_async_context_manager(self, server_config: ServerConfig) -> None:
        async with SomeIpServer(server_config) as server:
            assert server.is_running is True
        assert server.is_running is False

    def test_config_property(self, server_config: ServerConfig) -> None:
        server = SomeIpServer(server_config)
        assert server.config is server_config


class TestTransportMode:
    """feat_req_someip_800-854: UDP/TCP transport selection."""

    def test_udp_is_default(self, server_config: ServerConfig) -> None:
        server = SomeIpServer(server_config)
        assert isinstance(server.transport, UdpTransport)

    def test_tcp_transport(self, tcp_server_config: ServerConfig) -> None:
        server = SomeIpServer(tcp_server_config)
        assert isinstance(server.transport, TcpTransport)

    def test_transport_mode_enum_values(self) -> None:
        assert TransportMode.UDP.value == "udp"
        assert TransportMode.TCP.value == "tcp"


class TestServiceDiscovery:
    """feat_req_someipsd_200-205: SD offer/stop-offer."""

    def test_offer_service(self, server_config: ServerConfig) -> None:
        with SomeIpServer(server_config) as server:
            extra = ServiceInstance(service_id=0x5678, instance_id=0x0002)
            server.offer(extra)
            assert extra in server.offered_services

    def test_stop_offer_service(self, server_config: ServerConfig) -> None:
        with SomeIpServer(server_config) as server:
            svc = ServiceInstance(service_id=0x1234, instance_id=0x0001)
            server.stop_offer(svc)
            assert svc not in server.offered_services

    def test_offered_services_returns_frozenset(self, server_config: ServerConfig) -> None:
        with SomeIpServer(server_config) as server:
            assert isinstance(server.offered_services, frozenset)


class TestTpIntegration:
    """feat_req_someiptp_400-414: TP segmentation integration."""

    def test_tp_manager_created_when_enabled(self, tp_server_config: ServerConfig) -> None:
        server = SomeIpServer(tp_server_config)
        assert server.tp_manager is not None
        assert server.tp_manager.mtu == 100

    def test_tp_manager_none_when_disabled(self, server_config: ServerConfig) -> None:
        server = SomeIpServer(server_config)
        assert server.tp_manager is None

    def test_tp_lifecycle(self, tp_server_config: ServerConfig) -> None:
        with SomeIpServer(tp_server_config) as server:
            assert server.tp_manager is not None
            assert server.tp_manager.is_running is True
        assert server.tp_manager is not None
        assert server.tp_manager.is_running is False

    def test_send_via_tp_raises_without_native(self, tp_server_config: ServerConfig) -> None:
        with SomeIpServer(tp_server_config) as server:
            msg = Message(
                message_id=MessageId(0x1234, 0x0001),
                payload=b"\x00" * 200,
            )
            with pytest.raises(TransportError, match="native transport is not available"):
                server.send(msg)

    def test_send_without_tp_raises_without_native(self, server_config: ServerConfig) -> None:
        with SomeIpServer(server_config) as server:
            msg = Message(
                message_id=MessageId(0x1234, 0x0001),
                payload=b"\x00",
            )
            with pytest.raises(TransportError, match="native transport is not available"):
                server.send(msg)


class TestE2EIntegration:
    """feat_req_someip_102-103: E2E protection integration."""

    def test_e2e_created_when_configured(self, e2e_server_config: ServerConfig) -> None:
        server = SomeIpServer(e2e_server_config)
        assert server.e2e is not None

    def test_e2e_none_when_not_configured(self, server_config: ServerConfig) -> None:
        server = SomeIpServer(server_config)
        assert server.e2e is None

    def test_register_method_with_e2e(self, e2e_server_config: ServerConfig) -> None:
        server = SomeIpServer(e2e_server_config)
        method = MessageId(0x1234, 0x0001)
        calls: list[Message] = []

        def handler(req: Message) -> Message:
            calls.append(req)
            return Message(payload=b"response")

        server.register_method(method, handler)

    def test_publish_event_with_e2e_raises_without_native(
        self, e2e_server_config: ServerConfig
    ) -> None:
        with SomeIpServer(e2e_server_config) as server:
            server.register_event(event_id=0x8001, eventgroup_id=0x0001)
            with pytest.raises(RuntimeError, match="C\\+\\+ extension is not available"):
                server.publish_event(event_id=0x8001, payload=b"\x01")


class TestSetField:
    """Server field event support (getter/setter pattern)."""

    def test_set_field_raises_without_native(self, server_config: ServerConfig) -> None:
        with SomeIpServer(server_config) as server:
            server.register_event(event_id=0x8001, eventgroup_id=0x0001)
            with pytest.raises(RuntimeError, match="C\\+\\+ extension is not available"):
                server.set_field(event_id=0x8001, payload=b"\x42")
