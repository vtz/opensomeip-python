"""Integration tests for a shared application socket and injected transports."""

from __future__ import annotations

import pytest

from opensomeip._bridge import get_ext
from opensomeip.message import Message
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.server import ServerConfig, SomeIpServer, TransportMode
from opensomeip.transport import Endpoint
from opensomeip.types import MessageId, MessageType, ReturnCode

pytestmark = pytest.mark.integration

SERVICE = ServiceInstance(service_id=0x1234, instance_id=0x0001)
METHOD = MessageId(service_id=0x1234, method_id=0x0001)


def _echo(req: Message) -> Message:
    return Message(
        message_id=req.message_id,
        request_id=req.request_id,
        message_type=MessageType.RESPONSE,
        return_code=ReturnCode.E_OK,
        payload=req.payload,
    )


class TestTcpApplicationSocket:
    def test_injected_client_reaches_tcp_server(self) -> None:
        """A TCP server listens on its endpoint and answers an injected client."""
        ext = get_ext()
        assert ext is not None
        sd_config = SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("127.0.0.1", 30652),
        )
        server_config = ServerConfig(
            local_endpoint=Endpoint("127.0.0.1", 30650),
            sd_config=sd_config,
            services=[SERVICE],
            transport_mode=TransportMode.TCP,
        )
        server_endpoint = ext.Endpoint("127.0.0.1", 30650, ext.TransportProtocol.TCP)

        with SomeIpServer(server_config) as server:
            server.register_method(METHOD, _echo)
            tcp = ext.TcpTransport()
            initialized = tcp.initialize(ext.Endpoint("127.0.0.1", 0))
            assert initialized.name == "SUCCESS"
            connected = tcp.connect(server_endpoint)
            assert connected.name == "SUCCESS"
            rpc = ext.rpc.RpcClient(0x00A1, tcp)
            assert rpc.initialize() is True
            try:
                rpc.set_remote_endpoint(server_endpoint)
                result = rpc.call_method_sync(0x1234, 0x0001, [0xCA, 0xFE])
            finally:
                rpc.shutdown()

        assert int(result.result) == 0
        assert bytes(result.return_values) == b"\xca\xfe"


class TestInjectedFacades:
    def test_event_publisher_and_subscriber_start_on_borrowed_sockets(self) -> None:
        ext = get_ext()
        assert ext is not None
        publisher_socket = ext.UdpTransport(ext.Endpoint("127.0.0.1", 0))
        publisher = ext.events.EventPublisher(0x4321, 0x0001, publisher_socket)
        assert publisher.initialize() is True
        assert publisher.get_transport_result().name == "SUCCESS"
        publisher.shutdown()

        subscriber_socket = ext.UdpTransport(ext.Endpoint("127.0.0.1", 0))
        subscriber = ext.events.EventSubscriber(0x00B1, subscriber_socket)
        assert subscriber.initialize() is True
        assert subscriber.get_transport_result().name == "SUCCESS"
        subscriber.shutdown()

    def test_sd_client_and_server_start_on_borrowed_sockets(self) -> None:
        ext = get_ext()
        assert ext is not None
        config = ext.sd.SdConfig()
        config.multicast_address = "239.1.1.1"
        config.multicast_port = 30490

        server_socket = ext.UdpTransport(ext.Endpoint("127.0.0.1", 0))
        server = ext.sd.SdServer(config, server_socket)
        assert server.initialize() is True
        assert server.get_transport_result().name == "SUCCESS"
        server.shutdown()

        client_socket = ext.UdpTransport(ext.Endpoint("127.0.0.1", 0))
        client = ext.sd.SdClient(config, client_socket)
        assert client.initialize() is True
        assert client.get_transport_result().name == "SUCCESS"
        client.shutdown()
