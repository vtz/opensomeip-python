"""Tests for opensomeip.client — SomeIpClient high-level API.

Covers spec areas:
    - Transport selection (UDP/TCP) — feat_req_someip_800-854
    - Service Discovery — feat_req_someipsd_200-205
    - RPC calls — feat_req_someip_910-913
    - Event subscription — feat_req_someipsd_203-205
    - TP integration — feat_req_someiptp_400-414
    - E2E protection — feat_req_someip_102-103
    - Error handling — feat_req_someip_900-904
"""

from __future__ import annotations

import pytest

from opensomeip.client import ClientConfig, SomeIpClient
from opensomeip.e2e import E2ECheckStatus, E2EConfig, E2EProfile, E2EProfileId
from opensomeip.receiver import MessageReceiver
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.server import TransportMode
from opensomeip.transport import Endpoint, TcpTransport, UdpTransport
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


@pytest.fixture()
def tcp_client_config() -> ClientConfig:
    return ClientConfig(
        local_endpoint=Endpoint("0.0.0.0", 0),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.200", 30490),
        ),
        transport_mode=TransportMode.TCP,
    )


class _DummyE2EProfile(E2EProfile):
    def protect(self, data: bytearray, counter: int) -> bytearray:
        data.append(counter & 0xFF)
        return data

    def check(self, data: bytes, counter: int) -> E2ECheckStatus:
        return E2ECheckStatus.OK


@pytest.fixture()
def e2e_client_config() -> ClientConfig:
    return ClientConfig(
        local_endpoint=Endpoint("0.0.0.0", 0),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.200", 30490),
        ),
        e2e_config=E2EConfig(
            profile_id=E2EProfileId.PROFILE_01,
            data_id=0x1234,
            data_length=16,
        ),
        e2e_profile=_DummyE2EProfile(),
    )


@pytest.fixture()
def tp_client_config() -> ClientConfig:
    return ClientConfig(
        local_endpoint=Endpoint("0.0.0.0", 0),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.200", 30490),
        ),
        enable_tp=True,
        tp_mtu=100,
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


class TestTransportMode:
    """feat_req_someip_800-854: UDP/TCP transport selection."""

    def test_udp_is_default(self, client_config: ClientConfig) -> None:
        client = SomeIpClient(client_config)
        assert isinstance(client.transport, UdpTransport)

    def test_tcp_transport(self, tcp_client_config: ClientConfig) -> None:
        client = SomeIpClient(tcp_client_config)
        assert isinstance(client.transport, TcpTransport)


class TestServiceDiscovery:
    """feat_req_someipsd_200-205: SD find/subscribe."""

    def test_find_with_callback(self, client_config: ClientConfig) -> None:
        found: list[ServiceInstance] = []
        with SomeIpClient(client_config) as client:
            svc = ServiceInstance(service_id=0x1234, instance_id=0x0001)
            receiver = client.find(svc, callback=lambda s: found.append(s))
            assert isinstance(receiver, MessageReceiver)


class TestEventSubscription:
    """feat_req_someipsd_203-205: Eventgroup subscription."""

    def test_unsubscribe_events(self, client_config: ClientConfig) -> None:
        with SomeIpClient(client_config) as client:
            client.subscribe_events(eventgroup_id=0x0001)
            client.unsubscribe_events(eventgroup_id=0x0001)

    def test_subscription_status(self, client_config: ClientConfig) -> None:
        with SomeIpClient(client_config) as client:
            receiver = client.subscription_status()
            assert isinstance(receiver, MessageReceiver)


class TestTpIntegration:
    """feat_req_someiptp_400-414: TP integration."""

    def test_tp_manager_created_when_enabled(self, tp_client_config: ClientConfig) -> None:
        client = SomeIpClient(tp_client_config)
        assert client.tp_manager is not None
        assert client.tp_manager.mtu == 100

    def test_tp_manager_none_when_disabled(self, client_config: ClientConfig) -> None:
        client = SomeIpClient(client_config)
        assert client.tp_manager is None

    def test_tp_lifecycle(self, tp_client_config: ClientConfig) -> None:
        with SomeIpClient(tp_client_config) as client:
            assert client.tp_manager is not None
            assert client.tp_manager.is_running is True
        assert client.tp_manager is not None
        assert client.tp_manager.is_running is False

    def test_reassembled_messages(self, tp_client_config: ClientConfig) -> None:
        with SomeIpClient(tp_client_config) as client:
            receiver = client.reassembled_messages()
            assert isinstance(receiver, MessageReceiver)

    def test_reassembled_messages_raises_without_tp(self, client_config: ClientConfig) -> None:
        with (
            SomeIpClient(client_config) as client,
            pytest.raises(RuntimeError, match="TP is not enabled"),
        ):
            client.reassembled_messages()

    def test_send_via_tp(self, tp_client_config: ClientConfig) -> None:
        from opensomeip.message import Message
        from opensomeip.types import MessageId

        with SomeIpClient(tp_client_config) as client:
            msg = Message(
                message_id=MessageId(0x1234, 0x0001),
                payload=b"\x00" * 200,
            )
            client.send(msg)


class TestE2EIntegration:
    """feat_req_someip_102-103: E2E protection integration."""

    def test_e2e_created_when_configured(self, e2e_client_config: ClientConfig) -> None:
        client = SomeIpClient(e2e_client_config)
        assert client.e2e is not None

    def test_e2e_none_when_not_configured(self, client_config: ClientConfig) -> None:
        client = SomeIpClient(client_config)
        assert client.e2e is None

    def test_call_with_e2e(self, e2e_client_config: ClientConfig) -> None:
        with SomeIpClient(e2e_client_config) as client:
            response = client.call(MessageId(0x1234, 0x0001), payload=b"\x01")
            assert response.message_type == MessageType.RESPONSE
