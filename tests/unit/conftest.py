"""Unit test configuration — force pure-Python path.

Unit tests validate Python-level behaviour and must not depend on
native transport I/O, which may block on some platforms (e.g. Windows).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from opensomeip._bridge import get_ext


@pytest.fixture(autouse=True)
def _no_native_ext() -> None:  # type: ignore[misc]
    """Ensure ``get_ext()`` returns ``None`` for every unit test."""
    get_ext.cache_clear()
    with patch("opensomeip._bridge._load_extension", return_value=None):
        yield  # type: ignore[misc]
    get_ext.cache_clear()
