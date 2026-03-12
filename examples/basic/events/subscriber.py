#!/usr/bin/env python3
"""Sensor Event Subscriber -- Python equivalent of the C++ events/subscriber.

Subscribes to temperature (0x8001) and speed (0x8002) events from service 0x3000,
eventgroup 0x0001.  Decodes the 4-byte big-endian IEEE 754 float payload,
matching the C++ subscriber's wire format.

Interop:
    # Terminal 1 -- C++ publisher  (or the Python publisher)
    ./build/examples/basic/events/events_publisher
    python examples/basic/events/publisher.py

    # Terminal 2 -- this Python subscriber
    python examples/basic/events/subscriber.py
"""

from __future__ import annotations

import os
import signal
import struct
import threading

from opensomeip.events import EventSubscriber
from opensomeip.transport import Endpoint, UdpTransport

SENSOR_SERVICE_ID = 0x3000
TEMPERATURE_EVENT_ID = 0x8001
SPEED_EVENT_ID = 0x8002
SENSOR_EVENTGROUP_ID = 0x0001

PORT = int(os.environ.get("SUBSCRIBER_PORT", "30493"))

stop_event = threading.Event()


def be_bytes_to_float(data: bytes) -> float:
    """Decode 4 big-endian bytes to an IEEE 754 float."""
    (value,) = struct.unpack("!f", data[:4])
    return value


def main() -> None:
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    transport = UdpTransport(local_endpoint=Endpoint("0.0.0.0", PORT))
    subscriber = EventSubscriber(transport, client_id=0x0001)

    subscriber.subscribe(SENSOR_EVENTGROUP_ID)
    transport.start()
    subscriber.start()

    print("=== SOME/IP Events Subscriber (Python) ===")
    print(f"Service 0x{SENSOR_SERVICE_ID:04X}, listening on port {PORT}")
    print(f"  Subscribed to Temperature (0x{TEMPERATURE_EVENT_ID:04X})")
    print(f"  Subscribed to Speed       (0x{SPEED_EVENT_ID:04X})")
    print("Waiting for events... Press Ctrl+C to exit\n")

    receiver = subscriber.notifications()
    for msg in receiver:
        if stop_event.is_set():
            break

        event_id = msg.message_id.method_id
        if len(msg.payload) < 4:
            print(f"Event 0x{event_id:04X}: Invalid data size ({len(msg.payload)} bytes)")
            continue

        value = be_bytes_to_float(msg.payload)

        if event_id == TEMPERATURE_EVENT_ID:
            print(f"Temperature Event: {value:.1f} C")
        elif event_id == SPEED_EVENT_ID:
            print(f"Speed Event: {value:.1f} km/h")
        else:
            print(f"Unknown event 0x{event_id:04X}: {msg.payload.hex()}")

    subscriber.stop()
    transport.stop()
    print("Subscriber stopped.")


if __name__ == "__main__":
    main()
