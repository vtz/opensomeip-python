Events
======

SOME/IP events provide publish/subscribe messaging for continuous data
streams (e.g., sensor values, status updates).

Publishing Events
-----------------

.. code-block:: python

    from opensomeip.events import EventPublisher

    with EventPublisher(transport) as publisher:
        publisher.register_event(event_id=0x8001, eventgroup_id=0x0001)
        publisher.notify(event_id=0x8001, payload=b"\x01\x02")

Subscribing to Events
---------------------

.. code-block:: python

    from opensomeip.events import EventSubscriber

    with EventSubscriber(transport) as subscriber:
        subscriber.subscribe(eventgroup_id=0x0001)

        # Async iteration
        async for notification in subscriber.notifications():
            print(notification.payload)

Subscription Status
-------------------

Monitor subscription status changes:

.. code-block:: python

    status_receiver = subscriber.subscription_status()
    async for status in status_receiver:
        print(f"Subscription state: {status.state}")

Field Events
------------

Field events (getter/setter pattern) are supported via ``set_field()``:

.. code-block:: python

    publisher.set_field(event_id=0x8001, payload=b"\x42")
