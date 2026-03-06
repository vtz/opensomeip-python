RPC (Remote Procedure Call)
==========================

SOME/IP RPC enables request/response communication between services.

Client — Calling Methods
-------------------------

Synchronous:

.. code-block:: python

    from opensomeip.rpc import RpcClient
    from opensomeip.types import MessageId

    with RpcClient(transport) as client:
        response = client.call(
            MessageId(0x1234, 0x0001),
            payload=b"\x01\x02",
            timeout=5.0,
        )
        print(response.payload)

Asynchronous:

.. code-block:: python

    async with RpcClient(transport) as client:
        response = await client.call_async(
            MessageId(0x1234, 0x0001),
            payload=b"\x01\x02",
        )

Server — Handling Methods
--------------------------

Callback-based:

.. code-block:: python

    from opensomeip.rpc import RpcServer
    from opensomeip.message import Message

    def handler(request: Message) -> Message:
        return Message(payload=b"response")

    with RpcServer(transport) as server:
        server.register_handler(MessageId(0x1234, 0x0001), handler)

Async handler:

.. code-block:: python

    async def handler(request: Message) -> Message:
        result = await compute(request.payload)
        return Message(payload=result)

    server.register_async_handler(method_id, handler)

Iterator-based (for Jumpstarter-style drivers):

.. code-block:: python

    receiver = server.incoming_requests(method_id)
    async for request in receiver:
        # Process request, send response via ResponseSender
        pass
