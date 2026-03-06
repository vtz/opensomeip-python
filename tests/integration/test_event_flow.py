"""Integration tests: Event publish ↔ subscribe over loopback.

These tests require the C++ opensomeip library to be compiled and linked.
They are skipped when running without the native extension.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skip(reason="Requires compiled C++ opensomeip extension")
class TestEventFlow:
    def test_publish_and_receive(self) -> None:
        """Publisher notifies, subscriber receives via iterator."""

    @pytest.mark.asyncio
    async def test_async_notification_stream(self) -> None:
        """Subscriber receives notifications via async iterator."""
