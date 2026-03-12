#!/usr/bin/env python3
"""SD Demo Server -- Python equivalent of the C++ sd_demo/server.

Offers service 0x1000 instance 0x0001 via Service Discovery on multicast
239.255.255.251:30490, while handling SOME/IP requests on UDP port 30500.

Interop:
    # Terminal 1 -- this Python SD server
    python examples/basic/sd_demo/server.py

    # Terminal 2 -- any SD-aware client can find this service

Environment variables:
    SD_SERVICE_HOST  (default 127.0.0.1)
    SD_MULTICAST     (default 239.255.255.251)
"""

from __future__ import annotations

import os
import signal

from opensomeip.message import Message
from opensomeip.sd import SdConfig, SdServer, ServiceInstance
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, ReturnCode

SERVICE_ID = 0x1000
INSTANCE_ID = 0x0001
METHOD_HELLO = 0x0001
SERVICE_PORT = 30500


def main() -> None:
    host = os.environ.get("SD_SERVICE_HOST", "127.0.0.1")
    sd_multicast = os.environ.get("SD_MULTICAST", "239.255.255.251")

    transport = UdpTransport(local_endpoint=Endpoint("0.0.0.0", SERVICE_PORT))

    sd_config = SdConfig(
        multicast_endpoint=Endpoint(sd_multicast, 30490),
        unicast_endpoint=Endpoint(host, SERVICE_PORT),
        cyclic_offer_delay_ms=5000,
        ttl=60,
    )
    service = ServiceInstance(
        service_id=SERVICE_ID,
        instance_id=INSTANCE_ID,
        major_version=1,
        minor_version=0,
    )

    sd = SdServer(sd_config)

    def shutdown(*_: object) -> None:
        print("\nShutting down...")
        sd.stop_offer(service)
        sd.stop()
        transport.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    transport.start()
    sd.start()
    sd.offer(service)

    print("=== SD Demo Server (Python) ===")
    print(f"[service] Listening on 0.0.0.0:{SERVICE_PORT}")
    print(
        f"[sd] Offering service 0x{SERVICE_ID:04X} instance 0x{INSTANCE_ID:04X} "
        f"at {host}:{SERVICE_PORT}"
    )
    print(f"[sd] Multicast on {sd_multicast}:30490")
    print("Press Ctrl+C to stop.\n")

    for msg in transport.receiver:
        if (
            msg.message_id.service_id == SERVICE_ID
            and msg.message_id.method_id == METHOD_HELLO
            and msg.message_type == MessageType.REQUEST
        ):
            text = msg.payload.decode("utf-8", errors="replace")
            print(f"[service] Request: '{text}'")

            reply = f"Hello back! Got: {text}"
            response = Message(
                message_id=MessageId(SERVICE_ID, METHOD_HELLO),
                request_id=msg.request_id,
                message_type=MessageType.RESPONSE,
                return_code=ReturnCode.E_OK,
                payload=reply.encode("utf-8"),
            )
            transport.send(response, msg.source_endpoint)

    print("Server stopped.")


if __name__ == "__main__":
    main()
