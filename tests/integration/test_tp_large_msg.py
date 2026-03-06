"""Integration tests: TP segmentation round-trip.

These tests require the C++ opensomeip library to be compiled and linked.
They are skipped when running without the native extension.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skip(reason="Requires compiled C++ opensomeip extension")
class TestTpLargeMessage:
    def test_segment_and_reassemble(self) -> None:
        """Send message > MTU, verify it is segmented and reassembled correctly."""

    def test_multiple_concurrent_reassembly(self) -> None:
        """Multiple large messages reassembled concurrently."""
