# opensomeip-python

Python bindings for the [opensomeip](https://github.com/siemens/opensomeip) C++ SOME/IP
(Scalable service-Oriented MiddlewarE over IP) stack.

## Features

- **Full protocol coverage**: types, serialization, transport (UDP/TCP), service discovery,
  RPC, events, transport protocol (TP), and E2E protection
- **Pythonic API**: dataclasses, enums, context managers, iterators, and async/await support
- **Dual sync/async**: every callback-based API also exposes an iterator/async-iterator
  interface for use with `asyncio` and frameworks like Jumpstarter
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

## Quick Start

```python
import opensomeip
from opensomeip.types import MessageId, MessageType
from opensomeip.message import Message

# Create a SOME/IP message
msg = Message(
    message_id=MessageId(service_id=0x1234, method_id=0x0001),
    message_type=MessageType.REQUEST,
    payload=b"\x01\x02\x03",
)
print(msg)
```

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
```

## Architecture

The package has a two-layer architecture:

1. **`_opensomeip`** (compiled pybind11 extension): thin bindings to the C++ library with
   explicit GIL management for thread safety
2. **`opensomeip`** (pure Python package): Pythonic wrapper with dataclasses, context
   managers, async iterators, and logging integration

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
