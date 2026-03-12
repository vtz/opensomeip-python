"""Tests for opensomeip._logging — C++ log bridge."""

from __future__ import annotations

import logging

import pytest

from opensomeip import _logging


class TestOnCppLog:
    """Test _on_cpp_log callback with different levels."""

    def test_level_0_maps_to_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.DEBUG, logger="opensomeip"):
            _logging._on_cpp_log(0, "transport", "trace message")
        assert "trace message" in caplog.text
        assert caplog.records[0].levelno == logging.DEBUG

    def test_level_1_maps_to_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.DEBUG, logger="opensomeip"):
            _logging._on_cpp_log(1, "sd", "debug message")
        assert "debug message" in caplog.text
        assert caplog.records[0].levelno == logging.DEBUG

    def test_level_2_maps_to_info(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="opensomeip"):
            _logging._on_cpp_log(2, "rpc", "info message")
        assert "info message" in caplog.text
        assert caplog.records[0].levelno == logging.INFO

    def test_level_3_maps_to_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.WARNING, logger="opensomeip"):
            _logging._on_cpp_log(3, "transport", "warning message")
        assert "warning message" in caplog.text
        assert caplog.records[0].levelno == logging.WARNING

    def test_level_4_maps_to_error(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.ERROR, logger="opensomeip"):
            _logging._on_cpp_log(4, "sd", "error message")
        assert "error message" in caplog.text
        assert caplog.records[0].levelno == logging.ERROR

    def test_level_5_maps_to_critical(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.CRITICAL, logger="opensomeip"):
            _logging._on_cpp_log(5, "rpc", "critical message")
        assert "critical message" in caplog.text
        assert caplog.records[0].levelno == logging.CRITICAL

    def test_unknown_level_maps_to_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.DEBUG, logger="opensomeip"):
            _logging._on_cpp_log(99, "unknown", "unknown level message")
        assert "unknown level message" in caplog.text
        assert caplog.records[0].levelno == logging.DEBUG

    def test_component_in_message(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="opensomeip"):
            _logging._on_cpp_log(2, "my_component", "test")
        assert "[my_component]" in caplog.text


class TestCppToPythonLevel:
    """Test _CPP_TO_PYTHON_LEVEL mapping."""

    def test_mapping_completeness(self) -> None:
        assert _logging._CPP_TO_PYTHON_LEVEL[0] == logging.DEBUG
        assert _logging._CPP_TO_PYTHON_LEVEL[1] == logging.DEBUG
        assert _logging._CPP_TO_PYTHON_LEVEL[2] == logging.INFO
        assert _logging._CPP_TO_PYTHON_LEVEL[3] == logging.WARNING
        assert _logging._CPP_TO_PYTHON_LEVEL[4] == logging.ERROR
        assert _logging._CPP_TO_PYTHON_LEVEL[5] == logging.CRITICAL


class TestConfigureLogging:
    """Test configure_logging."""

    def test_sets_level_and_handler(self) -> None:
        logger = logging.getLogger("opensomeip")
        # Clear handlers from previous tests
        logger.handlers.clear()
        _logging.configure_logging(level=logging.WARNING)
        assert logger.level == logging.WARNING
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_does_not_duplicate_handlers_on_second_call(self) -> None:
        logger = logging.getLogger("opensomeip")
        logger.handlers.clear()
        _logging.configure_logging(level=logging.INFO)
        handler_count = len(logger.handlers)
        _logging.configure_logging(level=logging.DEBUG)
        assert len(logger.handlers) == handler_count
