#!/usr/bin/env python3
"""Calculator RPC Client -- Python equivalent of the C++ method_calls/client.

Calls service 0x2000 methods ADD, MULTIPLY, GET_STATS on UDP.
Wire format: big-endian integers (same as C++ client).

Interop:
    # Terminal 1 -- C++ server  (or the Python server)
    ./build/examples/basic/method_calls/method_calls_server
    python examples/basic/method_calls/server.py

    # Terminal 2 -- this Python client
    python examples/basic/method_calls/client.py
"""

from __future__ import annotations

import queue
import struct

from opensomeip.message import Message
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode

CALCULATOR_SERVICE_ID = 0x2000
ADD_METHOD_ID = 0x0001
MULTIPLY_METHOD_ID = 0x0002
GET_STATS_METHOD_ID = 0x0003

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 30491

CLIENT_ID = 0xABCD
session_counter = 0


def next_session() -> int:
    global session_counter
    session_counter += 1
    return session_counter & 0xFFFF


def call_method(
    transport: UdpTransport,
    server_ep: Endpoint,
    method_id: int,
    payload: bytes = b"",
    timeout: float = 5.0,
) -> bytes | None:
    request = Message(
        message_id=MessageId(CALCULATOR_SERVICE_ID, method_id),
        request_id=RequestId(client_id=CLIENT_ID, session_id=next_session()),
        message_type=MessageType.REQUEST,
        return_code=ReturnCode.E_OK,
        payload=payload,
    )
    transport.send(request, server_ep)

    try:
        response = transport.receiver._sync_queue.get(timeout=timeout)
        if (
            response.message_id.service_id == CALCULATOR_SERVICE_ID
            and response.message_id.method_id == method_id
            and response.message_type == MessageType.RESPONSE
        ):
            return response.payload
    except queue.Empty:
        pass
    return None


def test_add(transport: UdpTransport, server_ep: Endpoint, a: int, b: int) -> None:
    print(f"\n--- Testing ADD({a}, {b}) ---")
    payload = struct.pack("!ii", a, b)
    result = call_method(transport, server_ep, ADD_METHOD_ID, payload)
    if result and len(result) >= 4:
        (s,) = struct.unpack("!i", result[:4])
        print(f"Result: {a} + {b} = {s}")
    else:
        print("RPC call failed or timed out")


def test_multiply(transport: UdpTransport, server_ep: Endpoint, a: int, b: int) -> None:
    print(f"\n--- Testing MULTIPLY({a}, {b}) ---")
    payload = struct.pack("!ii", a, b)
    result = call_method(transport, server_ep, MULTIPLY_METHOD_ID, payload)
    if result and len(result) >= 4:
        (p,) = struct.unpack("!i", result[:4])
        print(f"Result: {a} * {b} = {p}")
    else:
        print("RPC call failed or timed out")


def test_get_stats(transport: UdpTransport, server_ep: Endpoint) -> None:
    print("\n--- Testing GET_STATS() ---")
    result = call_method(transport, server_ep, GET_STATS_METHOD_ID)
    if result and len(result) >= 4:
        (count,) = struct.unpack("!I", result[:4])
        print(f"Server statistics: {count} total method calls processed")
    else:
        print("RPC call failed or timed out")


def main() -> None:
    server_ep = Endpoint(SERVER_HOST, SERVER_PORT)
    transport = UdpTransport(
        local_endpoint=Endpoint("0.0.0.0", 0),
        remote_endpoint=server_ep,
    )

    print("=== SOME/IP Method Calls Client (Python) ===")
    print(f"Calculator Client (ID: 0x{CLIENT_ID:04X})\n")

    transport.start()

    print("=== Running Calculator Operations ===")
    test_add(transport, server_ep, 10, 5)
    test_add(transport, server_ep, -3, 7)
    test_add(transport, server_ep, 1000, 2000)
    test_multiply(transport, server_ep, 6, 7)
    test_multiply(transport, server_ep, -4, 5)
    test_multiply(transport, server_ep, 25, 4)
    test_get_stats(transport, server_ep)
    print("\n=== All Operations Completed ===")

    transport.stop()
    print("\nClient finished.")


if __name__ == "__main__":
    main()
