Service Discovery
=================

SOME/IP Service Discovery (SD) allows services to announce their
availability and clients to discover them on the network.

Server Side — Offering Services
--------------------------------

.. code-block:: python

    from opensomeip.sd import SdServer, SdConfig, ServiceInstance
    from opensomeip.transport import Endpoint

    config = SdConfig(
        multicast_endpoint=Endpoint("239.1.1.1", 30490),
        unicast_endpoint=Endpoint("192.168.1.100", 30490),
    )

    with SdServer(config) as server:
        svc = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        server.offer(svc)
        # Service is now discoverable...
        server.stop_offer(svc)

Client Side — Finding Services
-------------------------------

.. code-block:: python

    from opensomeip.sd import SdClient, SdConfig, ServiceInstance

    with SdClient(config) as client:
        target = ServiceInstance(service_id=0x1234, instance_id=0x0001)
        receiver = client.find(target)

        async for found_service in receiver:
            print(f"Found: {found_service}")

Configuration
-------------

``SdConfig`` controls timing parameters:

- ``initial_delay_min_ms`` / ``initial_delay_max_ms``: random initial delay range
- ``repetitions_base_delay_ms``: base delay between repeated offers
- ``repetitions_max``: maximum number of repetition phases
- ``cyclic_offer_delay_ms``: interval for periodic offers
- ``ttl``: time-to-live for service entries
