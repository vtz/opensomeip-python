#!/usr/bin/env python3
"""Large Messages Client -- Python equivalent of the C++ large_messages/client.

Calls service 0x5000 to test large data transfers using TP segmentation:
  - Request 2 KB, 10 KB, 50 KB of generated data
  - Send 10 KB of data for verification
  - 15 KB echo round-trip

Interop:
    # Terminal 1 -- C++ server  (or the Python server)
    ./build/examples/advanced/large_messages/large_messages_server
    python examples/advanced/large_messages/server.py

    # Terminal 2 -- this Python client
    python examples/advanced/large_messages/client.py
"""

from __future__ import annotations

import queue
import struct

from opensomeip.message import Message
from opensomeip.tp import TpManager
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode

LARGE_DATA_SERVICE_ID = 0x5000
SEND_LARGE_DATA = 0x0001
RECEIVE_LARGE_DATA = 0x0002
ECHO_LARGE_DATA = 0x0003

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 30495
CLIENT_ID = 0xABCD

session_counter = 0


def next_session() -> int:
    global session_counter
    session_counter += 1
    return session_counter & 0xFFFF


def generate_test_data(size: int) -> bytes:
    """Generate a repeating 0x00..0xFF pattern of the given size."""
    pattern = bytes(range(256))
    full, remainder = divmod(size, 256)
    return pattern * full + pattern[:remainder]


def call_method(
    tp: TpManager,
    transport: UdpTransport,
    server_ep: Endpoint,
    method_id: int,
    payload: bytes = b"",
    timeout: float = 10.0,
) -> bytes | None:
    request = Message(
        message_id=MessageId(LARGE_DATA_SERVICE_ID, method_id),
        request_id=RequestId(client_id=CLIENT_ID, session_id=next_session()),
        message_type=MessageType.REQUEST,
        return_code=ReturnCode.E_OK,
        payload=payload,
    )
    tp.send(request)

    try:
        response = transport.receiver._sync_queue.get(timeout=timeout)
        if response.message_type == MessageType.RESPONSE:
            return response.payload
    except queue.Empty:
        pass
    return None


def test_request_data(
    tp: TpManager, transport: UdpTransport, server_ep: Endpoint, size: int
) -> None:
    print(f"\n--- Requesting {size:,} bytes ---")
    payload = struct.pack("!I", size)
    result = call_method(tp, transport, server_ep, SEND_LARGE_DATA, payload)
    if result:
        print(f"Received {len(result):,} bytes (expected {size:,})")
        ok = len(result) == size
        print(f"Size check: {'PASS' if ok else 'FAIL'}")
    else:
        print("Request timed out")


def test_send_data(tp: TpManager, transport: UdpTransport, server_ep: Endpoint, size: int) -> None:
    print(f"\n--- Sending {size:,} bytes for verification ---")
    data = generate_test_data(size)
    result = call_method(tp, transport, server_ep, RECEIVE_LARGE_DATA, data)
    if result:
        print(f"Server response: '{result.decode('utf-8', errors='replace')}'")
    else:
        print("Request timed out")


def test_echo(tp: TpManager, transport: UdpTransport, server_ep: Endpoint, size: int) -> None:
    print(f"\n--- Echo round-trip: {size:,} bytes ---")
    data = generate_test_data(size)
    result = call_method(tp, transport, server_ep, ECHO_LARGE_DATA, data)
    if result:
        ok = result == data
        print(f"Echo {len(result):,} bytes -- {'PASS' if ok else 'MISMATCH'}")
    else:
        print("Request timed out")


def main() -> None:
    server_ep = Endpoint(SERVER_HOST, SERVER_PORT)
    transport = UdpTransport(
        local_endpoint=Endpoint("0.0.0.0", 0),
        remote_endpoint=server_ep,
    )
    tp = TpManager(transport=transport, mtu=1400)

    print("=== SOME/IP Large Messages Client (Python) ===")
    print(f"Client ID: 0x{CLIENT_ID:04X}\n")

    transport.start()
    tp.start()

    test_request_data(tp, transport, server_ep, 2048)
    test_request_data(tp, transport, server_ep, 10240)
    test_request_data(tp, transport, server_ep, 51200)
    test_send_data(tp, transport, server_ep, 10240)
    test_echo(tp, transport, server_ep, 15360)

    print("\n=== All Tests Completed ===")

    tp.stop()
    transport.stop()
    print("\nClient finished.")


if __name__ == "__main__":
    main()
