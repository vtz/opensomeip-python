#!/usr/bin/env python3
"""Complex Types Server -- Python equivalent of the C++ complex_types/server.

Service 0x4000 with three methods demonstrating Serializer/Deserializer:
  0x0001  PROCESS_VEHICLE_DATA(VehicleData) -> string
  0x0002  GET_SENSOR_ARRAY() -> SensorArray
  0x0003  ECHO_COMPLEX_STRUCT(SensorReading) -> SensorReading

Wire format uses the opensomeip Serializer:
  - uint32/uint16/uint8/bool/float in big-endian
  - strings: uint32 length prefix + UTF-8 data + 4-byte alignment padding

Interop:
    # Terminal 1 -- this Python server
    python examples/advanced/complex_types/server.py

    # Terminal 2 -- C++ client  (or the Python client)
    ./build/examples/advanced/complex_types/complex_types_client
    python examples/advanced/complex_types/client.py
"""

from __future__ import annotations

import signal
import threading
from dataclasses import dataclass

from opensomeip.message import Message
from opensomeip.serialization import Deserializer, Serializer
from opensomeip.transport import Endpoint, UdpTransport
from opensomeip.types import MessageType, ReturnCode

COMPLEX_SERVICE_ID = 0x4000
PROCESS_VEHICLE_DATA = 0x0001
GET_SENSOR_ARRAY = 0x0002
ECHO_COMPLEX_STRUCT = 0x0003

PORT = 30494

stop_event = threading.Event()


@dataclass
class VehicleData:
    vehicle_id: int
    model: str
    fuel_level: float
    tire_pressure: list[int]  # 4 uint8 values
    lights_on: bool
    mileage: int


@dataclass
class SensorReading:
    sensor_id: int
    value: float
    unit: str
    timestamp: int


def deserialize_vehicle(des: Deserializer) -> VehicleData:
    vehicle_id = des.read_uint32()
    model = des.read_string()
    fuel_level = des.read_float32()
    tire_pressure = [des.read_uint8() for _ in range(4)]
    lights_on = des.read_bool()
    mileage = des.read_uint16()
    return VehicleData(vehicle_id, model, fuel_level, tire_pressure, lights_on, mileage)


def serialize_sensor_reading(reading: SensorReading) -> bytes:
    ser = Serializer()
    ser.write_uint8(reading.sensor_id)
    ser.write_float32(reading.value)
    ser.write_string(reading.unit)
    ser.write_uint32(reading.timestamp)
    return ser.to_bytes()


def deserialize_sensor_reading(des: Deserializer) -> SensorReading:
    sensor_id = des.read_uint8()
    value = des.read_float32()
    unit = des.read_string()
    timestamp = des.read_uint32()
    return SensorReading(sensor_id, value, unit, timestamp)


def serialize_sensor_array(sensors: list[SensorReading]) -> bytes:
    ser = Serializer()
    ser.write_uint32(len(sensors))
    for s in sensors:
        sensor_bytes = serialize_sensor_reading(s)
        ser.write_uint32(len(sensor_bytes))
        ser.write_bytes_raw(sensor_bytes)
    return ser.to_bytes()


def handle_process_vehicle_data(payload: bytes) -> bytes:
    des = Deserializer(payload)
    vehicle = deserialize_vehicle(des)

    print("Processing vehicle data:")
    print(f"  ID: {vehicle.vehicle_id}")
    print(f"  Model: {vehicle.model}")
    print(f"  Fuel Level: {vehicle.fuel_level * 100:.0f}%")
    print(f"  Tire Pressure: {vehicle.tire_pressure} PSI")
    print(f"  Lights: {'ON' if vehicle.lights_on else 'OFF'}")
    print(f"  Mileage: {vehicle.mileage} km")

    response = f"Processed vehicle data for {vehicle.model} (ID: {vehicle.vehicle_id})"
    ser = Serializer()
    ser.write_string(response)
    return ser.to_bytes()


def handle_get_sensor_array(_payload: bytes) -> bytes:
    sensors = [
        SensorReading(1, 23.5, "C", 1000000),
        SensorReading(2, 65.2, "%", 1000001),
        SensorReading(3, 12.8, "V", 1000002),
        SensorReading(4, 1013.25, "hPa", 1000003),
    ]
    print(f"Returning sensor array with {len(sensors)} readings")
    return serialize_sensor_array(sensors)


def handle_echo_complex_struct(payload: bytes) -> bytes:
    des = Deserializer(payload)
    sensor = deserialize_sensor_reading(des)
    print(
        f"Echoing sensor reading: ID={sensor.sensor_id}, "
        f"Value={sensor.value}{sensor.unit}, Timestamp={sensor.timestamp}"
    )
    return serialize_sensor_reading(sensor)


HANDLERS = {
    PROCESS_VEHICLE_DATA: handle_process_vehicle_data,
    GET_SENSOR_ARRAY: handle_get_sensor_array,
    ECHO_COMPLEX_STRUCT: handle_echo_complex_struct,
}


def main() -> None:
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    transport = UdpTransport(local_endpoint=Endpoint("0.0.0.0", PORT))

    print("=== SOME/IP Complex Types Server (Python) ===")
    print(f"Service 0x{COMPLEX_SERVICE_ID:04X} on port {PORT}")
    print("Methods:")
    print(f"  0x{PROCESS_VEHICLE_DATA:04X}: process_vehicle_data(VehicleData) -> string")
    print(f"  0x{GET_SENSOR_ARRAY:04X}: get_sensor_array() -> SensorArray")
    print(f"  0x{ECHO_COMPLEX_STRUCT:04X}: echo_complex_struct(SensorReading) -> SensorReading")
    print("Press Ctrl+C to exit\n")

    transport.start()

    for msg in transport.receiver:
        if stop_event.is_set():
            break

        if (
            msg.message_id.service_id == COMPLEX_SERVICE_ID
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
                transport.send(response)

    transport.stop()
    print("Server stopped.")


if __name__ == "__main__":
    main()
