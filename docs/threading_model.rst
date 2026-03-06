Threading Model and GIL Management
===================================

This page documents how opensomeip-python manages threads, the Python GIL,
and callbacks between C++ and Python.

Overview
--------

The opensomeip C++ library uses background threads for network I/O and
service discovery. The Python bindings must bridge these threads with
Python's Global Interpreter Lock (GIL) correctly to avoid deadlocks.

The binding layer follows two rules:

1. **Python → C++ calls release the GIL** when the call may block or do
   significant I/O (e.g., ``transport.start()``, ``rpc_client.call()``).
2. **C++ → Python callbacks acquire the GIL** before invoking any Python
   code (e.g., message received callback, RPC handler).

Python → C++ (GIL Released)
----------------------------

The following methods release the GIL before calling into C++:

- ``UdpTransport`` / ``TcpTransport``: ``start()``, ``stop()``, ``send()``, ``connect()``
- ``SdClient``: ``start()``, ``stop()``, ``find_service()``, ``subscribe()``
- ``SdServer``: ``start()``, ``stop()``, ``offer_service()``, ``stop_offer()``
- ``RpcClient``: ``call()`` (sync), ``start()``, ``stop()``
- ``RpcServer``: ``start()``, ``stop()``
- ``EventPublisher``: ``start()``, ``stop()``, ``notify()``
- ``EventSubscriber``: ``start()``, ``stop()``, ``subscribe()``
- ``TpManager``: ``send()``, ``start()``, ``stop()``
- ``Serializer`` / ``Deserializer``: for large payloads (> 64 KB)

C++ → Python (GIL Acquired)
-----------------------------

Callbacks invoked from C++ background threads acquire the GIL:

- ``ITransportListener`` trampoline: ``on_message_received``, ``on_error``
- ``RpcServer`` method handler
- ``RpcClient`` async callback
- ``EventSubscriber`` notification and subscription status callbacks
- ``SdClient`` find callback
- ``E2EProfile`` trampoline virtual methods

The Callback Bridge
-------------------

When a C++ callback delivers a message, the following sequence occurs:

1. C++ background thread receives data from the network
2. The trampoline class acquires the GIL
3. The C++ ``Message`` is converted to a Python ``Message`` dataclass
4. The message is pushed onto a thread-safe queue via
   ``loop.call_soon_threadsafe(queue.put_nowait, msg)``
5. The GIL is released
6. The Python consumer awaits or iterates on the queue

This design ensures:

- The GIL is held only briefly (for the queue push)
- No C++ mutexes are held while the GIL is acquired
- The Python event loop processes messages asynchronously

Safe Usage Patterns
-------------------

**DO**:

- Use context managers for transport/server/client lifecycle
- Use ``MessageReceiver`` for consuming incoming messages
- Use ``async for msg in receiver`` in asyncio code
- Use ``for msg in receiver`` in synchronous code

**DON'T**:

- Don't hold Python locks while calling C++ blocking methods
- Don't call C++ methods from within a C++ callback (re-entrancy)
- Don't store C++ wrapper objects (``_opensomeip.Message``) long-term;
  always convert to Python dataclasses at the boundary
