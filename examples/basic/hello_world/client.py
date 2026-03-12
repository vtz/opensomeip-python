#!/usr/bin/env python3
"""Hello World Client -- Python equivalent of the C++ hello_world/client.

Sends a "Hello from Python Client!" request to the server on UDP port 30490
(service 0x1000 / method 0x0001) and prints the response.

Interop:
    # Terminal 1 -- C++ server  (or the Python server)
    ./build/examples/basic/hello_world/hello_world_server
    python examples/basic/hello_world/server.py

    # Terminal 2 -- this Python client
    python examples/basic/hello_world/client.py

Environment variables:
    HELLO_SERVER_HOST  (default 127.0.0.1)
    HELLO_SERVER_PORT  (default 30490)
"""

from __future__ import annotations

import os
import queue

from opensomeip.message import Message
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode

HELLO_SERVICE_ID = 0x1000
SAY_HELLO_METHOD_ID = 0x0001


def main() -> None:
    server_host = os.environ.get("HELLO_SERVER_HOST", "127.0.0.1")
    server_port = int(os.environ.get("HELLO_SERVER_PORT", "30490"))
    server_ep = Endpoint(server_host, server_port)

    transport = UdpTransport(
        local_endpoint=Endpoint("0.0.0.0", 0),
        remote_endpoint=server_ep,
    )

    print("=== SOME/IP Hello World Client (Python) ===\n")
    transport.start()

    request = Message(
        message_id=MessageId(HELLO_SERVICE_ID, SAY_HELLO_METHOD_ID),
        request_id=RequestId(client_id=0x1234, session_id=0x5678),
        message_type=MessageType.REQUEST,
        return_code=ReturnCode.E_OK,
        payload=b"Hello from Python Client!",
    )

    print(f"Sending message: 'Hello from Python Client!' to {server_host}:{server_port}")
    transport.send(request, server_ep)

    print("Waiting for response (5 s timeout)...")
    try:
        response = transport.receiver._sync_queue.get(timeout=5.0)
        if (
            response.message_id.service_id == HELLO_SERVICE_ID
            and response.message_id.method_id == SAY_HELLO_METHOD_ID
            and response.message_type == MessageType.RESPONSE
        ):
            text = response.payload.decode("utf-8", errors="replace")
            print(f"Server responded: '{text}'")
        else:
            print(f"Unexpected message: {response}")
    except queue.Empty:
        print("Timeout waiting for server response")

    transport.stop()
    print("Client finished.")


if __name__ == "__main__":
    main()
