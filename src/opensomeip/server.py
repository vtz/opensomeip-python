"""High-level convenience class: SomeIpServer.

Composes Transport + SdServer + RpcServer + EventPublisher + TpManager + E2E
into a single ergonomic object covering the full SOME/IP specification surface.

Spec coverage:
    - Message format (feat_req_someip_538-559)
    - Service Discovery server (feat_req_someipsd_200-205, 300-304)
    - RPC server (method handler registration)
    - Events publisher (feat_req_someipsd_203-205 eventgroup subscriptions)
    - Transport Protocol (feat_req_someiptp_400-414)
    - E2E protection (feat_req_someip_102-103)
    - UDP/TCP transport (feat_req_someip_800-854)
    - Session management (feat_req_someip_910-913)
    - Error handling (feat_req_someip_900-904)
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from types import TracebackType
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip.e2e import E2EConfig, E2EProfile, E2EProtection
from opensomeip.events import EventPublisher
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.rpc import RpcServer
from opensomeip.sd import SdConfig, SdServer, ServiceInstance
from opensomeip.tp import TpManager
from opensomeip.transport import Endpoint, TcpTransport, Transport, UdpTransport
from opensomeip.types import MessageId, MessageType, ReturnCode


class TransportMode(enum.Enum):
    """Transport protocol selection for the server."""

    UDP = "udp"
    TCP = "tcp"


@dataclass(slots=True)
class ServerConfig:
    """Configuration for :class:`SomeIpServer`.

    Covers spec requirements:
        - feat_req_someipsd_300-304: SD multicast/port configuration
        - feat_req_someip_800-804: UDP transport configuration
        - feat_req_someip_850-854: TCP transport configuration
        - feat_req_someiptp_403: TP segment size negotiation
        - feat_req_someip_102-103: E2E protection configuration
    """

    local_endpoint: Endpoint
    sd_config: SdConfig
    services: list[ServiceInstance] = field(default_factory=list)
    transport_mode: TransportMode = TransportMode.UDP
    multicast_group: str | None = None
    enable_tp: bool = False
    tp_mtu: int = 1400
    e2e_config: E2EConfig | None = None
    e2e_profile: E2EProfile | None = None


class SomeIpServer:
    """High-level SOME/IP server combining all protocol components.

    Composes Transport, Service Discovery, RPC, Events, TP, and E2E
    into a unified server interface covering the complete SOME/IP spec.

    Supports both synchronous and asynchronous usage::

        # Synchronous with context manager
        with SomeIpServer(config) as server:
            server.register_method(method_id, handler)
            server.register_event(event_id, eventgroup_id)
            server.publish_event(event_id, payload)

        # Asynchronous
        async with SomeIpServer(config) as server:
            server.register_async_method(method_id, async_handler)
            async for req in server.incoming_requests(method_id):
                ...
    """

    def __init__(self, config: ServerConfig) -> None:
        self._config = config

        if config.transport_mode == TransportMode.TCP:
            self._transport: Transport = TcpTransport(
                config.local_endpoint,
            )
        else:
            self._transport = UdpTransport(
                config.local_endpoint,
                multicast_group=config.multicast_group,
            )

        self._sd_server = SdServer(config.sd_config)
        self._rpc_server = RpcServer(self._transport)
        self._event_publisher = EventPublisher(self._transport)

        self._tp_manager: TpManager | None = None
        if config.enable_tp:
            self._tp_manager = TpManager(self._transport, mtu=config.tp_mtu)

        self._e2e: E2EProtection | None = None
        if config.e2e_config is not None:
            self._e2e = E2EProtection(config.e2e_config, config.e2e_profile)

        self._running = False

    # --- Properties ---

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
    def tp_manager(self) -> TpManager | None:
        return self._tp_manager

    @property
    def e2e(self) -> E2EProtection | None:
        return self._e2e

    @property
    def is_running(self) -> bool:
        return self._running

    # --- Lifecycle (feat_req_someip_900-904 error handling) ---

    def start(self) -> None:
        """Start all server sub-components."""
        self._transport.start()
        self._sd_server.start()
        self._rpc_server.start()
        self._event_publisher.start()
        if self._tp_manager is not None:
            self._tp_manager.start()
        for svc in self._config.services:
            self._sd_server.offer(svc)
        self._running = True

    def stop(self) -> None:
        """Stop all server sub-components in reverse order."""
        self._running = False
        for svc in self._config.services:
            self._sd_server.stop_offer(svc)
        if self._tp_manager is not None:
            self._tp_manager.stop()
        self._event_publisher.stop()
        self._rpc_server.stop()
        self._sd_server.stop()
        self._transport.stop()

    # --- RPC (method registration) ---

    def register_method(
        self,
        method_id: MessageId,
        handler: Callable[[Message], Message],
    ) -> None:
        """Register a synchronous RPC method handler."""
        if self._e2e is not None:
            original = handler
            e2e = self._e2e

            def e2e_handler(req: Message) -> Message:
                resp = original(req)
                resp.payload = e2e.protect(resp.payload)
                return resp

            self._rpc_server.register_handler(method_id, e2e_handler)
        else:
            self._rpc_server.register_handler(method_id, handler)

    def register_async_method(
        self,
        method_id: MessageId,
        handler: Callable[[Message], Awaitable[Message]],
    ) -> None:
        """Register an asynchronous RPC method handler."""
        self._rpc_server.register_async_handler(method_id, handler)

    def incoming_requests(self, method_id: MessageId) -> MessageReceiver:
        """Return an async-iterable receiver of incoming RPC requests.

        Iterator pattern alternative to callback-based method registration.
        """
        return self._rpc_server.incoming_requests(method_id)

    # --- Events (feat_req_someipsd_203-205 eventgroup subscriptions) ---

    def register_event(self, event_id: int, eventgroup_id: int) -> None:
        """Register an event for publishing."""
        self._event_publisher.register_event(event_id, eventgroup_id)

    def publish_event(self, event_id: int, payload: bytes) -> None:
        """Publish an event notification.

        If E2E is enabled, protection is applied automatically.
        If TP is enabled and the payload exceeds MTU, it is segmented.
        """
        if self._e2e is not None:
            payload = self._e2e.protect(payload)

        msg = Message(
            message_id=MessageId(service_id=0, method_id=event_id),
            message_type=MessageType.NOTIFICATION,
            return_code=ReturnCode.E_OK,
            payload=payload,
        )

        if self._tp_manager is not None and len(payload) > self._config.tp_mtu:
            self._tp_manager.send(msg)
        else:
            self._event_publisher.notify(event_id, payload)

    def set_field(self, event_id: int, payload: bytes) -> None:
        """Set the value of a field event (getter/setter pattern)."""
        if self._e2e is not None:
            payload = self._e2e.protect(payload)
        self._event_publisher.set_field(event_id, payload)

    # --- Service Discovery (feat_req_someipsd_200-205) ---

    def offer(self, service: ServiceInstance) -> None:
        """Offer a service instance for discovery."""
        self._sd_server.offer(service)

    def stop_offer(self, service: ServiceInstance) -> None:
        """Withdraw a service offer."""
        self._sd_server.stop_offer(service)

    @property
    def offered_services(self) -> frozenset[ServiceInstance]:
        """Return the set of currently offered services."""
        return self._sd_server.offered_services

    # --- TP (feat_req_someiptp_400-414) ---

    def send(self, message: Message) -> None:
        """Send a message, using TP segmentation if needed.

        This is the low-level send that handles TP transparently.
        Prefer :meth:`publish_event` or RPC methods for typical use.
        """
        if self._tp_manager is not None:
            self._tp_manager.send(message)
        else:
            self._transport.send(message)

    # --- Context managers ---

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
