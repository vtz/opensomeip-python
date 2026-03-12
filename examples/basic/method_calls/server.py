#!/usr/bin/env python3
"""Calculator RPC Server -- Python equivalent of the C++ method_calls/server.

Offers service 0x2000 with three methods:
  0x0001  ADD(int32, int32) -> int32
  0x0002  MULTIPLY(int32, int32) -> int32
  0x0003  GET_STATS() -> uint32

Wire format: big-endian integers (same as C++ server).

Interop:
    # Terminal 1 -- this Python server
    python examples/basic/method_calls/server.py

    # Terminal 2 -- C++ client  (or the Python client)
    ./build/examples/basic/method_calls/method_calls_client
    python examples/basic/method_calls/client.py
"""

from __future__ import annotations

import signal
import struct

from opensomeip.message import Message
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageType, ReturnCode

CALCULATOR_SERVICE_ID = 0x2000
ADD_METHOD_ID = 0x0001
MULTIPLY_METHOD_ID = 0x0002
GET_STATS_METHOD_ID = 0x0003

PORT = 30491

total_calls = 0


def handle_add(payload: bytes) -> bytes:
    global total_calls
    if len(payload) < 8:
        return b""
    a, b = struct.unpack("!ii", payload[:8])
    result = a + b
    total_calls += 1
    print(f"ADD: {a} + {b} = {result}")
    return struct.pack("!i", result)


def handle_multiply(payload: bytes) -> bytes:
    global total_calls
    if len(payload) < 8:
        return b""
    a, b = struct.unpack("!ii", payload[:8])
    result = a * b
    total_calls += 1
    print(f"MULTIPLY: {a} * {b} = {result}")
    return struct.pack("!i", result)


def handle_get_stats(_payload: bytes) -> bytes:
    print(f"GET_STATS: {total_calls} total calls processed")
    return struct.pack("!I", total_calls)


HANDLERS = {
    ADD_METHOD_ID: handle_add,
    MULTIPLY_METHOD_ID: handle_multiply,
    GET_STATS_METHOD_ID: handle_get_stats,
}


def main() -> None:
    transport = UdpTransport(
        local_endpoint=Endpoint("0.0.0.0", PORT),
    )

    def shutdown(*_: object) -> None:
        print("\nShutting down...")
        transport.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("=== SOME/IP Method Calls Server (Python) ===")
    print(f"Calculator service 0x{CALCULATOR_SERVICE_ID:04X} on port {PORT}")
    print("Available methods:")
    print(f"  - 0x{ADD_METHOD_ID:04X}: add(int32, int32) -> int32")
    print(f"  - 0x{MULTIPLY_METHOD_ID:04X}: multiply(int32, int32) -> int32")
    print(f"  - 0x{GET_STATS_METHOD_ID:04X}: get_stats() -> uint32")
    print("Press Ctrl+C to exit\n")

    transport.start()

    for msg in transport.receiver:
        if (
            msg.message_id.service_id == CALCULATOR_SERVICE_ID
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
                transport.send(response, msg.source_endpoint)

    print("Server stopped.")


if __name__ == "__main__":
    main()
