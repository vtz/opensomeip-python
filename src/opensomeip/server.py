"""High-level convenience class: SomeIpServer.

Composes Transport + SdServer + RpcServer + EventPublisher into a single
ergonomic object for common server use cases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip.events import EventPublisher
from opensomeip.message import Message
from opensomeip.rpc import RpcServer
from opensomeip.sd import SdConfig, SdServer, ServiceInstance
from opensomeip.transport import Endpoint, Transport, UdpTransport
from opensomeip.types import MessageId


@dataclass(slots=True)
class ServerConfig:
    """Configuration for :class:`SomeIpServer`."""

    local_endpoint: Endpoint
    sd_config: SdConfig
    services: list[ServiceInstance] = field(default_factory=list)


class SomeIpServer:
    """High-level SOME/IP server combining transport, SD, RPC, and events.

    Example::

        config = ServerConfig(
            local_endpoint=Endpoint("0.0.0.0", 30490),
            sd_config=SdConfig(
                multicast_endpoint=Endpoint("239.1.1.1", 30490),
                unicast_endpoint=Endpoint("192.168.1.100", 30490),
            ),
            services=[ServiceInstance(service_id=0x1234, instance_id=0x0001)],
        )
        with SomeIpServer(config) as server:
            server.register_method(
                MessageId(0x1234, 0x0001),
                lambda req: Message(payload=b"response"),
            )
            # server is running...
    """

    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._transport: Transport = UdpTransport(config.local_endpoint)
        self._sd_server = SdServer(config.sd_config)
        self._rpc_server = RpcServer(self._transport)
        self._event_publisher = EventPublisher(self._transport)
        self._running = False

    @property
    def config(self) -> ServerConfig:
        return self._config

    @property
    def transport(self) -> Transport:
        return self._transport

    @property
    def sd_server(self) -> SdServer:
        return self._sd_server

    @property
    def rpc_server(self) -> RpcServer:
        return self._rpc_server

    @property
    def event_publisher(self) -> EventPublisher:
        return self._event_publisher

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start all server sub-components."""
        self._transport.start()
        self._sd_server.start()
        self._rpc_server.start()
        self._event_publisher.start()
        for svc in self._config.services:
            self._sd_server.offer(svc)
        self._running = True

    def stop(self) -> None:
        """Stop all server sub-components in reverse order."""
        self._running = False
        for svc in self._config.services:
            self._sd_server.stop_offer(svc)
        self._event_publisher.stop()
        self._rpc_server.stop()
        self._sd_server.stop()
        self._transport.stop()

    def register_method(
        self,
        method_id: MessageId,
        handler: Callable[[Message], Message],
    ) -> None:
        """Register a synchronous RPC method handler."""
        self._rpc_server.register_handler(method_id, handler)

    def register_async_method(
        self,
        method_id: MessageId,
        handler: Callable[[Message], Awaitable[Message]],
    ) -> None:
        """Register an asynchronous RPC method handler."""
        self._rpc_server.register_async_handler(method_id, handler)

    def register_event(self, event_id: int, eventgroup_id: int) -> None:
        """Register an event for publishing."""
        self._event_publisher.register_event(event_id, eventgroup_id)

    def publish_event(self, event_id: int, payload: bytes) -> None:
        """Publish an event notification."""
        self._event_publisher.notify(event_id, payload)

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
