#!/usr/bin/env python3
"""Complex Types Client -- Python equivalent of the C++ complex_types/client.

Calls service 0x4000 methods to demonstrate Serializer/Deserializer usage
with complex data structures (VehicleData, SensorArray, SensorReading).

Interop:
    # Terminal 1 -- C++ server  (or the Python server)
    ./build/examples/advanced/complex_types/complex_types_server
    python examples/advanced/complex_types/server.py

    # Terminal 2 -- this Python client
    python examples/advanced/complex_types/client.py
"""

from __future__ import annotations

import queue
from dataclasses import dataclass

from opensomeip.message import Message
from opensomeip.serialization import Deserializer, Serializer
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode

COMPLEX_SERVICE_ID = 0x4000
PROCESS_VEHICLE_DATA = 0x0001
GET_SENSOR_ARRAY = 0x0002
ECHO_COMPLEX_STRUCT = 0x0003

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 30494
CLIENT_ID = 0xABCD

session_counter = 0


@dataclass
class VehicleData:
    vehicle_id: int
    model: str
    fuel_level: float
    tire_pressure: list[int]
    lights_on: bool
    mileage: int


@dataclass
class SensorReading:
    sensor_id: int
    value: float
    unit: str
    timestamp: int


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
        message_id=MessageId(COMPLEX_SERVICE_ID, method_id),
        request_id=RequestId(client_id=CLIENT_ID, session_id=next_session()),
        message_type=MessageType.REQUEST,
        return_code=ReturnCode.E_OK,
        payload=payload,
    )
    transport.send(request, server_ep)

    try:
        response = transport.receiver._sync_queue.get(timeout=timeout)
        if response.message_type == MessageType.RESPONSE:
            return response.payload
    except queue.Empty:
        pass
    return None


def serialize_vehicle_data(v: VehicleData) -> bytes:
    ser = Serializer()
    ser.write_uint32(v.vehicle_id)
    ser.write_string(v.model)
    ser.write_float32(v.fuel_level)
    for p in v.tire_pressure:
        ser.write_uint8(p)
    ser.write_bool(v.lights_on)
    ser.write_uint16(v.mileage)
    return ser.to_bytes()


def serialize_sensor_reading(s: SensorReading) -> bytes:
    ser = Serializer()
    ser.write_uint8(s.sensor_id)
    ser.write_float32(s.value)
    ser.write_string(s.unit)
    ser.write_uint32(s.timestamp)
    return ser.to_bytes()


def test_vehicle_data(transport: UdpTransport, server_ep: Endpoint) -> None:
    print("\n--- Test: Process Vehicle Data ---")
    vehicle = VehicleData(
        vehicle_id=42,
        model="Model Y",
        fuel_level=0.75,
        tire_pressure=[32, 33, 31, 34],
        lights_on=True,
        mileage=15000,
    )
    payload = serialize_vehicle_data(vehicle)
    result = call_method(transport, server_ep, PROCESS_VEHICLE_DATA, payload)
    if result:
        des = Deserializer(result)
        response_text = des.read_string()
        print(f"Server response: '{response_text}'")
    else:
        print("RPC call failed or timed out")


def test_sensor_array(transport: UdpTransport, server_ep: Endpoint) -> None:
    print("\n--- Test: Get Sensor Array ---")
    result = call_method(transport, server_ep, GET_SENSOR_ARRAY)
    if result:
        des = Deserializer(result)
        count = des.read_uint32()
        print(f"Received {count} sensor readings:")
        for i in range(count):
            _length = des.read_uint32()
            sensor_id = des.read_uint8()
            value = des.read_float32()
            unit = des.read_string()
            timestamp = des.read_uint32()
            print(f"  [{i}] Sensor {sensor_id}: {value:.1f} {unit} (t={timestamp})")
    else:
        print("RPC call failed or timed out")


def test_echo_struct(transport: UdpTransport, server_ep: Endpoint) -> None:
    print("\n--- Test: Echo Complex Struct ---")
    reading = SensorReading(sensor_id=7, value=42.0, unit="dB", timestamp=9999)
    payload = serialize_sensor_reading(reading)
    result = call_method(transport, server_ep, ECHO_COMPLEX_STRUCT, payload)
    if result:
        des = Deserializer(result)
        echo = SensorReading(
            sensor_id=des.read_uint8(),
            value=des.read_float32(),
            unit=des.read_string(),
            timestamp=des.read_uint32(),
        )
        print(
            f"Echoed: sensor_id={echo.sensor_id}, value={echo.value}, "
            f"unit='{echo.unit}', timestamp={echo.timestamp}"
        )
    else:
        print("RPC call failed or timed out")


def main() -> None:
    server_ep = Endpoint(SERVER_HOST, SERVER_PORT)
    transport = UdpTransport(
        local_endpoint=Endpoint("0.0.0.0", 0),
        remote_endpoint=server_ep,
    )

    print("=== SOME/IP Complex Types Client (Python) ===")
    print(f"Client ID: 0x{CLIENT_ID:04X}\n")

    transport.start()

    print("=== Complex Types Demonstrations ===")
    test_vehicle_data(transport, server_ep)
    test_sensor_array(transport, server_ep)
    test_echo_struct(transport, server_ep)
    print("\n=== All Demonstrations Completed ===")

    transport.stop()
    print("\nClient finished.")


if __name__ == "__main__":
    main()
