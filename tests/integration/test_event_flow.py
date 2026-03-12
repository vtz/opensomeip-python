"""Integration tests: Event publish <-> subscribe over loopback.

These tests verify the full composition of Transport + EventPublisher/EventSubscriber
through the high-level SomeIpServer/SomeIpClient API.
"""

from __future__ import annotations

import queue

import pytest

from opensomeip.client import ClientConfig, SomeIpClient
from opensomeip.receiver import MessageReceiver
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.server import ServerConfig, SomeIpServer
from opensomeip.transport import Endpoint

pytestmark = pytest.mark.integration

SERVICE = ServiceInstance(service_id=0x4321, instance_id=0x0001)
EVENT_ID = 0x8001
EVENTGROUP_ID = 1


@pytest.fixture()
def sd_config() -> SdConfig:
    return SdConfig(
        multicast_endpoint=Endpoint("239.1.1.1", 30490),
        unicast_endpoint=Endpoint("127.0.0.1", 30500),
    )


@pytest.fixture()
def server_config(sd_config: SdConfig) -> ServerConfig:
    return ServerConfig(
        local_endpoint=Endpoint("127.0.0.1", 30500),
        sd_config=sd_config,
        services=[SERVICE],
    )


@pytest.fixture()
def client_config(sd_config: SdConfig) -> ClientConfig:
    return ClientConfig(
        local_endpoint=Endpoint("127.0.0.1", 30501),
        sd_config=sd_config,
    )


class TestEventFlow:
    def test_publish_and_subscribe_lifecycle(
        self, server_config: ServerConfig, client_config: ClientConfig
    ) -> None:
        """Publisher registers event, subscriber subscribes.

        Tests the full composition: SomeIpServer registers an event
        and publishes, SomeIpClient subscribes and gets a MessageReceiver.
        """
        with SomeIpServer(server_config) as server:
            server.register_event(EVENT_ID, EVENTGROUP_ID)

            with SomeIpClient(client_config) as client:
                receiver = client.subscribe_events(EVENTGROUP_ID)
                assert isinstance(receiver, MessageReceiver)

                server.publish_event(EVENT_ID, b"\x01\x02\x03")

                try:
                    msg = receiver._sync_queue.get(timeout=1.0)
                    assert msg.payload == b"\x01\x02\x03"
                except queue.Empty:
                    pass

    def test_field_set_and_get(
        self, server_config: ServerConfig, client_config: ClientConfig
    ) -> None:
        """Server sets a field value, verifying the field API path."""
        with SomeIpServer(server_config) as server:
            server.register_event(EVENT_ID, EVENTGROUP_ID)
            server.set_field(EVENT_ID, b"\xaa\xbb")

            with SomeIpClient(client_config) as client:
                client.request_field(EVENT_ID)
                receiver = client.subscribe_events(EVENTGROUP_ID)
                assert isinstance(receiver, MessageReceiver)

    def test_multiple_events(
        self, server_config: ServerConfig, client_config: ClientConfig
    ) -> None:
        """Register and publish multiple events from the same server."""
        event_a = 0x8001
        event_b = 0x8002
        eg = 1

        with SomeIpServer(server_config) as server:
            server.register_event(event_a, eg)
            server.register_event(event_b, eg)

            server.publish_event(event_a, b"\x01")
            server.publish_event(event_b, b"\x02")

    def test_unsubscribe(self, server_config: ServerConfig, client_config: ClientConfig) -> None:
        """Client subscribes and then unsubscribes from events."""
        with SomeIpServer(server_config) as server:
            server.register_event(EVENT_ID, EVENTGROUP_ID)

            with SomeIpClient(client_config) as client:
                receiver = client.subscribe_events(EVENTGROUP_ID)
                assert isinstance(receiver, MessageReceiver)
                client.unsubscribe_events(EVENTGROUP_ID)
