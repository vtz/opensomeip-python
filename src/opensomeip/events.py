"""Pythonic wrappers for SOME/IP event publishing and subscribing.

Provides :class:`EventPublisher` and :class:`EventSubscriber` with
iterator interfaces for continuous event streams.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

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

    Lifecycle is explicit via :meth:`start` / :meth:`stop`, or use as a
    context manager.
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._running = False
        self._registered_events: dict[int, int] = {}

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the event publisher."""
        self._running = True

    def stop(self) -> None:
        """Stop the event publisher."""
        self._running = False
        self._registered_events.clear()

    def register_event(self, event_id: int, eventgroup_id: int) -> None:
        """Register an event within an event group."""
        self._registered_events[event_id] = eventgroup_id

    def notify(self, event_id: int, payload: bytes) -> None:
        """Publish a notification for a registered event.

        In the full implementation, this delegates to C++ ``EventPublisher::notify()``
        with the GIL released.
        """
        from opensomeip.message import Message
        from opensomeip.types import MessageType, ReturnCode

        if event_id not in self._registered_events:
            from opensomeip.exceptions import ConfigurationError

            raise ConfigurationError(f"Event {event_id:#06x} is not registered")

        msg = Message(
            message_id=MessageId(service_id=0, method_id=event_id),
            message_type=MessageType.NOTIFICATION,
            return_code=ReturnCode.E_OK,
            payload=payload,
        )
        self._transport.send(msg)

    def set_field(self, event_id: int, payload: bytes) -> None:
        """Set the value of a field event (getter/setter pattern).

        In the full implementation, this delegates to C++ ``EventPublisher::set_field()``.
        """

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

    Provides async iterator access to notification streams via :meth:`notifications`
    and subscription status updates via :meth:`subscription_status`.
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._running = False
        self._notification_receiver = MessageReceiver()
        self._status_receiver: MessageReceiver | None = None
        self._subscribed_groups: set[int] = set()

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the event subscriber."""
        self._running = True

    def stop(self) -> None:
        """Stop the event subscriber and close receivers."""
        self._running = False
        self._notification_receiver.close()
        if self._status_receiver is not None:
            self._status_receiver.close()
        self._subscribed_groups.clear()

    def subscribe(self, eventgroup_id: int) -> None:
        """Subscribe to an event group.

        In the full implementation, this delegates to C++ with the GIL released.
        """
        self._subscribed_groups.add(eventgroup_id)

    def unsubscribe(self, eventgroup_id: int) -> None:
        """Unsubscribe from an event group."""
        self._subscribed_groups.discard(eventgroup_id)

    def notifications(self) -> MessageReceiver:
        """Return an async-iterable :class:`MessageReceiver` of event notifications."""
        return self._notification_receiver

    def subscription_status(self) -> MessageReceiver:
        """Return a :class:`MessageReceiver` of subscription status updates."""
        if self._status_receiver is None:
            self._status_receiver = MessageReceiver()
        return self._status_receiver

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
