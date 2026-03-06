opensomeip-python
=================

Python bindings for the `opensomeip <https://github.com/siemens/opensomeip>`_ C++ SOME/IP
(Scalable service-Oriented MiddlewarE over IP) stack.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getting_started
   guides/index
   api/index
   threading_model
   compatibility

Features
--------

- **Full protocol coverage**: types, serialization, transport (UDP/TCP), service discovery,
  RPC, events, transport protocol (TP), and E2E protection
- **Pythonic API**: dataclasses, enums, context managers, iterators, and async/await
- **Dual sync/async**: every callback-based API also exposes an iterator/async-iterator
  interface for use with ``asyncio`` and frameworks like Jumpstarter
- **Type-safe**: full type annotations with ``py.typed`` marker (PEP 561)
- **gRPC-friendly types**: all public types are plain Python objects (dataclasses, bytes,
  enums) enabling seamless serialization

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
