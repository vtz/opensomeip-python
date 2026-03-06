Transport Protocol (TP) and E2E Protection
==========================================

Transport Protocol
------------------

SOME/IP-TP handles messages that exceed the transport MTU by segmenting
them on the sender side and reassembling on the receiver side.

.. code-block:: python

    from opensomeip.tp import TpManager

    with TpManager(transport, mtu=1400) as tp:
        # Messages larger than MTU are automatically segmented
        tp.send(large_message)

        # Receive reassembled messages
        async for msg in tp.reassembled():
            print(f"Reassembled: {len(msg.payload)} bytes")

E2E Protection
--------------

End-to-End (E2E) protection adds integrity checks to SOME/IP messages.

Built-in profiles:

.. code-block:: python

    from opensomeip.e2e import E2EProtection, E2EConfig, E2EProfileId

    config = E2EConfig(
        profile_id=E2EProfileId.PROFILE_01,
        data_id=0x1234,
        data_length=16,
    )
    protection = E2EProtection(config)

    protected = protection.protect(payload)
    status = protection.check(received_payload)

Custom E2E Profiles
-------------------

Implement custom profiles by subclassing ``E2EProfile``:

.. code-block:: python

    from opensomeip.e2e import E2EProfile, E2ECheckStatus

    class MyProfile(E2EProfile):
        def protect(self, data: bytearray, counter: int) -> bytearray:
            # Add custom CRC/checksum
            crc = compute_crc(data)
            data.append(crc)
            return data

        def check(self, data: bytes, counter: int) -> E2ECheckStatus:
            if verify_crc(data):
                return E2ECheckStatus.OK
            return E2ECheckStatus.ERROR

CRC Utilities
^^^^^^^^^^^^^

.. code-block:: python

    from opensomeip.e2e import crc8, crc32

    checksum = crc8(b"data")
    checksum32 = crc32(b"data")
