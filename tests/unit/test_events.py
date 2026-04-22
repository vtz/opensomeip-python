"""Tests for opensomeip.events — EventPublisher, EventSubscriber."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from opensomeip.events import (
    EventPublisher,
    EventSubscriber,
    SubscriptionState,
    SubscriptionStatus,
)
from opensomeip.exceptions import ConfigurationError
from opensomeip.receiver import MessageReceiver
from opensomeip.transport import Endpoint, UdpTransport


@pytest.fixture()
def transport() -> UdpTransport:
    t = UdpTransport(Endpoint("0.0.0.0", 0))
    t.start()
    return t


class TestEventPublisher:
    def test_lifecycle(self, transport: UdpTransport) -> None:
        pub = EventPublisher(transport)
        assert pub.is_running is False
        pub.start()
        assert pub.is_running is True
        pub.stop()
        assert pub.is_running is False

    def test_context_manager(self, transport: UdpTransport) -> None:
        with EventPublisher(transport) as pub:
            assert pub.is_running is True
        assert pub.is_running is False

    def test_notify_raises_without_native(self, transport: UdpTransport) -> None:
        """notify() raises RuntimeError when the C++ extension is unavailable."""
        with patch("opensomeip.events.get_ext", return_value=None):
            pub = EventPublisher(transport)
            pub.start()
            pub.register_event(event_id=0x8001, eventgroup_id=0x0001)
            with pytest.raises(RuntimeError, match="C\\+\\+ extension is not available"):
                pub.notify(event_id=0x8001, payload=b"\x01\x02")
            pub.stop()

    def test_set_field_raises_without_native(self, transport: UdpTransport) -> None:
        """set_field() raises RuntimeError when the C++ extension is unavailable."""
        with patch("opensomeip.events.get_ext", return_value=None):
            pub = EventPublisher(transport)
            pub.start()
            with pytest.raises(RuntimeError, match="C\\+\\+ extension is not available"):
                pub.set_field(event_id=0x8001, payload=b"\x01")
            pub.stop()

    def test_notify_unregistered_event(self, transport: UdpTransport) -> None:
        pub = EventPublisher(transport)
        pub.start()
        with pytest.raises(ConfigurationError, match="not registered"):
            pub.notify(event_id=0x9999, payload=b"\x01")
        pub.stop()

    def test_stop_clears_events(self, transport: UdpTransport) -> None:
        pub = EventPublisher(transport)
        pub.register_event(0x8001, 0x0001)
        pub.stop()
        with pytest.raises(ConfigurationError):
            pub.notify(0x8001, b"")

    @pytest.mark.asyncio
    async def test_async_context_manager(self, transport: UdpTransport) -> None:
        async with EventPublisher(transport) as pub:
            assert pub.is_running is True


class TestEventSubscriber:
    def test_lifecycle(self, transport: UdpTransport) -> None:
        sub = EventSubscriber(transport)
        sub.start()
        assert sub.is_running is True
        sub.stop()
        assert sub.is_running is False

    def test_context_manager(self, transport: UdpTransport) -> None:
        with EventSubscriber(transport) as sub:
            assert sub.is_running is True
        assert sub.is_running is False

    def test_subscribe_raises_without_native(self, transport: UdpTransport) -> None:
        """subscribe() raises RuntimeError when the C++ extension is unavailable."""
        with patch("opensomeip.events.get_ext", return_value=None):
            sub = EventSubscriber(transport)
            with pytest.raises(RuntimeError, match="C\\+\\+ extension is not available"):
                sub.subscribe(0x0001)

    def test_notifications_returns_receiver(self, transport: UdpTransport) -> None:
        sub = EventSubscriber(transport)
        receiver = sub.notifications()
        assert isinstance(receiver, MessageReceiver)

    def test_subscription_status_returns_receiver(self, transport: UdpTransport) -> None:
        sub = EventSubscriber(transport)
        status_receiver = sub.subscription_status()
        assert isinstance(status_receiver, MessageReceiver)

    def test_stop_closes_notification_receiver(self, transport: UdpTransport) -> None:
        sub = EventSubscriber(transport)
        receiver = sub.notifications()
        sub.start()
        sub.stop()
        assert receiver.closed is True


class TestSubscriptionStatus:
    def test_construction(self) -> None:
        ss = SubscriptionStatus(
            service_id=0x1234,
            instance_id=0x0001,
            eventgroup_id=0x0001,
            state=SubscriptionState.SUBSCRIBED,
        )
        assert ss.state == SubscriptionState.SUBSCRIBED

    def test_states(self) -> None:
        assert SubscriptionState.PENDING == 0
        assert SubscriptionState.SUBSCRIBED == 1
        assert SubscriptionState.NOT_SUBSCRIBED == 2
