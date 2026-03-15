"""Bridge between pure-Python wrapper types and C++ binding types.

Provides lazy import of the ``_opensomeip`` extension and conversion
helpers between the Pythonic dataclass/enum types and pybind11 structs.

When the C++ extension is not available (e.g. type-checking or testing
without compilation), ``HAS_NATIVE`` is ``False`` and all ``to_cpp_*`` /
``from_cpp_*`` functions raise ``RuntimeError``.
"""

from __future__ import annotations

import functools
import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opensomeip.message import Message
    from opensomeip.sd import SdConfig, ServiceInstance
    from opensomeip.transport import Endpoint

HAS_NATIVE: bool = False
_ext: Any = None


def _load_extension() -> Any:
    global HAS_NATIVE, _ext
    if _ext is not None:
        return _ext
    try:
        from opensomeip import _opensomeip  # type: ignore[attr-defined]

        _ext = _opensomeip
        HAS_NATIVE = True
        return _ext
    except ImportError as exc:
        HAS_NATIVE = False
        _msg = (
            f"opensomeip C++ extension failed to load: {exc}\n"
            "Transport classes will run as no-op stubs (no sockets will be opened).\n"
            "On macOS, this is often caused by a libc++ ABI mismatch when building "
            "from source with a non-system compiler (e.g. Homebrew LLVM). "
            "Rebuild with the system compiler:\n"
            "  CC=/usr/bin/clang CXX=/usr/bin/clang++ "
            "pip install --no-cache-dir --force-reinstall --no-binary=opensomeip opensomeip\n"
            "See https://github.com/vtz/opensomeip-python#troubleshooting for details."
        )
        warnings.warn(_msg, ImportWarning, stacklevel=2)
        return None


@functools.lru_cache(maxsize=1)
def get_ext() -> Any:
    """Return the ``_opensomeip`` extension module, or ``None``."""
    return _load_extension()


def require_native() -> Any:
    """Return the extension or raise ``RuntimeError`` if unavailable."""
    ext = get_ext()
    if ext is None:
        raise RuntimeError(
            "opensomeip C++ extension (_opensomeip) is not available. "
            "Install with: pip install -e ."
        )
    return ext


# ---------------------------------------------------------------------------
# Endpoint conversions
# ---------------------------------------------------------------------------


def to_cpp_endpoint(ep: Endpoint) -> Any:
    ext = require_native()
    return ext.Endpoint(ep.ip, ep.port)


def from_cpp_endpoint(cpp_ep: Any) -> Endpoint:
    from opensomeip.transport import Endpoint as PyEndpoint

    return PyEndpoint(ip=cpp_ep.address, port=cpp_ep.port)


# ---------------------------------------------------------------------------
# MessageId / RequestId conversions
# ---------------------------------------------------------------------------


def to_cpp_message_id(mid: Any) -> Any:
    ext = require_native()
    return ext.MessageId(mid.service_id, mid.method_id)


def from_cpp_message_id(cpp_mid: Any) -> Any:
    from opensomeip.types import MessageId

    return MessageId(service_id=cpp_mid.service_id, method_id=cpp_mid.method_id)


def to_cpp_request_id(rid: Any) -> Any:
    ext = require_native()
    return ext.RequestId(rid.client_id, rid.session_id)


def from_cpp_request_id(cpp_rid: Any) -> Any:
    from opensomeip.types import RequestId

    return RequestId(client_id=cpp_rid.client_id, session_id=cpp_rid.session_id)


# ---------------------------------------------------------------------------
# Message conversions
# ---------------------------------------------------------------------------


def to_cpp_message(msg: Message) -> Any:
    ext = require_native()
    cpp_mid = ext.MessageId(msg.message_id.service_id, msg.message_id.method_id)
    cpp_rid = ext.RequestId(msg.request_id.client_id, msg.request_id.session_id)
    cpp_msg = ext.Message(
        cpp_mid,
        cpp_rid,
        ext.MessageType(int(msg.message_type)),
        ext.ReturnCode(int(msg.return_code)),
    )
    cpp_msg.interface_version = msg.interface_version
    cpp_msg.payload = msg.payload
    return cpp_msg


def from_cpp_message(cpp_msg: Any) -> Message:
    from opensomeip.message import Message as PyMessage
    from opensomeip.types import MessageId, MessageType, RequestId, ReturnCode

    cpp_mid = cpp_msg.message_id
    cpp_rid = cpp_msg.request_id
    return PyMessage(
        message_id=MessageId(service_id=cpp_mid.service_id, method_id=cpp_mid.method_id),
        request_id=RequestId(client_id=cpp_rid.client_id, session_id=cpp_rid.session_id),
        message_type=MessageType(int(cpp_msg.message_type)),
        return_code=ReturnCode(int(cpp_msg.return_code)),
        interface_version=cpp_msg.interface_version,
        payload=bytes(cpp_msg.payload),
    )


# ---------------------------------------------------------------------------
# SdConfig conversions
# ---------------------------------------------------------------------------


def to_cpp_sd_config(config: SdConfig) -> Any:
    import datetime

    ext = require_native()
    cpp_cfg = ext.sd.SdConfig()
    cpp_cfg.multicast_address = config.multicast_endpoint.ip
    cpp_cfg.multicast_port = config.multicast_endpoint.port
    cpp_cfg.unicast_address = config.unicast_endpoint.ip
    cpp_cfg.unicast_port = config.unicast_endpoint.port
    try:
        cpp_cfg.ttl = datetime.timedelta(seconds=config.ttl)
    except TypeError:
        pass
    try:
        cpp_cfg.repetition_max = datetime.timedelta(milliseconds=config.repetitions_base_delay_ms)
    except TypeError:
        pass
    return cpp_cfg


# ---------------------------------------------------------------------------
# ServiceInstance conversions
# ---------------------------------------------------------------------------


def to_cpp_service_instance(svc: ServiceInstance) -> Any:
    ext = require_native()
    cpp_svc = ext.sd.ServiceInstance(
        svc.service_id,
        svc.instance_id,
        svc.major_version,
        svc.minor_version,
    )
    return cpp_svc


def from_cpp_service_instance(cpp_svc: Any) -> ServiceInstance:
    from opensomeip.sd import ServiceInstance as PySvc

    return PySvc(
        service_id=cpp_svc.service_id,
        instance_id=cpp_svc.instance_id,
        major_version=cpp_svc.major_version,
        minor_version=cpp_svc.minor_version,
    )
