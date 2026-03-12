"""Pythonic wrappers for SOME/IP Service Discovery (SD).

When the C++ extension is available, delegates to the native SD
implementations. Otherwise, provides stub behavior for testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip._bridge import (
    from_cpp_service_instance,
    get_ext,
    to_cpp_sd_config,
    to_cpp_service_instance,
)
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

    When the C++ extension is available, delegates to the native
    ``_opensomeip.sd.SdServer``.
    """

    def __init__(self, config: SdConfig) -> None:
        self._config = config
        self._running = False
        self._offered: set[ServiceInstance] = set()
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            cpp_cfg = to_cpp_sd_config(config)
            self._cpp = ext.sd.SdServer(cpp_cfg)

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
        """Start the SD server."""
        if self._cpp is not None:
            try:
                self._cpp.initialize()
            except Exception:
                pass
        self._running = True

    def stop(self) -> None:
        """Stop the SD server and withdraw all offers."""
        if self._cpp is not None:
            try:
                self._cpp.shutdown()
            except Exception:
                pass
        self._offered.clear()
        self._running = False

    def offer(self, service: ServiceInstance) -> None:
        """Offer a service instance for discovery."""
        if self._cpp is not None:
            try:
                cpp_svc = to_cpp_service_instance(service)
                self._cpp.offer_service(
                    cpp_svc,
                    f"{self._config.unicast_endpoint.ip}:{self._config.unicast_endpoint.port}",
                )
            except Exception:
                pass
        self._offered.add(service)

    def stop_offer(self, service: ServiceInstance) -> None:
        """Withdraw a service offer."""
        if self._cpp is not None:
            try:
                self._cpp.stop_offer_service(service.service_id, service.instance_id)
            except Exception:
                pass
        self._offered.discard(service)

    def get_statistics(self) -> Any:
        """Return SD server statistics (native only)."""
        if self._cpp is not None:
            return self._cpp.get_statistics()
        return None

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

    When the C++ extension is available, delegates to the native
    ``_opensomeip.sd.SdClient``.
    """

    def __init__(self, config: SdConfig) -> None:
        self._config = config
        self._running = False
        self._find_receiver: MessageReceiver | None = None
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            cpp_cfg = to_cpp_sd_config(config)
            self._cpp = ext.sd.SdClient(cpp_cfg)

    @property
    def config(self) -> SdConfig:
        return self._config

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the SD client."""
        if self._cpp is not None:
            try:
                self._cpp.initialize()
            except Exception:
                pass
        self._running = True

    def stop(self) -> None:
        """Stop the SD client."""
        if self._cpp is not None:
            try:
                self._cpp.shutdown()
            except Exception:
                pass
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
        """
        self._find_receiver = MessageReceiver()

        if self._cpp is not None:
            receiver = self._find_receiver

            def _on_found(cpp_svc: Any) -> None:
                py_svc = from_cpp_service_instance(cpp_svc)
                from opensomeip.message import Message

                msg = Message(payload=repr(py_svc).encode())
                receiver.put(msg)
                if callback is not None:
                    callback(py_svc)

            try:
                self._cpp.find_service(service.service_id, _on_found)
            except Exception:
                pass
        return self._find_receiver

    def subscribe(
        self,
        service: ServiceInstance,
        eventgroup_id: int,
        callback: Callable[..., None] | None = None,
    ) -> None:
        """Subscribe to an event group of a service."""
        if self._cpp is not None:
            self._cpp.subscribe_eventgroup(service.service_id, service.instance_id, eventgroup_id)

    def unsubscribe(
        self,
        service: ServiceInstance,
        eventgroup_id: int,
    ) -> None:
        """Unsubscribe from an event group of a service."""
        if self._cpp is not None:
            self._cpp.unsubscribe_eventgroup(
                service.service_id, service.instance_id, eventgroup_id
            )

    def get_statistics(self) -> Any:
        """Return SD client statistics (native only)."""
        if self._cpp is not None:
            return self._cpp.get_statistics()
        return None

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
