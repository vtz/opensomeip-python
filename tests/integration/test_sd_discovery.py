"""Integration tests: SD offer ↔ find over loopback/multicast.

These tests require the C++ opensomeip library to be compiled and linked.
Multicast tests may be skipped in CI environments.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.multicast]


@pytest.mark.skip(reason="Requires compiled C++ opensomeip extension")
class TestSdDiscovery:
    def test_offer_and_find(self) -> None:
        """SdServer offers a service, SdClient discovers it."""

    def test_stop_offer(self) -> None:
        """SdServer withdraws offer, SdClient stops receiving it."""
