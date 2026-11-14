#!/usr/bin/env python3
"""RPC client that calls the shared-socket echo server.

``remote_endpoint`` is the server's application endpoint. The client uses
its own socket and sends there.

    python examples/basic/shared_socket/client.py
"""

from __future__ import annotations

from opensomeip.client import ClientConfig, SomeIpClient
from opensomeip.sd import SdConfig
from opensomeip.transport import Endpoint
from opensomeip.types import MessageId

METHOD = MessageId(service_id=0x1234, method_id=0x0001)
SERVER = Endpoint("127.0.0.1", 30510)


def main() -> None:
    config = ClientConfig(
        local_endpoint=Endpoint("127.0.0.1", 30511),
        remote_endpoint=SERVER,
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("127.0.0.1", 30513),
        ),
    )
    with SomeIpClient(config) as client:
        response = client.call(METHOD, payload=b"\xca\xfe")
    print(f"Response payload: {response.payload.hex()}")


if __name__ == "__main__":
    main()
