Serialization
=============

SOME/IP payloads are serialized using a big-endian wire format.
The ``Serializer`` and ``Deserializer`` classes provide a typed interface
for encoding and decoding these payloads.

Serializing Data
----------------

.. code-block:: python

    from opensomeip.serialization import Serializer

    with Serializer() as s:
        s.write_uint16(0x1234)
        s.write_int32(-42)
        s.write_string("hello")
        s.write_bytes(b"\xDE\xAD")

    payload = s.to_bytes()

Deserializing Data
------------------

.. code-block:: python

    from opensomeip.serialization import Deserializer

    d = Deserializer(payload)
    value = d.read_uint16()    # 0x1234
    number = d.read_int32()    # -42
    text = d.read_string()     # "hello"
    blob = d.read_bytes()      # b"\xDE\xAD"

    assert d.remaining == 0

Supported Types
---------------

.. list-table::
   :header-rows: 1

   * - Type
     - Write Method
     - Read Method
     - Size
   * - bool
     - ``write_bool()``
     - ``read_bool()``
     - 1 byte
   * - uint8
     - ``write_uint8()``
     - ``read_uint8()``
     - 1 byte
   * - uint16
     - ``write_uint16()``
     - ``read_uint16()``
     - 2 bytes
   * - uint32
     - ``write_uint32()``
     - ``read_uint32()``
     - 4 bytes
   * - uint64
     - ``write_uint64()``
     - ``read_uint64()``
     - 8 bytes
   * - int8
     - ``write_int8()``
     - ``read_int8()``
     - 1 byte
   * - int16
     - ``write_int16()``
     - ``read_int16()``
     - 2 bytes
   * - int32
     - ``write_int32()``
     - ``read_int32()``
     - 4 bytes
   * - int64
     - ``write_int64()``
     - ``read_int64()``
     - 8 bytes
   * - float32
     - ``write_float32()``
     - ``read_float32()``
     - 4 bytes
   * - float64
     - ``write_float64()``
     - ``read_float64()``
     - 8 bytes
   * - bytes
     - ``write_bytes()``
     - ``read_bytes()``
     - 4 + N bytes
   * - string
     - ``write_string()``
     - ``read_string()``
     - 4 + N bytes

Strings and byte blobs are length-prefixed with a 4-byte (uint32) header.
Strings are NUL-terminated in the wire format.
