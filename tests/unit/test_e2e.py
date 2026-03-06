"""Tests for opensomeip.e2e — E2EProtection, E2EProfile, CRC functions."""

from __future__ import annotations

from opensomeip.e2e import (
    E2ECheckStatus,
    E2EConfig,
    E2EProfile,
    E2EProfileId,
    E2EProtection,
    crc8,
    crc32,
)


class TestE2EProfileId:
    def test_values(self) -> None:
        assert E2EProfileId.PROFILE_01 == 1
        assert E2EProfileId.PROFILE_04 == 4
        assert E2EProfileId.PROFILE_22 == 22


class TestE2ECheckStatus:
    def test_values(self) -> None:
        assert E2ECheckStatus.OK == 0
        assert E2ECheckStatus.ERROR == 3
        assert E2ECheckStatus.NO_NEW_DATA == 5


class TestE2EConfig:
    def test_construction(self) -> None:
        cfg = E2EConfig(
            profile_id=E2EProfileId.PROFILE_01,
            data_id=0x1234,
            data_length=16,
        )
        assert cfg.profile_id == E2EProfileId.PROFILE_01
        assert cfg.data_id == 0x1234
        assert cfg.max_delta_counter == 15


class TestE2EProtection:
    def test_no_profile_protect_passthrough(self) -> None:
        cfg = E2EConfig(profile_id=E2EProfileId.PROFILE_01, data_id=0, data_length=8)
        prot = E2EProtection(cfg)
        data = b"\x01\x02\x03"
        assert prot.protect(data) == data

    def test_no_profile_check_returns_ok(self) -> None:
        cfg = E2EConfig(profile_id=E2EProfileId.PROFILE_01, data_id=0, data_length=8)
        prot = E2EProtection(cfg)
        assert prot.check(b"\x01\x02\x03") == E2ECheckStatus.OK

    def test_custom_profile(self) -> None:
        class XorProfile(E2EProfile):
            def protect(self, data: bytearray, counter: int) -> bytearray:
                xor = 0
                for b in data:
                    xor ^= b
                data.append(xor)
                return data

            def check(self, data: bytes, counter: int) -> E2ECheckStatus:
                if len(data) < 2:
                    return E2ECheckStatus.ERROR
                xor = 0
                for b in data[:-1]:
                    xor ^= b
                if xor == data[-1]:
                    return E2ECheckStatus.OK
                return E2ECheckStatus.ERROR

        cfg = E2EConfig(profile_id=E2EProfileId.PROFILE_01, data_id=0, data_length=8)
        profile = XorProfile()
        prot = E2EProtection(cfg, profile=profile)

        original = b"\x01\x02\x03"
        protected = prot.protect(original)
        assert len(protected) == len(original) + 1

        assert profile.check(protected, 0) == E2ECheckStatus.OK
        assert profile.check(b"\x01\x02\xff\x00", 0) == E2ECheckStatus.ERROR


class TestCrcFunctions:
    def test_crc8_known_value(self) -> None:
        result = crc8(b"\x00")
        assert isinstance(result, int)
        assert 0 <= result <= 0xFF

    def test_crc8_deterministic(self) -> None:
        assert crc8(b"\x01\x02\x03") == crc8(b"\x01\x02\x03")

    def test_crc8_different_data(self) -> None:
        assert crc8(b"\x01") != crc8(b"\x02")

    def test_crc32_known_value(self) -> None:
        result = crc32(b"hello")
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFFFFFF

    def test_crc32_deterministic(self) -> None:
        assert crc32(b"test") == crc32(b"test")

    def test_crc32_different_data(self) -> None:
        assert crc32(b"abc") != crc32(b"xyz")
