"""High-level convenience class: SomeIpClient.

Composes Transport + SdClient + RpcClient + EventSubscriber into a single
ergonomic object for common client use cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip.events import EventSubscriber
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.rpc import RpcClient
from opensomeip.sd import SdClient, SdConfig, ServiceInstance
from opensomeip.transport import Endpoint, Transport, UdpTransport
from opensomeip.types import MessageId


@dataclass(slots=True)
class ClientConfig:
    """Configuration for :class:`SomeIpClient`."""

    local_endpoint: Endpoint
    sd_config: SdConfig


class SomeIpClient:
    """High-level SOME/IP client combining transport, SD, RPC, and events.

    Example::

        config = ClientConfig(
            local_endpoint=Endpoint("0.0.0.0", 0),
            sd_config=SdConfig(
                multicast_endpoint=Endpoint("239.1.1.1", 30490),
                unicast_endpoint=Endpoint("192.168.1.200", 30490),
            ),
        )
        with SomeIpClient(config) as client:
            response = client.call(
                MessageId(0x1234, 0x0001),
                payload=b"request",
            )
    """

    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        self._transport: Transport = UdpTransport(config.local_endpoint)
        self._sd_client = SdClient(config.sd_config)
        self._rpc_client = RpcClient(self._transport)
        self._event_subscriber = EventSubscriber(self._transport)
        self._running = False

    @property
    def config(self) -> ClientConfig:
        return self._config

    @property
    def transport(self) -> Transport:
        return self._transport

    @property
    def sd_client(self) -> SdClient:
        return self._sd_client

    @property
    def rpc_client(self) -> RpcClient:
        return self._rpc_client

    @property
    def event_subscriber(self) -> EventSubscriber:
        return self._event_subscriber

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start all client sub-components."""
        self._transport.start()
        self._sd_client.start()
        self._rpc_client.start()
        self._event_subscriber.start()
        self._running = True

    def stop(self) -> None:
        """Stop all client sub-components in reverse order."""
        self._running = False
        self._event_subscriber.stop()
        self._rpc_client.stop()
        self._sd_client.stop()
        self._transport.stop()

    def find(self, service: ServiceInstance) -> MessageReceiver:
        """Find a service via SD and return a receiver for discovery results."""
        return self._sd_client.find(service)

    def call(
        self,
        method_id: MessageId,
        payload: bytes = b"",
        *,
        timeout: float = 5.0,
    ) -> Message:
        """Synchronous RPC call to a remote method."""
        return self._rpc_client.call(method_id, payload, timeout=timeout)

    async def call_async(
        self,
        method_id: MessageId,
        payload: bytes = b"",
        *,
        timeout: float = 5.0,
    ) -> Message:
        """Asynchronous RPC call to a remote method."""
        return await self._rpc_client.call_async(method_id, payload, timeout=timeout)

    def subscribe_events(self, eventgroup_id: int) -> MessageReceiver:
        """Subscribe to an event group and return a notification receiver."""
        self._event_subscriber.subscribe(eventgroup_id)
        return self._event_subscriber.notifications()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()

    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()
