"""Integration tests: RPC client ↔ server round-trip over loopback.

These tests require the C++ opensomeip library to be compiled and linked.
They are skipped when running without the native extension.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skip(reason="Requires compiled C++ opensomeip extension")
class TestRpcRoundTrip:
    def test_sync_call(self) -> None:
        """Client sends request, server responds, client receives response."""

    @pytest.mark.asyncio
    async def test_async_call(self) -> None:
        """Async variant of the sync call test."""

    def test_concurrent_calls(self) -> None:
        """Multiple concurrent RPC calls from different threads."""
