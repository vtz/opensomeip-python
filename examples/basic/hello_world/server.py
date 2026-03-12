#!/usr/bin/env python3
"""Hello World Server -- Python equivalent of the C++ hello_world/server.

Listens on UDP port 30490 for SOME/IP requests to service 0x1000 / method 0x0001
and replies with "Hello World! Server received: <payload>".

Interop:
    # Terminal 1 -- this Python server
    python examples/basic/hello_world/server.py

    # Terminal 2 -- C++ client  (or the Python client)
    ./build/examples/basic/hello_world/hello_world_client
    python examples/basic/hello_world/client.py

Environment variables:
    HELLO_BIND_HOST  (default 0.0.0.0)
    HELLO_BIND_PORT  (default 30490)
"""

from __future__ import annotations

import os
import signal

from opensomeip.message import Message
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, ReturnCode

HELLO_SERVICE_ID = 0x1000
SAY_HELLO_METHOD_ID = 0x0001


def main() -> None:
    bind_host = os.environ.get("HELLO_BIND_HOST", "0.0.0.0")
    bind_port = int(os.environ.get("HELLO_BIND_PORT", "30490"))

    transport = UdpTransport(
        local_endpoint=Endpoint(bind_host, bind_port),
    )

    def shutdown(*_: object) -> None:
        print("\nShutting down...")
        transport.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("=== SOME/IP Hello World Server (Python) ===")
    print(f"Listening on {bind_host}:{bind_port}")
    print("Waiting for 'Hello' messages...")
    print("Press Ctrl+C to exit\n")

    transport.start()

    for msg in transport.receiver:
        if (
            msg.message_id.service_id == HELLO_SERVICE_ID
            and msg.message_id.method_id == SAY_HELLO_METHOD_ID
            and msg.message_type == MessageType.REQUEST
        ):
            received_text = msg.payload.decode("utf-8", errors="replace")
            print(f"Client said: '{received_text}' (from {msg.source_endpoint})")

            greeting = f"Hello World! Server received: {received_text}"
            response = Message(
                message_id=MessageId(HELLO_SERVICE_ID, SAY_HELLO_METHOD_ID),
                request_id=msg.request_id,
                message_type=MessageType.RESPONSE,
                return_code=ReturnCode.E_OK,
                payload=greeting.encode("utf-8"),
            )
            transport.send(response, msg.source_endpoint)
            print(f"Sent greeting: '{greeting}'")

    print("Server stopped.")


if __name__ == "__main__":
    main()
