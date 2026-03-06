Getting Started
===============

Installation
------------

From PyPI (when published)::

    pip install opensomeip

From source::

    git clone --recurse-submodules https://github.com/vtz/opensomeip-python.git
    cd opensomeip-python
    pip install -e ".[dev]"

Requirements
^^^^^^^^^^^^

- Python >= 3.10
- CMake >= 3.20
- A C++17 compiler (GCC 10+, Clang 12+, MSVC 2019+)
- pybind11 >= 2.13

Quick Start
-----------

Creating a SOME/IP Message
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from opensomeip.types import MessageId, MessageType
    from opensomeip.message import Message

    msg = Message(
        message_id=MessageId(service_id=0x1234, method_id=0x0001),
        message_type=MessageType.REQUEST,
        payload=b"\x01\x02\x03",
    )
    print(msg)

Using the Serializer
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from opensomeip.serialization import Serializer, Deserializer

    with Serializer() as s:
        s.write_uint16(0x1234)
        s.write_string("hello")
    data = s.to_bytes()

    d = Deserializer(data)
    value = d.read_uint16()   # 0x1234
    text = d.read_string()    # "hello"

High-Level Server
^^^^^^^^^^^^^^^^^

.. code-block:: python

    from opensomeip.server import SomeIpServer, ServerConfig
    from opensomeip.sd import SdConfig, ServiceInstance
    from opensomeip.transport import Endpoint
    from opensomeip.message import Message
    from opensomeip.types import MessageId

    config = ServerConfig(
        local_endpoint=Endpoint("0.0.0.0", 30490),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.100", 30490),
        ),
        services=[ServiceInstance(service_id=0x1234, instance_id=0x0001)],
    )

    with SomeIpServer(config) as server:
        server.register_method(
            MessageId(0x1234, 0x0001),
            lambda req: Message(payload=b"response"),
        )
        # Server is running and discoverable...

High-Level Client
^^^^^^^^^^^^^^^^^

.. code-block:: python

    from opensomeip.client import SomeIpClient, ClientConfig
    from opensomeip.sd import SdConfig
    from opensomeip.transport import Endpoint
    from opensomeip.types import MessageId

    config = ClientConfig(
        local_endpoint=Endpoint("0.0.0.0", 0),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("192.168.1.200", 30490),
        ),
    )

    with SomeIpClient(config) as client:
        response = client.call(
            MessageId(0x1234, 0x0001),
            payload=b"request data",
        )
        print(response.payload)
