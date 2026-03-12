# opensomeip-python Examples

Python examples that mirror the C++ examples in `extern/opensomeip/examples/`.
Each Python example is **wire-compatible** with its C++ counterpart, so you can
run a Python server with a C++ client (or vice versa).

## Prerequisites

```bash
# Install the package (builds the C++ extension)
CC=/usr/bin/clang CXX=/usr/bin/clang++ pip install -e .

# Verify
python -c "from opensomeip import _opensomeip; print('OK')"
```

## Examples

### Basic

| Example | Description | Files |
|---------|-------------|-------|
| **Hello World** | Simplest request/response over UDP | `basic/hello_world/server.py`, `client.py` |
| **Method Calls** | Calculator RPC (add, multiply, get_stats) | `basic/method_calls/server.py`, `client.py` |
| **Events** | Sensor publish/subscribe (temperature, speed) | `basic/events/publisher.py`, `subscriber.py` |
| **SD Demo** | Service Discovery with multicast | `basic/sd_demo/server.py` |

### Advanced

| Example | Description | Files |
|---------|-------------|-------|
| **Complex Types** | Serializer/Deserializer with structs | `advanced/complex_types/server.py`, `client.py` |
| **Large Messages** | TP segmentation for large payloads | `advanced/large_messages/server.py`, `client.py` |

### E2E Protection

| Example | Description | Files |
|---------|-------------|-------|
| **Basic E2E** | CRC / counter / freshness protection | `e2e_protection/basic_e2e.py` |

## Running

### Python server + Python client

```bash
# Terminal 1
python examples/basic/hello_world/server.py

# Terminal 2
python examples/basic/hello_world/client.py
```

### Python server + C++ client (cross-language interop)

```bash
# Build the C++ examples first
cd extern/opensomeip && mkdir -p build && cd build
cmake .. -DBUILD_EXAMPLES=ON && make -j$(nproc)
cd ../../..

# Terminal 1 -- Python server
python examples/basic/hello_world/server.py

# Terminal 2 -- C++ client
./extern/opensomeip/build/examples/basic/hello_world/hello_world_client
```

### C++ server + Python client

```bash
# Terminal 1 -- C++ server
./extern/opensomeip/build/examples/basic/hello_world/hello_world_server

# Terminal 2 -- Python client
python examples/basic/hello_world/client.py
```

### Standalone (no network)

```bash
# E2E protection demo (no transport needed)
python examples/e2e_protection/basic_e2e.py
```

## Wire Format Reference

All examples use the standard SOME/IP wire format:

- **Integers**: big-endian (network byte order)
- **Floats**: big-endian IEEE 754
- **Strings**: uint32 length prefix + UTF-8 data (+ 4-byte alignment in Serializer)
- **Messages**: SOME/IP header (service ID, method ID, client ID, session ID,
  message type, return code) + payload

## Environment Variables

| Variable | Default | Used by |
|----------|---------|---------|
| `HELLO_BIND_HOST` | `0.0.0.0` | hello_world server |
| `HELLO_BIND_PORT` | `30490` | hello_world server |
| `HELLO_SERVER_HOST` | `127.0.0.1` | hello_world client |
| `HELLO_SERVER_PORT` | `30490` | hello_world client |
| `SD_SERVICE_HOST` | `127.0.0.1` | sd_demo server |
| `SD_MULTICAST` | `239.255.255.251` | sd_demo server |
| `SENSOR_PORT` | `30492` | events publisher |
| `SUBSCRIBER_PORT` | `30493` | events subscriber |

## Port Map

| Port | Example |
|------|---------|
| 30490 | hello_world, SD multicast |
| 30491 | method_calls |
| 30492 | events publisher |
| 30493 | events subscriber |
| 30494 | complex_types |
| 30495 | large_messages |
| 30500 | sd_demo service |
