#!/usr/bin/env python3
"""RPC server that answers on its own UDP endpoint.

The configured services share that socket through a service demux. Events
and service discovery keep their own sockets.

    # Terminal 1
    python examples/basic/shared_socket/server.py

    # Terminal 2
    python examples/basic/shared_socket/client.py
"""

from __future__ import annotations

import signal
import threading

from opensomeip.message import Message
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.server import ServerConfig, SomeIpServer
from opensomeip.transport import Endpoint
from opensomeip.types import MessageId, MessageType, ReturnCode

SERVICE = ServiceInstance(service_id=0x1234, instance_id=0x0001)
METHOD = MessageId(service_id=0x1234, method_id=0x0001)
PORT = 30510


def echo(request: Message) -> Message:
    """Return the request payload unchanged."""
    print(f"Request payload: {request.payload.hex()}")
    return Message(
        message_id=request.message_id,
        request_id=request.request_id,
        message_type=MessageType.RESPONSE,
        return_code=ReturnCode.E_OK,
        payload=request.payload,
    )


def main() -> None:
    config = ServerConfig(
        local_endpoint=Endpoint("127.0.0.1", PORT),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("127.0.0.1", 30512),
        ),
        services=[SERVICE],
    )
    print(f"Echo service 0x{SERVICE.service_id:04X} listening on 127.0.0.1:{PORT}")
    print("Press Ctrl+C to exit")
    stopped = threading.Event()

    def _stop(*_: object) -> None:
        stopped.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    with SomeIpServer(config) as server:
        server.register_method(METHOD, echo)
        stopped.wait()
        print("Shutting down")


if __name__ == "__main__":
    main()
