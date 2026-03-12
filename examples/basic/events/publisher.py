#!/usr/bin/env python3
"""Sensor Event Publisher -- Python equivalent of the C++ events/publisher.

Publishes temperature (0x8001) and speed (0x8002) events for service 0x3000,
eventgroup 0x0001.  Payload is a big-endian IEEE 754 float (4 bytes), matching
the C++ publisher's wire format.

Interop:
    # Terminal 1 -- this Python publisher
    python examples/basic/events/publisher.py

    # Terminal 2 -- C++ subscriber  (or the Python subscriber)
    ./build/examples/basic/events/events_subscriber
    python examples/basic/events/subscriber.py
"""

from __future__ import annotations

import os
import random
import signal
import struct
import threading
import time

from opensomeip.events import EventPublisher
from opensomeip.transport import Endpoint, UdpTransport

SENSOR_SERVICE_ID = 0x3000
TEMPERATURE_EVENT_ID = 0x8001
SPEED_EVENT_ID = 0x8002
SENSOR_EVENTGROUP_ID = 0x0001

PORT = int(os.environ.get("SENSOR_PORT", "30492"))

stop_event = threading.Event()


def float_to_be_bytes(value: float) -> bytes:
    """Encode a float as 4 big-endian bytes (IEEE 754)."""
    return struct.pack("!f", value)


def main() -> None:
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    transport = UdpTransport(local_endpoint=Endpoint("0.0.0.0", PORT))
    publisher = EventPublisher(
        transport, service_id=SENSOR_SERVICE_ID, instance_id=0x0001
    )

    publisher.register_event(TEMPERATURE_EVENT_ID, SENSOR_EVENTGROUP_ID)
    publisher.register_event(SPEED_EVENT_ID, SENSOR_EVENTGROUP_ID)

    transport.start()
    publisher.start()

    print("=== SOME/IP Events Publisher (Python) ===")
    print(f"Service 0x{SENSOR_SERVICE_ID:04X} on port {PORT}")
    print(f"  Temperature (0x{TEMPERATURE_EVENT_ID:04X}) every 2 s")
    print(f"  Speed       (0x{SPEED_EVENT_ID:04X}) every 1.5 s")
    print("Press Ctrl+C to exit\n")

    last_temp = time.monotonic()
    last_speed = time.monotonic()

    while not stop_event.is_set():
        now = time.monotonic()

        if now - last_temp >= 2.0:
            temperature = random.uniform(15.0, 35.0)
            publisher.notify(TEMPERATURE_EVENT_ID, float_to_be_bytes(temperature))
            print(f"Published Temperature: {temperature:.1f} C")
            last_temp = now

        if now - last_speed >= 1.5:
            speed = random.uniform(0.0, 120.0)
            publisher.notify(SPEED_EVENT_ID, float_to_be_bytes(speed))
            print(f"Published Speed: {speed:.1f} km/h")
            last_speed = now

        stop_event.wait(0.1)

    print("\nShutting down...")
    publisher.stop()
    transport.stop()
    print("Publisher stopped.")


if __name__ == "__main__":
    main()
