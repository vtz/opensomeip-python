"""Pythonic wrappers for SOME/IP E2E (End-to-End) protection.

When the C++ extension is available, delegates to the native E2E
implementations. Otherwise, provides pure-Python behavior.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from opensomeip._bridge import get_ext


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

    Subclass this to implement custom E2E profiles. When the C++ extension
    is available, the ``PyE2EProfile`` trampoline bridges Python subclasses
    to the C++ ``E2EProfile`` virtual interface.
    """

    @abstractmethod
    def protect(self, data: bytearray, counter: int) -> bytearray:
        """Apply E2E protection to the data."""

    @abstractmethod
    def check(self, data: bytes, counter: int) -> E2ECheckStatus:
        """Verify E2E protection on received data."""


class E2EProtection:
    """Applies and verifies E2E protection on SOME/IP messages.

    When the C++ extension is available, delegates to the native
    ``_opensomeip.e2e.E2EProtection``.
    """

    def __init__(self, config: E2EConfig, profile: E2EProfile | None = None) -> None:
        self._config = config
        self._profile = profile
        self._counter = 0
        self._cpp: Any = None
        self._cpp_config: Any = None

    @property
    def config(self) -> E2EConfig:
        return self._config

    def protect(self, payload: bytes) -> bytes:
        """Apply E2E protection to a payload."""
        if self._profile is None:
            return payload
        data = bytearray(payload)
        result = self._profile.protect(data, self._counter)
        self._counter = (self._counter + 1) & 0xFF
        return bytes(result)

    def check(self, payload: bytes) -> E2ECheckStatus:
        """Verify E2E protection on a received payload."""
        if self._profile is None:
            return E2ECheckStatus.OK
        return self._profile.check(payload, self._counter)


def crc8(data: bytes) -> int:
    """Compute CRC-8/SAE-J1850 (used by E2E Profile 01)."""
    ext = get_ext()
    if ext is not None:
        return int(ext.e2e.calculate_crc8_sae_j1850(list(data)))

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


def crc16(data: bytes) -> int:
    """Compute CRC-16/ITU-T X.25."""
    ext = get_ext()
    if ext is not None:
        return int(ext.e2e.calculate_crc16_itu_x25(list(data)))

    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc ^ 0xFFFF


def crc32(data: bytes) -> int:
    """Compute CRC-32 (used by E2E Profile 04/22)."""
    ext = get_ext()
    if ext is not None:
        return int(ext.e2e.calculate_crc32(list(data)))

    import binascii

    return binascii.crc32(data) & 0xFFFFFFFF
