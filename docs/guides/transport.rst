Transport Layer
===============

The transport layer provides UDP and TCP transports for sending and
receiving SOME/IP messages.

Basic Usage
-----------

.. code-block:: python

    from opensomeip.transport import UdpTransport, Endpoint

    local = Endpoint("0.0.0.0", 30490)
    remote = Endpoint("192.168.1.1", 30490)

    with UdpTransport(local, remote) as transport:
        # Transport is running
        transport.send(msg)

        # Iterate over received messages
        for incoming in transport.receiver:
            print(incoming)

Async Usage
-----------

.. code-block:: python

    async with UdpTransport(local, remote) as transport:
        async for msg in transport.receiver:
            process(msg)

TCP Transport
-------------

TCP transport works the same way but automatically establishes a
connection to the remote endpoint on ``start()``:

.. code-block:: python

    with TcpTransport(local, remote) as transport:
        assert transport.is_connected
        transport.send(msg)

Multicast
---------

UDP transport supports multicast for service discovery:

.. code-block:: python

    transport = UdpTransport(
        local,
        multicast_group="239.1.1.1",
    )

Thread Safety
-------------

- ``send()`` is thread-safe and releases the GIL
- Incoming messages are delivered to the ``MessageReceiver`` which is
  thread-safe and supports both sync and async consumption
- ``start()`` and ``stop()`` should be called from a single thread
