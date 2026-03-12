"""Bridge C++ opensomeip log output to Python's ``logging`` module.

When the C++ extension is available, registers a callback that routes
C++ log messages through Python's logging infrastructure.
"""

from __future__ import annotations

import logging

from opensomeip._bridge import get_ext

_logger = logging.getLogger("opensomeip")

_CPP_TO_PYTHON_LEVEL = {
    0: logging.DEBUG,
    1: logging.DEBUG,
    2: logging.INFO,
    3: logging.WARNING,
    4: logging.ERROR,
    5: logging.CRITICAL,
}


def _on_cpp_log(level: int, component: str, message: str) -> None:
    """Callback invoked from C++ when a log message is emitted.

    Args:
        level: C++ log level (0=trace .. 5=critical).
        component: The C++ component name (e.g. "transport", "sd").
        message: The log message text.
    """
    py_level = _CPP_TO_PYTHON_LEVEL.get(level, logging.DEBUG)
    _logger.log(py_level, "[%s] %s", component, message)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the opensomeip logger with a console handler.

    Also registers the C++ log callback if the extension is available.

    Convenience for quick setup. For production use, configure the
    ``"opensomeip"`` logger via standard Python logging configuration.
    """
    _logger.setLevel(level)
    if not _logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
        )
        _logger.addHandler(handler)

    ext = get_ext()
    if ext is not None and hasattr(ext, "set_log_callback"):
        ext.set_log_callback(_on_cpp_log)
