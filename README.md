# opensomeip-python

Python bindings for the [opensomeip](https://github.com/vtz/opensomeip) C++ SOME/IP
(Scalable service-Oriented MiddlewarE over IP) stack.

## Features

- **Full protocol coverage**: types, serialization, transport (UDP/TCP), service discovery,
  RPC, events, transport protocol (TP), and E2E protection
- **Pythonic API**: dataclasses, enums, context managers, iterators, and async/await support
- **Dual sync/async**: every callback-based API also exposes an iterator/async-iterator
  interface for use with `asyncio` and frameworks like Jumpstarter
- **Native performance**: when compiled with the C++ extension, all protocol operations
  delegate to the opensomeip C++ stack; pure-Python stubs are available for type checking
  and testing without compilation
- **Type-safe**: full type annotations with `py.typed` marker (PEP 561)
- **gRPC-friendly types**: all public types are plain Python objects (dataclasses, bytes,
  enums) — no opaque C++ wrappers — enabling seamless serialization across gRPC

## Requirements

- Python >= 3.10
- CMake >= 3.20
- A C++17 compiler (GCC 10+, Clang 12+, MSVC 2019+)
- pybind11 >= 2.13

## Installation

### From PyPI (when published)

```bash
pip install opensomeip
```

### From source

```bash
git clone --recurse-submodules https://github.com/vtz/opensomeip-python.git
cd opensomeip-python
pip install -e ".[dev]"
```

### Verify native extension

After installing, confirm the C++ extension loaded successfully:

```bash
python3 -c "from opensomeip._bridge import get_ext; ext = get_ext(); print('native:', ext is not None)"
```

If this prints `native: False`, the library will raise errors on any network
operation. See the [Troubleshooting](#troubleshooting) section below.

## Quick Start

### Server — offer a service and handle RPC calls

```python
from opensomeip import SomeIpServer, ServerConfig, TransportMode
from opensomeip.transport import Endpoint
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.message import Message
from opensomeip.types import MessageId

config = ServerConfig(
    local_endpoint=Endpoint("192.168.1.10", 30490),
    sd_config=SdConfig(
        multicast_endpoint=Endpoint("239.1.1.1", 30490),
        unicast_endpoint=Endpoint("192.168.1.10", 30490),
    ),
    services=[ServiceInstance(service_id=0x1234, instance_id=0x0001)],
)

def echo_handler(request: Message) -> Message:
    return Message(
        message_id=request.message_id,
        request_id=request.request_id,
        payload=request.payload,  # echo back
    )

with SomeIpServer(config) as server:
    server.register_method(MessageId(0x1234, 0x0001), echo_handler)
    # Server is now offering service 0x1234 via SD and handling RPCs
```

### Client — find a service and call methods

```python
from opensomeip import SomeIpClient, ClientConfig
from opensomeip.transport import Endpoint
from opensomeip.sd import SdConfig, ServiceInstance
from opensomeip.types import MessageId

config = ClientConfig(
    local_endpoint=Endpoint("192.168.1.20", 30491),
    sd_config=SdConfig(
        multicast_endpoint=Endpoint("239.1.1.1", 30490),
        unicast_endpoint=Endpoint("192.168.1.20", 30491),
    ),
)

with SomeIpClient(config) as client:
    # Find the service via Service Discovery
    receiver = client.find(ServiceInstance(service_id=0x1234, instance_id=0x0001))

    # Synchronous RPC call
    response = client.call(MessageId(0x1234, 0x0001), payload=b"\x01\x02\x03")
    print(response.payload)

    # Subscribe to events
    for notification in client.subscribe_events(eventgroup_id=1):
        print(notification.payload)
```

### Async usage

```python
import asyncio
from opensomeip import SomeIpClient, ClientConfig
from opensomeip.transport import Endpoint
from opensomeip.sd import SdConfig
from opensomeip.types import MessageId

async def main():
    config = ClientConfig(
        local_endpoint=Endpoint("0.0.0.0", 30491),
        sd_config=SdConfig(
            multicast_endpoint=Endpoint("239.1.1.1", 30490),
            unicast_endpoint=Endpoint("0.0.0.0", 30491),
        ),
    )
    async with SomeIpClient(config) as client:
        response = await client.call_async(
            MessageId(0x1234, 0x0001),
            payload=b"\x01\x02\x03",
        )
        print(response.payload)

asyncio.run(main())
```

### Serialization

```python
from opensomeip.serialization import Serializer, Deserializer

# Serialize a payload
with Serializer() as s:
    s.write_uint16(0x1234)
    s.write_string("hello")
    s.write_float32(3.14)
payload = s.to_bytes()

# Deserialize it back
d = Deserializer(payload)
value = d.read_uint16()   # 0x1234
name = d.read_string()    # "hello"
pi = d.read_float32()     # 3.14
```

## Architecture

The package has a two-layer architecture:

1. **`_opensomeip`** (compiled pybind11 extension): thin bindings to the C++ library with
   explicit GIL management for thread safety
2. **`opensomeip`** (pure Python package): Pythonic wrapper with dataclasses, context
   managers, async iterators, and logging integration

When the C++ extension is available, all wrapper classes automatically delegate to the
native implementation. Without it, pure-Python stubs provide the same API for testing
and type checking.

### Module Map

| Module | Purpose |
|--------|---------|
| `opensomeip.types` | Core types: `MessageId`, `RequestId`, `MessageType`, `ReturnCode` |
| `opensomeip.message` | `Message` dataclass with header fields and payload |
| `opensomeip.transport` | `UdpTransport`, `TcpTransport`, `Endpoint` |
| `opensomeip.sd` | `SdServer`, `SdClient`, `ServiceInstance`, `SdConfig` |
| `opensomeip.rpc` | `RpcClient`, `RpcServer` for remote procedure calls |
| `opensomeip.events` | `EventPublisher`, `EventSubscriber` for notifications |
| `opensomeip.serialization` | `Serializer`, `Deserializer` for payload encoding |
| `opensomeip.tp` | `TpManager` for large message segmentation/reassembly |
| `opensomeip.e2e` | `E2EProtection`, CRC functions for end-to-end safety |
| `opensomeip.server` | `SomeIpServer` — high-level server composing all components |
| `opensomeip.client` | `SomeIpClient` — high-level client composing all components |
| `opensomeip.receiver` | `MessageReceiver` — sync/async message iterator |

## Troubleshooting

### macOS: C++ extension fails to load (`ImportError` / symbol not found)

When installing from source on macOS (e.g. `pip install opensomeip` on a Python
version for which no pre-built wheel is available), the C++ extension may fail to
load at runtime with an error like:

```
ImportError: dlopen(…/_opensomeip.cpython-3xx-darwin.so, 0x0002):
  symbol not found in flat namespace '__ZNSt3__113__hash_memoryEPKvm'
```

**Cause:** If [Homebrew LLVM](https://formulae.brew.sh/formula/llvm) is installed
and its `clang++` appears in `PATH` before `/usr/bin/clang++`, CMake will use it
during the build. Homebrew's compiler ships a newer libc++ than the one bundled
with macOS, so the compiled extension references symbols that don't exist in the
system library loaded at runtime.

**Fix — rebuild with the system compiler:**

```bash
CC=/usr/bin/clang CXX=/usr/bin/clang++ \
  pip install --no-cache-dir --force-reinstall --no-binary=opensomeip opensomeip
```

**Tip:** Pre-built wheels (available for Python 3.10 – 3.14 on macOS, Linux, and
Windows) are compiled in CI with the correct toolchain and don't have this issue.
If a wheel exists for your platform you'll never hit this problem — it only
occurs when pip falls back to building from the source distribution.

### Operations fail with "C++ extension is not available"

If the C++ extension fails to load, all operations that require the native
stack (RPC calls, transport send, event subscriptions) will raise clear errors
such as `RpcError`, `TransportError`, or `RuntimeError` with a message
indicating the C++ extension is not available.

To check whether the extension loaded:

```bash
python3 -c "from opensomeip._bridge import get_ext; ext = get_ext(); print('native:', ext is not None)"
```

If this prints `native: False`, follow the steps in the section above to fix
the extension build.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/opensomeip/

# Build documentation
pip install -e ".[docs]"
cd docs && make html
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and
pull request guidelines.

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
