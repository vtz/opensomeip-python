#include <pybind11/pybind11.h>
#include <stdexcept>

namespace py = pybind11;

static py::exception<std::runtime_error> someip_error;
static py::exception<std::runtime_error> transport_error;
static py::exception<std::runtime_error> connection_error;
static py::exception<std::runtime_error> connection_lost_error;
static py::exception<std::runtime_error> serialization_error;
static py::exception<std::runtime_error> timeout_error;
static py::exception<std::runtime_error> sd_error;
static py::exception<std::runtime_error> rpc_error;
static py::exception<std::runtime_error> e2e_error;
static py::exception<std::runtime_error> config_error;

void init_exceptions(py::module_& m) {
    someip_error = py::register_exception<std::runtime_error>(m, "SomeIpError");
    transport_error = py::register_exception<std::runtime_error>(
        m, "TransportError", someip_error);
    connection_error = py::register_exception<std::runtime_error>(
        m, "ConnectionError", transport_error);
    connection_lost_error = py::register_exception<std::runtime_error>(
        m, "ConnectionLostError", transport_error);
    serialization_error = py::register_exception<std::runtime_error>(
        m, "SerializationError", someip_error);
    timeout_error = py::register_exception<std::runtime_error>(
        m, "TimeoutError", someip_error);
    sd_error = py::register_exception<std::runtime_error>(
        m, "ServiceDiscoveryError", someip_error);
    rpc_error = py::register_exception<std::runtime_error>(
        m, "RpcError", someip_error);
    e2e_error = py::register_exception<std::runtime_error>(
        m, "E2EError", someip_error);
    config_error = py::register_exception<std::runtime_error>(
        m, "ConfigurationError", someip_error);
}
