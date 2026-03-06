"""Shared test fixtures for opensomeip tests."""

from __future__ import annotations

import pytest

from opensomeip.message import Message
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode


@pytest.fixture()
def sample_message_id() -> MessageId:
    return MessageId(service_id=0x1234, method_id=0x0001)


@pytest.fixture()
def sample_request_id() -> RequestId:
    return RequestId(client_id=0x0010, session_id=0x0001)


@pytest.fixture()
def sample_message(sample_message_id: MessageId, sample_request_id: RequestId) -> Message:
    return Message(
        message_id=sample_message_id,
        request_id=sample_request_id,
        message_type=MessageType.REQUEST,
        return_code=ReturnCode.E_OK,
        payload=b"\x01\x02\x03\x04",
    )
