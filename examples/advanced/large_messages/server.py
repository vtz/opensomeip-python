#!/usr/bin/env python3
"""Large Messages Server -- Python equivalent of the C++ large_messages/server.

Service 0x5000 with three methods demonstrating TP segmentation:
  0x0001  SEND_LARGE_DATA(uint32 size) -> bytes   -- generates test data
  0x0002  RECEIVE_LARGE_DATA(bytes) -> string      -- verifies data integrity
  0x0003  ECHO_LARGE_DATA(bytes) -> bytes           -- echoes payload back

Wire format: 4-byte big-endian size prefix, then test data = repeating 0x00..0xFF.

Interop:
    # Terminal 1 -- this Python server
    python examples/advanced/large_messages/server.py

    # Terminal 2 -- C++ client  (or the Python client)
    ./build/examples/advanced/large_messages/large_messages_client
    python examples/advanced/large_messages/client.py
"""

from __future__ import annotations

import signal
import struct

from opensomeip.message import Message
from opensomeip.tp import TpManager
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageType, ReturnCode

LARGE_DATA_SERVICE_ID = 0x5000
SEND_LARGE_DATA = 0x0001
RECEIVE_LARGE_DATA = 0x0002
ECHO_LARGE_DATA = 0x0003

PORT = 30495

def generate_test_data(size: int) -> bytes:
    """Generate a repeating 0x00..0xFF pattern of the given size."""
    pattern = bytes(range(256))
    full, remainder = divmod(size, 256)
    return pattern * full + pattern[:remainder]


def verify_test_data(data: bytes) -> bool:
    """Verify data matches the expected repeating pattern."""
    return all(byte == i % 256 for i, byte in enumerate(data))


def handle_send_large_data(payload: bytes) -> bytes:
    if len(payload) < 4:
        return b""
    (size,) = struct.unpack("!I", payload[:4])
    print(f"SEND_LARGE_DATA: Generating {size} bytes of test data")
    return generate_test_data(size)


def handle_receive_large_data(payload: bytes) -> bytes:
    ok = verify_test_data(payload)
    status = "valid" if ok else "CORRUPTED"
    print(f"RECEIVE_LARGE_DATA: Received {len(payload)} bytes -- {status}")
    response = f"Received {len(payload)} bytes, integrity: {status}"
    return response.encode("utf-8")


def handle_echo_large_data(payload: bytes) -> bytes:
    print(f"ECHO_LARGE_DATA: Echoing {len(payload)} bytes")
    return payload


HANDLERS = {
    SEND_LARGE_DATA: handle_send_large_data,
    RECEIVE_LARGE_DATA: handle_receive_large_data,
    ECHO_LARGE_DATA: handle_echo_large_data,
}


def main() -> None:
    transport = UdpTransport(local_endpoint=Endpoint("0.0.0.0", PORT))
    tp = TpManager(transport=transport, mtu=1400)

    def shutdown(*_: object) -> None:
        print("\nShutting down...")
        tp.stop()
        transport.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("=== SOME/IP Large Messages Server (Python) ===")
    print(f"Service 0x{LARGE_DATA_SERVICE_ID:04X} on port {PORT}")
    print("Methods:")
    print(f"  0x{SEND_LARGE_DATA:04X}: send_large_data(size) -> bytes")
    print(f"  0x{RECEIVE_LARGE_DATA:04X}: receive_large_data(bytes) -> status")
    print(f"  0x{ECHO_LARGE_DATA:04X}: echo_large_data(bytes) -> bytes")
    print("Press Ctrl+C to exit\n")

    transport.start()
    tp.start()

    for msg in transport.receiver:
        if (
            msg.message_id.service_id == LARGE_DATA_SERVICE_ID
            and msg.message_type == MessageType.REQUEST
        ):
            handler = HANDLERS.get(msg.message_id.method_id)
            if handler is not None:
                result_payload = handler(msg.payload)
                response = Message(
                    message_id=msg.message_id,
                    request_id=msg.request_id,
                    message_type=MessageType.RESPONSE,
                    return_code=ReturnCode.E_OK,
                    payload=result_payload,
                )
                tp.send(response, endpoint=msg.source_endpoint)

    tp.stop()
    transport.stop()
    print("Server stopped.")


if __name__ == "__main__":
    main()
