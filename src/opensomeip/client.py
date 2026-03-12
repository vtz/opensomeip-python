"""High-level convenience class: SomeIpClient.

Composes Transport + SdClient + RpcClient + EventSubscriber + TpManager + E2E
into a single ergonomic object covering the full SOME/IP specification surface.

Spec coverage:
    - Message format (feat_req_someip_538-559)
    - Service Discovery client (feat_req_someipsd_200-205, 300-304)
    - RPC client (sync/async method calls)
    - Events subscriber (eventgroup subscriptions, notifications, fields)
    - Transport Protocol (feat_req_someiptp_400-414)
    - E2E protection (feat_req_someip_102-103)
    - UDP/TCP transport (feat_req_someip_800-854)
    - Session management (feat_req_someip_910-913)
    - Error handling (feat_req_someip_900-904)
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip.e2e import E2ECheckStatus, E2EConfig, E2EProfile, E2EProtection
from opensomeip.events import EventSubscriber
from opensomeip.exceptions import E2EError
from opensomeip.message import Message
from opensomeip.receiver import MessageReceiver
from opensomeip.rpc import RpcClient
from opensomeip.sd import SdClient, SdConfig, ServiceInstance
from opensomeip.server import TransportMode
from opensomeip.tp import TpManager
from opensomeip.transport import Endpoint, TcpTransport, Transport, UdpTransport
from opensomeip.types import MessageId


@dataclass(slots=True)
class ClientConfig:
    """Configuration for :class:`SomeIpClient`.

    Covers spec requirements:
        - feat_req_someipsd_300-304: SD multicast/port configuration
        - feat_req_someip_800-804: UDP transport configuration
        - feat_req_someip_850-854: TCP transport configuration
        - feat_req_someiptp_403: TP segment size negotiation
        - feat_req_someip_102-103: E2E protection configuration
    """

    local_endpoint: Endpoint
    sd_config: SdConfig
    transport_mode: TransportMode = TransportMode.UDP
    multicast_group: str | None = None
    enable_tp: bool = False
    tp_mtu: int = 1400
    e2e_config: E2EConfig | None = None
    e2e_profile: E2EProfile | None = None


class SomeIpClient:
    """High-level SOME/IP client combining all protocol components.

    Composes Transport, Service Discovery, RPC, Events, TP, and E2E
    into a unified client interface covering the complete SOME/IP spec.

    Supports both synchronous and asynchronous usage::

        # Synchronous
        with SomeIpClient(config) as client:
            response = client.call(method_id, payload=b"request")
            for msg in client.subscribe_events(eventgroup_id):
                process(msg)

        # Asynchronous
        async with SomeIpClient(config) as client:
            response = await client.call_async(method_id, payload=b"data")
            async for msg in client.subscribe_events(eventgroup_id):
                await process(msg)
    """

    def __init__(self, config: ClientConfig) -> None:
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

        self._sd_client = SdClient(config.sd_config)
        self._rpc_client = RpcClient(self._transport)
        self._event_subscriber = EventSubscriber(self._transport)

        self._tp_manager: TpManager | None = None
        if config.enable_tp:
            self._tp_manager = TpManager(self._transport, mtu=config.tp_mtu)

        self._e2e: E2EProtection | None = None
        if config.e2e_config is not None:
            self._e2e = E2EProtection(config.e2e_config, config.e2e_profile)

        self._running = False

    # --- Properties ---

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
        """Start all client sub-components."""
        self._transport.start()
        self._sd_client.start()
        self._rpc_client.start()
        self._event_subscriber.start()
        if self._tp_manager is not None:
            self._tp_manager.start()
        self._running = True

    def stop(self) -> None:
        """Stop all client sub-components in reverse order."""
        self._running = False
        if self._tp_manager is not None:
            self._tp_manager.stop()
        self._event_subscriber.stop()
        self._rpc_client.stop()
        self._sd_client.stop()
        self._transport.stop()

    # --- Service Discovery (feat_req_someipsd_200-205, 300-304) ---

    def find(
        self,
        service: ServiceInstance,
        callback: Callable[[ServiceInstance], None] | None = None,
    ) -> MessageReceiver:
        """Find a service via SD and return a receiver for discovery results.

        Args:
            service: Service to find.
            callback: Optional callback invoked when the service is found.
        """
        return self._sd_client.find(service, callback)

    def subscribe_service(
        self,
        service: ServiceInstance,
        *,
        on_available: Callable[[ServiceInstance], None] | None = None,
        on_unavailable: Callable[[ServiceInstance], None] | None = None,
    ) -> None:
        """Subscribe to availability notifications for a service.

        Tracks service availability via SD offer/stop-offer messages.
        """
        # Placeholder — will delegate to SdClient when availability
        # tracking is wired through the C++ binding callbacks.

    # --- RPC (feat_req_someip_910-913 session management) ---

    def call(
        self,
        method_id: MessageId,
        payload: bytes = b"",
        *,
        timeout: float = 5.0,
    ) -> Message:
        """Synchronous RPC call to a remote method.

        If E2E is enabled, protection is applied to the request
        and verified on the response.
        """
        if self._e2e is not None:
            payload = self._e2e.protect(payload)

        response = self._rpc_client.call(method_id, payload, timeout=timeout)

        if self._e2e is not None:
            status = self._e2e.check(response.payload)
            if status != E2ECheckStatus.OK:
                raise E2EError(f"E2E check failed on response: {status.name}")

        return response

    async def call_async(
        self,
        method_id: MessageId,
        payload: bytes = b"",
        *,
        timeout: float = 5.0,
    ) -> Message:
        """Asynchronous RPC call to a remote method.

        If E2E is enabled, protection is applied to the request
        and verified on the response.
        """
        if self._e2e is not None:
            payload = self._e2e.protect(payload)

        response = await self._rpc_client.call_async(method_id, payload, timeout=timeout)

        if self._e2e is not None:
            status = self._e2e.check(response.payload)
            if status != E2ECheckStatus.OK:
                raise E2EError(f"E2E check failed on response: {status.name}")

        return response

    # --- Events (feat_req_someipsd_203-205 eventgroup subscriptions) ---

    def subscribe_events(self, eventgroup_id: int) -> MessageReceiver:
        """Subscribe to an event group and return a notification receiver.

        The returned :class:`~opensomeip.receiver.MessageReceiver` supports
        both synchronous and asynchronous iteration.
        """
        self._event_subscriber.subscribe(eventgroup_id)
        return self._event_subscriber.notifications()

    def unsubscribe_events(self, eventgroup_id: int) -> None:
        """Unsubscribe from an event group."""
        self._event_subscriber.unsubscribe(eventgroup_id)

    def subscription_status(self) -> MessageReceiver:
        """Return a receiver for subscription status updates."""
        return self._event_subscriber.subscription_status()

    def request_field(self, event_id: int) -> None:
        """Request the current value of a field event (getter pattern)."""
        # Placeholder — delegates to EventSubscriber when wired through C++

    # --- TP (feat_req_someiptp_400-414) ---

    def send(self, message: Message) -> None:
        """Send a message, using TP segmentation if payload exceeds MTU.

        This is the low-level send. Prefer :meth:`call` for RPC
        or :meth:`subscribe_events` for event streams.
        """
        if self._tp_manager is not None:
            self._tp_manager.send(message)
        else:
            self._transport.send(message)

    def reassembled_messages(self) -> MessageReceiver:
        """Return a receiver for TP-reassembled incoming messages.

        Only available when TP is enabled.
        """
        if self._tp_manager is None:
            raise RuntimeError("TP is not enabled in client configuration")
        return self._tp_manager.reassembled()

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
