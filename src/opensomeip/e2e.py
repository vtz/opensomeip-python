"""Pythonic wrappers for SOME/IP E2E (End-to-End) protection.

Provides :class:`E2EProtection` for applying and verifying E2E headers,
:class:`E2EConfig` for configuration, and a base class :class:`E2EProfile`
for custom protection profiles.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass


class E2EProfileId(enum.IntEnum):
    """Standard E2E protection profile identifiers."""

    PROFILE_01 = 1
    PROFILE_02 = 2
    PROFILE_04 = 4
    PROFILE_05 = 5
    PROFILE_06 = 6
    PROFILE_07 = 7
    PROFILE_11 = 11
    PROFILE_22 = 22


class E2ECheckStatus(enum.IntEnum):
    """Result of an E2E check."""

    OK = 0
    REPEATED = 1
    WRONG_SEQUENCE = 2
    ERROR = 3
    NOT_AVAILABLE = 4
    NO_NEW_DATA = 5


@dataclass(slots=True)
class E2EConfig:
    """Configuration for E2E protection."""

    profile_id: E2EProfileId
    data_id: int
    data_length: int
    max_delta_counter: int = 15
    crc_offset: int = 0
    counter_offset: int = 0


class E2EProfile(ABC):
    """Base class for E2E protection profiles.

    Subclass this to implement custom E2E profiles. In the full implementation,
    a ``PyE2EProfile`` trampoline class bridges Python subclasses to C++.
    """

    @abstractmethod
    def protect(self, data: bytearray, counter: int) -> bytearray:
        """Apply E2E protection to the data.

        Args:
            data: The payload to protect (mutable).
            counter: The current message counter.

        Returns:
            The protected payload with E2E header/CRC applied.
        """

    @abstractmethod
    def check(self, data: bytes, counter: int) -> E2ECheckStatus:
        """Verify E2E protection on received data.

        Args:
            data: The received payload to verify.
            counter: The expected message counter.

        Returns:
            The check status indicating whether the data is valid.
        """


class E2EProtection:
    """Applies and verifies E2E protection on SOME/IP messages.

    Uses a configured :class:`E2EConfig` and an :class:`E2EProfile`
    implementation (built-in or custom).
    """

    def __init__(self, config: E2EConfig, profile: E2EProfile | None = None) -> None:
        self._config = config
        self._profile = profile
        self._counter = 0

    @property
    def config(self) -> E2EConfig:
        return self._config

    def protect(self, payload: bytes) -> bytes:
        """Apply E2E protection to a payload.

        In the full implementation, this delegates to the C++ E2E library.
        """
        if self._profile is None:
            return payload
        data = bytearray(payload)
        result = self._profile.protect(data, self._counter)
        self._counter = (self._counter + 1) & 0xFF
        return bytes(result)

    def check(self, payload: bytes) -> E2ECheckStatus:
        """Verify E2E protection on a received payload.

        In the full implementation, this delegates to the C++ E2E library.
        """
        if self._profile is None:
            return E2ECheckStatus.OK
        return self._profile.check(payload, self._counter)


def crc8(data: bytes) -> int:
    """Compute CRC-8/SAE-J1850 (used by E2E Profile 01)."""
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x1D
            else:
                crc <<= 1
            crc &= 0xFF
    return crc ^ 0xFF


def crc32(data: bytes) -> int:
    """Compute CRC-32/AUTOSAR (used by E2E Profile 04/22)."""
    import binascii

    return binascii.crc32(data) & 0xFFFFFFFF
