"""Pythonic wrappers for SOME/IP Service Discovery (SD).

Provides :class:`SdServer` (offer/stop-offer) and :class:`SdClient`
(find/subscribe) with context managers and async iterator interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip.receiver import MessageReceiver
from opensomeip.transport import Endpoint


@dataclass(frozen=True, slots=True)
class ServiceInstance:
    """Identifies a SOME/IP service instance."""

    service_id: int
    instance_id: int
    major_version: int = 1
    minor_version: int = 0

    def __repr__(self) -> str:
        return (
            f"ServiceInstance(service={self.service_id:#06x}, "
            f"instance={self.instance_id:#06x}, "
            f"v{self.major_version}.{self.minor_version})"
        )


@dataclass(slots=True)
class SdConfig:
    """Configuration for Service Discovery."""

    multicast_endpoint: Endpoint
    unicast_endpoint: Endpoint
    initial_delay_min_ms: int = 10
    initial_delay_max_ms: int = 50
    repetitions_base_delay_ms: int = 30
    repetitions_max: int = 3
    cyclic_offer_delay_ms: int = 1000
    ttl: int = 3


class SdServer:
    """SOME/IP SD Server — offers services for discovery.

    Lifecycle is explicit via :meth:`start` / :meth:`stop`, or use as a
    context manager.
    """

    def __init__(self, config: SdConfig) -> None:
        self._config = config
        self._running = False
        self._offered: set[ServiceInstance] = set()

    @property
    def config(self) -> SdConfig:
        return self._config

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def offered_services(self) -> frozenset[ServiceInstance]:
        return frozenset(self._offered)

    def start(self) -> None:
        """Start the SD server. In full implementation, delegates to C++ with GIL released."""
        self._running = True

    def stop(self) -> None:
        """Stop the SD server and withdraw all offers."""
        self._offered.clear()
        self._running = False

    def offer(self, service: ServiceInstance) -> None:
        """Offer a service instance for discovery."""
        self._offered.add(service)

    def stop_offer(self, service: ServiceInstance) -> None:
        """Withdraw a service offer."""
        self._offered.discard(service)

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        self.stop()


class SdClient:
    """SOME/IP SD Client — finds and subscribes to services.

    Lifecycle is explicit via :meth:`start` / :meth:`stop`, or use as a
    context manager.
    """

    def __init__(self, config: SdConfig) -> None:
        self._config = config
        self._running = False
        self._find_receiver: MessageReceiver | None = None

    @property
    def config(self) -> SdConfig:
        return self._config

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the SD client. In full implementation, delegates to C++ with GIL released."""
        self._running = True

    def stop(self) -> None:
        """Stop the SD client."""
        self._running = False
        if self._find_receiver is not None:
            self._find_receiver.close()

    def find(
        self,
        service: ServiceInstance,
        callback: Callable[[ServiceInstance], None] | None = None,
    ) -> MessageReceiver:
        """Find a service on the network.

        Returns a :class:`MessageReceiver` that yields discovery results.
        Optionally takes a callback for push-style notification.
        """
        self._find_receiver = MessageReceiver()
        return self._find_receiver

    def subscribe(
        self,
        service: ServiceInstance,
        eventgroup_id: int,
        callback: Callable[..., None] | None = None,
    ) -> None:
        """Subscribe to an event group of a service."""

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
