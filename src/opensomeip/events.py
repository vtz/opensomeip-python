"""Pythonic wrappers for SOME/IP event publishing and subscribing.

When the C++ extension is available, delegates to the native event
implementations. Otherwise, provides stub behavior for testing.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self

from opensomeip._bridge import get_ext
from opensomeip.receiver import MessageReceiver
from opensomeip.transport import Transport
from opensomeip.types import MessageId


class SubscriptionState(enum.IntEnum):
    """Subscription status for an event group."""

    PENDING = 0
    SUBSCRIBED = 1
    NOT_SUBSCRIBED = 2


@dataclass(frozen=True, slots=True)
class SubscriptionStatus:
    """Status update for an event group subscription."""

    service_id: int
    instance_id: int
    eventgroup_id: int
    state: SubscriptionState


class EventPublisher:
    """SOME/IP Event Publisher — registers events and sends notifications.

    When the C++ extension is available, delegates to the native
    ``_opensomeip.events.EventPublisher``.
    """

    def __init__(
        self,
        transport: Transport,
        *,
        service_id: int = 0x0000,
        instance_id: int = 0x0001,
    ) -> None:
        self._transport = transport
        self._running = False
        self._registered_events: dict[int, int] = {}
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            self._cpp = ext.events.EventPublisher(service_id, instance_id)

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the event publisher."""
        if self._cpp is not None:
            try:
                self._cpp.initialize()
            except Exception:
                pass
        self._running = True

    def stop(self) -> None:
        """Stop the event publisher."""
        if self._cpp is not None:
            try:
                self._cpp.shutdown()
            except Exception:
                pass
        self._running = False
        self._registered_events.clear()

    def register_event(self, event_id: int, eventgroup_id: int) -> None:
        """Register an event within an event group."""
        self._registered_events[event_id] = eventgroup_id

        if self._cpp is not None:
            ext = get_ext()
            cfg = ext.events.EventConfig()
            cfg.event_id = event_id
            cfg.eventgroup_id = eventgroup_id
            self._cpp.register_event(cfg)

    def notify(self, event_id: int, payload: bytes) -> None:
        """Publish a notification for a registered event."""
        from opensomeip.message import Message
        from opensomeip.types import MessageType, ReturnCode

        if event_id not in self._registered_events:
            from opensomeip.exceptions import ConfigurationError

            raise ConfigurationError(f"Event {event_id:#06x} is not registered")

        if self._cpp is not None:
            data = list(payload)
            self._cpp.publish_event(event_id, data)
            return

        msg = Message(
            message_id=MessageId(service_id=0, method_id=event_id),
            message_type=MessageType.NOTIFICATION,
            return_code=ReturnCode.E_OK,
            payload=payload,
        )
        self._transport.send(msg)

    def set_field(self, event_id: int, payload: bytes) -> None:
        """Set the value of a field event (getter/setter pattern)."""
        if self._cpp is not None:
            data = list(payload)
            self._cpp.publish_field(event_id, data)

    def get_statistics(self) -> Any:
        """Return event publisher statistics (native only)."""
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


class EventSubscriber:
    """SOME/IP Event Subscriber — subscribes to event groups and receives notifications.

    When the C++ extension is available, delegates to the native
    ``_opensomeip.events.EventSubscriber``.
    """

    def __init__(
        self,
        transport: Transport,
        *,
        client_id: int = 0x0001,
    ) -> None:
        self._transport = transport
        self._running = False
        self._notification_receiver = MessageReceiver()
        self._status_receiver: MessageReceiver | None = None
        self._subscribed_groups: set[int] = set()
        self._cpp: Any = None
        ext = get_ext()
        if ext is not None:
            self._cpp = ext.events.EventSubscriber(client_id)

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the event subscriber."""
        if self._cpp is not None:
            try:
                self._cpp.initialize()
            except Exception:
                pass
        self._running = True

    def stop(self) -> None:
        """Stop the event subscriber and close receivers."""
        if self._cpp is not None:
            try:
                self._cpp.shutdown()
            except Exception:
                pass
        self._running = False
        self._notification_receiver.close()
        if self._status_receiver is not None:
            self._status_receiver.close()
        self._subscribed_groups.clear()

    def subscribe(
        self,
        eventgroup_id: int,
        *,
        service_id: int = 0xFFFF,
        instance_id: int = 0xFFFF,
    ) -> None:
        """Subscribe to an event group."""
        self._subscribed_groups.add(eventgroup_id)

        if self._cpp is not None:
            receiver = self._notification_receiver

            def _on_notification(cpp_notif: Any) -> None:
                from opensomeip.message import Message

                payload = bytes(cpp_notif.event_data) if cpp_notif.event_data else b""
                msg = Message(
                    message_id=MessageId(
                        service_id=cpp_notif.service_id,
                        method_id=cpp_notif.event_id,
                    ),
                    payload=payload,
                )
                receiver.put(msg)

            self._cpp.subscribe_eventgroup(
                service_id,
                instance_id,
                eventgroup_id,
                _on_notification,
            )

    def unsubscribe(
        self,
        eventgroup_id: int,
        *,
        service_id: int = 0xFFFF,
        instance_id: int = 0xFFFF,
    ) -> None:
        """Unsubscribe from an event group."""
        self._subscribed_groups.discard(eventgroup_id)
        if self._cpp is not None:
            self._cpp.unsubscribe_eventgroup(service_id, instance_id, eventgroup_id)

    def notifications(self) -> MessageReceiver:
        """Return an async-iterable :class:`MessageReceiver` of event notifications."""
        return self._notification_receiver

    def subscription_status(self) -> MessageReceiver:
        """Return a :class:`MessageReceiver` of subscription status updates."""
        if self._status_receiver is None:
            self._status_receiver = MessageReceiver()
        return self._status_receiver

    def get_statistics(self) -> Any:
        """Return event subscriber statistics (native only)."""
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
